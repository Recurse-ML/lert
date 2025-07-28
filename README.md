# lert

Demo CLI of Recurse ML alert investigator

# Recurse ML X Logfire Demo

## Setup

1. Install `lert`
	1. Install dependencies:
		1. `python3.11`
		2. `uv` (if not present)
		3. `direnv`
	2. Clone: https://github.com/Recurse-ML/lert
	   TMP: `git checkout rml-262-logfire-poc`
	3. Run `uv run lert` inside of the newly created repo.
	   On the first run `lert` will automatically create a user for you with an authentication token, displayed in the top-right corner. Note this token down. You'll need to specify, the token when configuring the channel for the logfire alert.
2. Clone the example repo: https://github.com/recurse-ML/logfire-example
3. Checkout the branch with intentionally introduced bugs
	```bash
	git checkout demo/buggy-branch
	```
4. Create a logfire project
5. Create an alert that's triggered on 500 status codes:
   ```sql
	SELECT * FROM RECORDS WHERE http_response_status_code>=500;
	```
	1. Create a channel for listening to the alert:
		1. Create a new channel to send alerts to a specific destination
		2. Channel Name: Recurse ML
		3. Type: Webhook
		4. Format: Slack Legacy (for Discord, etc.)
		5. Webhook URL: `<base-url>/your-lert-token`
		6. Select alert variant: Alert query has matches
6. Set the `LOGFIRE_TOKEN` in the `.env.example` file in `logfire-example` root.
7. `cp .env.example .env`
8. Ensure docker is running on your system.
9. Run the webapp: `sh ./start-app.sh`
   `docker compose watch`
10. Check that frontend is served on `http://localhost:5173` and backend (docs) on `http://localhost:8000/docs`.

## Triggering errors

1. Any of the actions bellow should trigger an alert.
2. You can verify that the action has been executed successfully by navigating the live logs page on seeing whether there's an ERROR https://logfire-us.pydantic.dev/<user-name>/<project-name>
	(alerts take)

**Existing endpoints:**

GET request to 
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/password-recovery/foobar%40tar.com' \
  -H 'accept: application/json' \
  -d ''
```

**Creating new errors:** you might want to introduce your own bugs into the code and see Recurse ML analysis results:
1. Modify the web app's code.
2. Commit and push the changes
3. Run `sh ./start-app.sh`
4. Trigger the alert.

## Bring Your Own Repo

⚠️If using your own repo, ensure that [Recurse ML GH App](https://github.com/marketplace/recurse-ml/) is installed on it⚠️

## Limitations

1. Assumes alert is triggered by the following query:
   ```sql
	SELECT * FROM RECORDS WHERE http_response_status_code>=500;
	```


# CLI Specs

Interface:
1. Textual table of all triggered alerts in the project
2. Select an alert for investigation
3. Detailed investigation results for the alert

Query data:
(On initialization and every 5 seconds)

1. GET /logfire/reports/
2. Update the table of investigations

## Report View

1. When a user presses enter, on an alert that has a "success" status and a InvestigationResponse.report field that's not None, they should enter a report view.
2. The report view must render the InvestigationResponse.report field as markdown.
3. Pressing (h) for home must take them back to home screen


## Authentication:

1. Generate secret key
2. Create a logfire project
3. Create an alert in the project
4. Add a Recurse ML webhook to the alert. In the webhook, specify your token.

Generating and viewing the token:
Deployment: upon initialization, generate the token in the local storage
            user has a shortcut to view the token in the CLI UI

# Recurse ML Logfire Endpoint

This API provides endpoints for integrating with Logfire, a monitoring and alerting platform. The API enables webhook handling, user management, and incident investigation reporting.

## Authentication

### Logfire API Request Authentication

For API endpoints (`/logfire/reports/` and `/logfire/report/{alert_id}/`), authentication is performed using custom headers:

- **X-Logfire-User-ID**: Your Logfire user identifier
- **X-Logfire-Secret**: Your Logfire webhook secret

Both headers are required for authentication. The system verifies that the provided user ID and secret match a valid Logfire user in the system.

### Logfire Webhook Authentication

For webhook endpoints (`/logfire/{logfire_secret}/`), authentication is performed by including the webhook secret directly in the URL path. The secret is validated against the registered Logfire user credentials.

## Endpoints

### User Management

**POST /logfire/user/**
- Creates a new Logfire user with a read token
- **Authentication**: None required
- **Request Body**: 
  ```json
  {
    "read_token": "your_logfire_read_token"
  }
  ```
- **Response**: User ID, read token, and secret for future authentication

### Reports and Investigations

**GET /logfire/reports/**
- Retrieves all investigation reports for the authenticated user
- **Authentication Required**: X-Logfire-User-ID and X-Logfire-Secret headers
- **Response**: Array of investigation responses with ID, alert ID, status, and report content

**GET /logfire/report/{alert_id}/**
- Retrieves a specific investigation report by alert ID
- **Authentication Required**: X-Logfire-User-ID and X-Logfire-Secret headers
- **Parameters**: `alert_id` (string) - The alert identifier
- **Response**: Investigation response with details including:
  - `investigation_id`: Internal investigation identifier
  - `alert_id`: The original alert identifier
  - `status`: Investigation status (PENDING, ERROR, or completed)
  - `report`: Investigation report content (null if pending or error)

### Webhook Handling

**POST /logfire/{logfire_secret}/**
- Handles incoming Logfire webhooks for incident investigations
- **Authentication**: Webhook secret embedded in URL path
- **Parameters**: `logfire_secret` (string) - Webhook secret in URL path
- **Request Body**: Logfire webhook payload containing alert information
- **Functionality**: Creates incident investigations from Logfire alerts
- **Response**: 
  - **201 Created**: Investigation created successfully
  - **409 Conflict**: Investigation already exists for this alert
  - **400 Bad Request**: Invalid webhook data or missing alert_id

## Error Responses

- **401 Unauthorized**: Missing or invalid authentication credentials
- **404 Not Found**: Investigation not found for the given alert ID
- **500 Internal Server Error**: Server-side processing error

