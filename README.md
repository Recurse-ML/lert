# lert Demo Setup Guide

Welcome to the Recurse ML X Logfire demo!
This demo will show you how Recurse ML, can find the root cause for alerts in your application.

This demo has 3 components:
1. `lert` (this repo): the interface for inspecting Recurse ML alert results.
2. [`logfire-example`](https://github.com/recurse-ml/logfire-example): a sample repo, that's instrumented with Logfire.
    We'll use it to simulate production alerts in a FastAPI web app. 
3. Your Logfire project: it will listen for alerts from `logfire-example` and send them as webhooks to Recurse ML for analysis.
    The analysis results, in turn, will be displayed here, in `lert`.

## What You'll Need

Before we start, make sure you have these dependencies installed:
- `python3.11`
- `uv` (if not already installed)
- Docker (running on your system)

## Part 1: Setting Up the Alert Investigator

Let's get the lert CLI tool up and running:

**1. Configure your Logfire connection**

First, grab a read token from your Logfire project:
- Navigate to `https://logfire-us.pydantic.dev/<user-name>/<project-name>/settings/read-tokens`
- Create a new read token and copy it

**2. Start lert**
```bash
uv run lert
```

On your first run, lert will automatically create a user account for you. When prompted, enter the read token you created in the previous step.

**3. Note your webhook URL**

Once lert is running, you'll see a webhook URL displayed in the top-right corner. Write this down - you'll need it for the next section!

## Part 2: Setting Up Your Demo Application

**1. Get the example application**

_I've already created example bugs in `demo/buggy-branch` for you to investigate._

```bash
git clone https://github.com/recurse-ML/logfire-example
cd logfire-example
git fetch
git checkout demo/buggy-branch
```

**2. Configure Logfire for the app**

Create a write token for your application:
- Go to `https://logfire-us.pydantic.dev/<user-name>/<project-name>/settings/write-tokens`
- Create a new write token

Set up your environment:
```bash
# Edit .env.example and set your LOGFIRE_TOKEN
cp .env.example .env
```

**3. Start the application**

```bash
./start-app.sh
```

Your app should now be running:
- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`

## Part 3: Creating Your Alert System

**1. Create a Logfire project**

If you haven't already, set up a new project in Logfire.

**2. Set up the alert query**

⚠️ **Important:** Use these exact settings for the demo to work properly!

- **Query:**
  ```sql
  SELECT * FROM RECORDS WHERE http_response_status_code>=500;
  ```
- **Execute the query:** "every minute"
- **Include rows from:** "the last minute"  
- **Notify me when:** "the query has results"

**3. Connect the alert to lert**

Create a new channel to send alerts to the Recurse ML investigator:

- **Channel Name:** Recurse ML
- **Type:** Webhook
- **Format:** Raw Data
- **Webhook URL:** `https://squash-322339097191.europe-west3.run.app/logfire/<your-lert-token>/`
- **Select alert variant:** Alert query has matches

Test your setup by clicking "Send a test alert" - you should get a 200 status code.

## Testing Your Setup

**Trigger an error**

Try this API call to generate a 500 error:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/password-recovery/nonexistent%40user.com' \
  -H 'accept: application/json' \
  -d ''
```

**Verify the alert worked**

You can check that your error was logged by visiting your Logfire live logs page:
`https://logfire-us.pydantic.dev/<user-name>/<project-name>`

Look for ERROR entries.

Now, an alert should be triggered within a minute of the original log in the alerts section.

Immediately after an alert is triggered, you should see the alert entry in `lert`.
It will initially have status "pending".
Within 5 minutes, the alert should be processed and its status will change to "success" (or in the unfortunate case to "error").

If you get an error or analysis takes longer than that, please do reach out (email's at the bottom of this page).


## Experimenting Further

**Create your own bugs**

Want to see how the system handles different types of errors?

1. Modify the webapp's code to introduce new bugs
2. Commit and push your changes  
3. Run `sh ./start-app.sh` to restart with your changes
4. Trigger the alert and see what the AI investigator finds!

## Using Your Own Repository

If you want to try this with your own codebase instead of the demo app, make sure the [Recurse ML GitHub App](https://github.com/marketplace/recurse-ml/) is installed on your repository first.

## Current Limitations

This demo assumes your alert uses the specific query:
```sql
SELECT * FROM RECORDS WHERE http_response_status_code>=500;
```

---

That's it!
You just saw how Recurse ML can help you debug your Logfire alerts.

Did you run into any issues? Have feedback on the prototype? Either way, I'd love to hear all about it: <first letter of the alphabet> (at) recurse.ml

