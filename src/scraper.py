"""
Time Doctor Web Scraper
Handles authentication and web scraping using Playwright
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

# Load environment variables from the project directory
# Get the directory where this script is located
script_dir = Path(__file__).parent
project_dir = script_dir.parent
env_path = project_dir / ".env"

# Load .env file from project directory
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TimeDocorScraper:
    """
    Web scraper for Time Doctor time tracking platform.
    Uses Playwright for browser automation and authentication.
    """

    def __init__(self):
        """Initialize the Time Doctor scraper with configuration from environment."""
        self.email = os.getenv("TD_EMAIL")
        self.password = os.getenv("TD_PASSWORD")
        self.base_url = os.getenv("TD_BASE_URL", "https://2.timedoctor.com")
        self.headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))

        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.playwright = None

        # Validate credentials
        if not self.email or not self.password:
            raise ValueError("TD_EMAIL and TD_PASSWORD must be set in .env file")

        logger.info(f"TimeDocorScraper initialized with email: {self.email}")

    async def start_browser(self):
        """Start the Playwright browser instance."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    async def close_browser(self):
        """Close the browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def login(self) -> bool:
        """
        Login to Time Doctor web interface.

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("Attempting to login to Time Doctor")

            # Navigate to login page
            login_url = f"{self.base_url}/login"
            await self.page.goto(login_url, wait_until="load", timeout=60000)
            logger.debug(f"Navigated to {login_url}")

            # Wait for login form to load
            await self.page.wait_for_timeout(2000)
            await self.page.wait_for_selector('input[type="email"]', timeout=10000)

            # Fill in email
            await self.page.fill('input[type="email"]', self.email)
            logger.debug("Email filled")

            # Fill in password
            await self.page.fill('input[type="password"]', self.password)
            logger.debug("Password filled")

            # Click login button and wait for navigation
            logger.debug("Clicking login button...")

            # Wait for navigation to complete after clicking login
            try:
                async with self.page.expect_navigation(wait_until="load", timeout=30000):
                    await self.page.click('button[type="submit"]')
                logger.debug("Navigation after login completed")
            except Exception as nav_error:
                logger.warning(f"Navigation wait failed: {nav_error}, checking URL anyway...")

            # Additional wait for any post-login processing
            await self.page.wait_for_timeout(3000)

            current_url = self.page.url
            logger.debug(f"Current URL after login attempt: {current_url}")

            # Check if login was successful (should redirect away from login page)
            if "/login" not in current_url:
                logger.info(f"Login successful - redirected to {current_url}")
                return True
            else:
                # Check for error messages on the page
                try:
                    error_elem = await self.page.query_selector('.error, .alert, [role="alert"]')
                    if error_elem:
                        error_text = await error_elem.inner_text()
                        logger.error(f"Login failed with error: {error_text}")
                except Exception:
                    pass

                logger.error("Login failed - still on login page")
                logger.error(f"Credentials used - Email: {self.email}")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def navigate_to_date(self, target_date: str):
        """
        Navigate to a specific date in the reports page using arrow buttons.
        Assumes we're already on the projects-report page.

        Args:
            target_date: Date in YYYY-MM-DD format
        """
        try:
            from datetime import datetime

            target = datetime.strptime(target_date, "%Y-%m-%d")
            logger.info(f"Navigating to date: {target_date}")

            # Get current date displayed on page
            # Look for button with date text like "Nov 4, 2025"
            date_button = await self.page.query_selector('button:has-text(", 20")')
            if not date_button:
                logger.warning("Could not find date display button")
                return

            current_date_text = await date_button.inner_text()
            logger.debug(f"Current date on page: {current_date_text}")

            # Parse the date (format: "Nov 4, 2025")
            try:
                current_date = datetime.strptime(current_date_text.strip(), "%b %d, %Y")
            except ValueError:
                logger.warning(f"Could not parse date from: {current_date_text}")
                return

            # Calculate days difference
            days_diff = (current_date - target).days

            if days_diff == 0:
                logger.info("Already on target date")
                return

            # Navigate using arrow buttons
            if days_diff > 0:
                # Need to go back in time (click left arrow)
                logger.info(f"Going back {days_diff} days")
                for i in range(days_diff):
                    # Find left arrow button
                    left_arrow = await self.page.query_selector(
                        'button.navigation-button:has(mat-icon:has-text("keyboard_arrow_left"))'
                    )

                    if not left_arrow:
                        logger.warning(f"Could not find left arrow button on iteration {i+1}")
                        break

                    # Check if button is disabled
                    is_disabled = await left_arrow.is_disabled()
                    if is_disabled:
                        logger.warning("Left arrow is disabled, cannot go further back")
                        break

                    # Click the arrow
                    await left_arrow.click()
                    logger.debug(f"Clicked left arrow ({i+1}/{days_diff})")

                    # Wait for page to update
                    await self.page.wait_for_timeout(1500)
            else:
                # Need to go forward in time (click right arrow)
                days_forward = abs(days_diff)
                logger.info(f"Going forward {days_forward} days")
                for i in range(days_forward):
                    # Find right arrow button
                    right_arrow = await self.page.query_selector(
                        'button.navigation-button:has(mat-icon:has-text("keyboard_arrow_right"))'
                    )

                    if not right_arrow:
                        logger.warning(f"Could not find right arrow button on iteration {i+1}")
                        break

                    # Check if button is disabled
                    is_disabled = await right_arrow.is_disabled()
                    if is_disabled:
                        logger.warning(
                            "Right arrow is disabled, cannot go further forward (probably at today)"
                        )
                        break

                    # Click the arrow
                    await right_arrow.click()
                    logger.debug(f"Clicked right arrow ({i+1}/{days_forward})")

                    # Wait for page to update
                    await self.page.wait_for_timeout(1500)

            # Verify we reached the target date
            date_button = await self.page.query_selector('button:has-text(", 20")')
            if date_button:
                final_date_text = await date_button.inner_text()
                logger.info(f"Navigation complete. Current date: {final_date_text}")

        except Exception as e:
            logger.error(f"Error navigating to date {target_date}: {e}", exc_info=True)

    async def get_daily_report_html(self, date: str, navigate_to_report: bool = True) -> str:
        """
        Get the HTML content of daily report page.

        Args:
            date: Date in YYYY-MM-DD format
            navigate_to_report: If True, navigate to report page first.
                              Set to False if already on the page.

        Returns:
            str: HTML content of the report page
        """
        try:
            logger.info(f"Fetching daily report for {date}")

            # Navigate to Projects & Tasks report if needed
            if navigate_to_report:
                report_url = f"{self.base_url}/projects-report"
                await self.page.goto(report_url, wait_until="load", timeout=60000)
                logger.debug(f"Navigated to {report_url}")
                await self.page.wait_for_timeout(3000)
            else:
                logger.debug("Already on report page, skipping navigation")

            # Navigate to specific date
            await self.navigate_to_date(date)

            # Click "Expand All" button to show all tasks
            try:
                expand_button = await self.page.query_selector('button:has-text("Expand All")')
                if expand_button:
                    await expand_button.click()
                    logger.debug("Clicked Expand All button")
                    await self.page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"Could not click Expand All: {e}")

            # Wait for content to fully load
            await self.page.wait_for_timeout(2000)

            # Get page HTML
            html_content = await self.page.content()
            logger.info(f"Successfully retrieved report HTML ({len(html_content)} bytes)")

            return html_content

        except Exception as e:
            logger.error(f"Error fetching daily report: {e}")
            raise

    async def get_date_range_reports(self, start_date: str, end_date: str) -> list[dict]:
        """
        Get reports for a date range in a single browser session.
        Stays logged in and navigates between dates efficiently.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List[Dict]: List of dicts with 'date' and 'html' for each day
        """
        try:
            logger.info(f"Fetching date range reports from {start_date} to {end_date}")

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            reports = []
            current_date = start

            # Navigate to report page once
            first_iteration = True

            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")

                # Only navigate to report page on first iteration
                # After that, stay on the page and just change dates
                html = await self.get_daily_report_html(
                    date_str, navigate_to_report=first_iteration
                )

                reports.append({"date": date_str, "html": html})

                first_iteration = False
                current_date += timedelta(days=1)

            logger.info(f"Successfully retrieved {len(reports)} daily reports in one session")
            return reports

        except Exception as e:
            logger.error(f"Error fetching date range reports: {e}")
            raise

    async def get_weekly_report_html(self, start_date: str, end_date: str) -> list[str]:
        """
        Get HTML content for a date range (weekly report).
        Legacy method - use get_date_range_reports instead.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List[str]: List of HTML contents for each day
        """
        try:
            reports = await self.get_date_range_reports(start_date, end_date)
            return [r["html"] for r in reports]

        except Exception as e:
            logger.error(f"Error fetching weekly report: {e}")
            raise

    async def get_report_data(self, date: str) -> dict:
        """
        Get structured report data for a specific date.
        This is a convenience method that handles browser lifecycle.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Dict: Report data with HTML content
        """
        try:
            await self.start_browser()

            # Login
            login_success = await self.login()
            if not login_success:
                raise Exception("Login failed")

            # Get report HTML
            html_content = await self.get_daily_report_html(date)

            return {"date": date, "html": html_content, "success": True}

        finally:
            await self.close_browser()

    async def get_date_range_data_single_session(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """
        Get structured report data for a date range in a SINGLE browser session.
        Login once, navigate through all dates, then close.
        This is the most efficient way to get multiple days of data.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List[Dict]: List of report data with 'date', 'html', 'success' for each day
        """
        try:
            logger.info(f"Starting single session for date range {start_date} to {end_date}")

            # Start browser once
            await self.start_browser()

            # Login once
            login_success = await self.login()
            if not login_success:
                raise Exception("Login failed")

            # Get all reports in one session
            reports = await self.get_date_range_reports(start_date, end_date)

            # Add success flag
            for report in reports:
                report["success"] = True

            logger.info(f"Completed single session: {len(reports)} days retrieved")
            return reports

        except Exception as e:
            logger.error(f"Error in single session data retrieval: {e}")
            raise

        finally:
            # Always close browser
            await self.close_browser()

    async def get_weekly_data(self, start_date: str, end_date: str) -> list[dict]:
        """
        Get structured report data for a date range.
        This is a convenience method that handles browser lifecycle.
        Uses single session for efficiency.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List[Dict]: List of report data for each day
        """
        try:
            # Use the new single-session method
            return await self.get_date_range_data_single_session(start_date, end_date)

        except Exception as e:
            logger.error(f"Error getting weekly data: {e}")
            raise


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        scraper = TimeDocorScraper()

        # Get today's report
        today = datetime.now().strftime("%Y-%m-%d")
        data = await scraper.get_report_data(today)

        print(f"Report fetched successfully: {data['success']}")
        print(f"HTML length: {len(data['html'])} bytes")

    asyncio.run(main())
