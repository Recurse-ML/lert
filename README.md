# lert

Demo CLI of Recurse ML alert investigator

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

