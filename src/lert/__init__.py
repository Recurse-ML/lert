"""
Interface:
1. List all triggered alerts in the project
2. Select an alert for investigation
3. Detailed investigation results for the alert

Query data:
(On initialization and every 5 seconds)

1. GET /logfire/reports/
2. Update the table of investigations


Authentication:
1. Generate secret key
2. Create a logfire project
3. Create an alert in the project
4. Add a Recurse ML webhook to the alert. In the webhook, specify your token.

Generating and viewing the token:
Deployment: upon initialization, generate the token in the local storage
            user has a shortcut to view the token in the CLI UI
"""

import json
import sys
from base64 import b64encode
from pathlib import Path
from typing import Dict, List, Optional

import click
import httpx
from pydantic import BaseModel
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Markdown, Static

from lert.package_config import HOST_URL


class InvestigationReport(BaseModel):
    id: int
    alert_id: str
    status: str
    report: Optional[str] = None


class AlertClient:
    def __init__(self, base_url: str = HOST_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.user_id: Optional[str] = None
        self.secret: Optional[str] = None
        self.config_dir = Path.home() / ".lert"
        self.config_file = self.config_dir / "credentials.json"

    def prompt_for_read_token(self) -> str:
        """Prompt user to enter their logfire read token"""
        print("Please enter your logfire read token:")

        while True:
            if (token := input("Token: ").strip()):
                print("✓ Token received!")
                return token
            else:
                print("⚠ Token cannot be empty.")
                retry = input("Try again? (y/n): ").lower().strip()
                if retry != "y":
                    raise ValueError("Logfire read token is required to proceed.")

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Load credentials from local storage"""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                # Only load if both id and secret exist and are not empty
                if data.get("id") and data.get("secret"):
                    self.user_id = str(data["id"])
                    self.secret = data["secret"]
                    return data
                return None
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None

    def save_credentials(self, data: Dict[str, str]) -> None:
        """Save credentials to local storage"""
        self.config_dir.mkdir(exist_ok=True)
        data["webhook_url"] = f"{HOST_URL}/logfire/{data['secret']}"
        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)

    async def authenticate(self, read_token: str) -> Dict[str, str]:
        """Create user and get credentials"""
        response = await self.client.post(
            "/logfire/user/", json={"logfire_read_token": read_token}
        )
        response.raise_for_status()
        data = response.json()

        self.user_id = str(data["id"])
        self.secret = data["secret"]
        self.save_credentials(data)
        return data

    async def get_reports(self) -> List[InvestigationReport]:
        """Get all investigation reports"""
        if not self.user_id or not self.secret:
            return []

        encoded_auth = b64encode(
            f"{self.user_id}:{self.secret}".encode("UTF-8")
        ).decode()
        headers = {"Authorization": f"Basic {encoded_auth}"}

        response = await self.client.get("/logfire/reports/", headers=headers)
        response.raise_for_status()
        data = response.json()
        return [InvestigationReport(**item) for item in data]

    async def get_report(self, alert_id: str) -> Optional[InvestigationReport]:
        """Get specific investigation report"""
        if not self.user_id or not self.secret:
            return None

        encoded_auth = b64encode(
            f"{self.user_id}:{self.secret}".encode("UTF-8")
        ).decode()
        headers = {"Authorization": f"Basic {encoded_auth}"}

        response = await self.client.get(
            f"/logfire/report/{alert_id}/", headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return InvestigationReport(**data)


class DetailScreen(Screen):
    """Screen for displaying detailed investigation results"""

    def __init__(self, report: InvestigationReport):
        super().__init__()
        self.report = report

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label(
                f"Investigation Details - Alert ID: {self.report.alert_id}",
                id="detail-title",
            ),
            Label(f"Status: {self.report.status}", id="detail-status"),
            Static(self.report.report or "No report available", id="detail-report"),
            Button("Back", id="back-button", variant="primary"),
            id="detail-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()


class ReportScreen(Screen):
    """Screen for displaying investigation reports with markdown rendering"""

    BINDINGS = [
        Binding("h", "home", "Home"),
    ]

    def __init__(self, report: InvestigationReport):
        super().__init__()
        self.report = report

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label(
                f"Investigation Report - Alert ID: {self.report.alert_id}",
                id="report-title",
            ),
            Label(f"Status: {self.report.status}", id="report-status"),
            Markdown(self.report.report or "No report available", id="report-content"),
            id="report-container",
        )
        yield Footer()

    def action_home(self) -> None:
        """Return to home screen"""
        self.app.pop_screen()


class AlertApp(App):
    """Main application for alert investigation"""

    CSS = """
    #alert-table {
        height: 1fr;
        margin: 1;
    }

    #header-container {
        height: 3;
        margin: 1;
    }

    #app-title {
        margin-right: 2;
    }

    #user-info {
        text-align: right;
        color: $text-muted;
        dock: right;
    }

    #detail-container {
        margin: 1;
        padding: 1;
    }

    #detail-title {
        color: $primary;
        margin-bottom: 1;
    }

    #detail-status {
        margin-bottom: 1;
    }

    #detail-report {
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }

    #report-container {
        margin: 1;
        padding: 1;
    }

    #report-title {
        color: $primary;
        margin-bottom: 1;
    }

    #report-status {
        margin-bottom: 1;
    }

    #report-content {
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: solid $accent;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.client = AlertClient()
        self.token_visible = False
        self.user_credentials = None
        self.reports_cache: Dict[str, InvestigationReport] = {}

    async def on_mount(self) -> None:
        """Initialize the application"""
        # Start background authentication - non-blocking
        self.call_later(self.setup_credentials)
        # Set up periodic refresh
        self.set_interval(5.0, self.refresh_data)
        # UI is ready immediately, data will load in background

    async def setup_credentials(self) -> None:
        """Setup user credentials or load from storage"""
        try:
            # First try to load existing credentials
            self.user_credentials = self.client.load_credentials()

            if self.user_credentials:
                self.notify("Loaded existing credentials", severity="information")
            else:
                self.notify(
                    "No existing credentials found. Please check console for setup.",
                    severity="warning",
                )
                return

            # Update user info in header after authentication
            self.update_user_info()

            # Start first data fetch after authentication
            await self.refresh_data()
        except Exception as e:
            self.notify(f"Authentication failed: {e}", severity="error", markup=False)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Label("Alert Investigation Dashboard", id="app-title"),
                Label("", id="user-info"),
                id="header-container",
            ),
            DataTable(id="alert-table"),
            id="main-container",
        )
        yield Footer()

    def update_user_info(self) -> None:
        """Update the user info display in the header"""
        user_info = self.query_one("#user-info", Label)
        if self.user_credentials:
            user_id = self.user_credentials.get("id", "N/A")
            secret = self.user_credentials.get("secret", "N/A")
            user_info.update(
                f"User ID: {user_id} | Webhook URL: {HOST_URL}/logfire/{secret}\n(Can't copy? URL is located in {str(self.client.config_file)})"
            )
        else:
            user_info.update("Connecting...")

    async def on_ready(self) -> None:
        """Setup the data table"""
        table = self.query_one("#alert-table", DataTable)
        table.add_columns("Alert ID", "Status", "ID")
        table.cursor_type = "row"

        # Update user info display
        self.update_user_info()

    async def refresh_data(self) -> None:
        """Refresh the alert data"""
        # Skip if not authenticated yet
        if not self.user_credentials:
            return

        try:
            reports = await self.client.get_reports()

            table = self.query_one("#alert-table", DataTable)
            # Preserve cursor position before clearing
            cursor_row = table.cursor_row
            table.clear()

            if len(table.columns) == 0:
                # Alert Table is not initialized yet
                return

            for report in reports:
                table.add_row(report.alert_id, report.status, report.id)
                self.reports_cache[report.alert_id] = report

            # Restore cursor position if it's still valid
            if cursor_row < table.row_count:
                table.move_cursor(row=cursor_row)
        except Exception as e:
            # Don't crash on data fetch errors, just log
            # Disable markup to prevent parsing issues with error messages
            self.notify(
                f"Failed to refresh data: {e}", severity="warning", markup=False
            )

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table"""
        table = event.data_table
        row = table.get_row_at(event.cursor_row)
        alert_id = str(row[0])
        status = str(row[1])

        report = self.reports_cache.get(alert_id)
        if report:
            # Navigate to report view if status is "success" and report exists
            if status == "success" and report.report is not None:
                self.push_screen(ReportScreen(report))
            else:
                self.push_screen(DetailScreen(report))
        else:
            self.notify("Failed to load investigation details", severity="error")

    async def action_refresh(self) -> None:
        """Manually refresh the data"""
        await self.refresh_data()
        self.notify("Data refreshed")

    async def action_quit(self) -> None:
        """Quit the application"""
        self.exit()


async def setup_user_if_needed():
    """Setup user credentials if they don't exist"""
    client = AlertClient()

    # Check if credentials already exist
    existing_creds = client.load_credentials()
    if existing_creds:
        print("✓ Existing credentials found. Starting application...")
        return

    print("🔧 Setting up user credentials for first time...")

    # Prompt for read token and create user
    try:
        read_token = client.prompt_for_read_token()
        credentials = await client.authenticate(read_token)
        print(f"✓ User created successfully! User ID: {credentials['id']}")
        print("Starting application...")
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        sys.exit(1)


@click.command()
def main():
    """Launch the alert investigation CLI"""
    import asyncio

    # Setup user credentials if needed (console mode)
    asyncio.run(setup_user_if_needed())

    # Start the textual app
    app = AlertApp()
    app.run()


if __name__ == "__main__":
    main()
