"""
Time Doctor Web Scraper
Handles authentication and web scraping using Playwright
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Handle both package import and direct execution
try:
    from .cache import ReportCache
    from .constants import (
        BROWSER_DEFAULT_TIMEOUT_MS,
        BROWSER_USER_AGENT,
        BROWSER_VIEWPORT_HEIGHT,
        BROWSER_VIEWPORT_WIDTH,
        CONTENT_LOAD_WAIT_MS,
        DATE_NAVIGATION_WAIT_MS,
        EMAIL_SELECTOR_TIMEOUT_MS,
        EXPAND_ALL_WAIT_MS,
        LOGIN_FORM_LOAD_WAIT_MS,
        LOGIN_NAVIGATION_TIMEOUT_MS,
        MAX_PARALLEL_SESSIONS,
        MAX_RETRY_ATTEMPTS,
        PAGE_LOAD_TIMEOUT_MS,
        PARALLEL_THRESHOLD,
        POST_LOGIN_WAIT_MS,
        REPORT_PAGE_LOAD_WAIT_MS,
        RETRY_MAX_WAIT_SECONDS,
        RETRY_MIN_WAIT_SECONDS,
        RETRY_MULTIPLIER,
    )
except ImportError:
    from cache import ReportCache
    from constants import (
        BROWSER_DEFAULT_TIMEOUT_MS,
        BROWSER_USER_AGENT,
        BROWSER_VIEWPORT_HEIGHT,
        BROWSER_VIEWPORT_WIDTH,
        CONTENT_LOAD_WAIT_MS,
        DATE_NAVIGATION_WAIT_MS,
        EMAIL_SELECTOR_TIMEOUT_MS,
        EXPAND_ALL_WAIT_MS,
        LOGIN_FORM_LOAD_WAIT_MS,
        LOGIN_NAVIGATION_TIMEOUT_MS,
        MAX_PARALLEL_SESSIONS,
        MAX_RETRY_ATTEMPTS,
        PAGE_LOAD_TIMEOUT_MS,
        PARALLEL_THRESHOLD,
        POST_LOGIN_WAIT_MS,
        REPORT_PAGE_LOAD_WAIT_MS,
        RETRY_MAX_WAIT_SECONDS,
        RETRY_MIN_WAIT_SECONDS,
        RETRY_MULTIPLIER,
    )

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
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", str(BROWSER_DEFAULT_TIMEOUT_MS)))

        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.playwright = None

        # Initialize cache
        self.cache = ReportCache()
        self.use_cache = os.getenv("USE_CACHE", "true").lower() == "true"

        # Validate credentials
        if not self.email or not self.password:
            raise ValueError("TD_EMAIL and TD_PASSWORD must be set in .env file")

        logger.info(f"TimeDocorScraper initialized with email: {self.email}")
        logger.info(f"Cache {'enabled' if self.use_cache else 'disabled'}")

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS
        ),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def start_browser(self):
        """Start the Playwright browser instance with retry logic."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            self.context = await self.browser.new_context(
                viewport={"width": BROWSER_VIEWPORT_WIDTH, "height": BROWSER_VIEWPORT_HEIGHT},
                user_agent=BROWSER_USER_AGENT,
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

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS
        ),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def login(self) -> bool:
        """
        Login to Time Doctor web interface with retry logic.

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("Attempting to login to Time Doctor")

            # Navigate to login page
            login_url = f"{self.base_url}/login"
            await self.page.goto(login_url, wait_until="load", timeout=PAGE_LOAD_TIMEOUT_MS)
            logger.debug(f"Navigated to {login_url}")

            # Wait for login form to load - use domcontentloaded instead of networkidle
            # because Time Doctor has continuous background network activity
            await self.page.wait_for_load_state("domcontentloaded", timeout=LOGIN_FORM_LOAD_WAIT_MS)
            await self.page.wait_for_selector(
                'input[type="email"]', timeout=EMAIL_SELECTOR_TIMEOUT_MS
            )

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
                async with self.page.expect_navigation(
                    wait_until="load", timeout=LOGIN_NAVIGATION_TIMEOUT_MS
                ):
                    await self.page.click('button[type="submit"]')
                logger.debug("Navigation after login completed")
            except Exception as nav_error:
                logger.warning(f"Navigation wait failed: {nav_error}, checking URL anyway...")

            # Wait for post-login processing - use domcontentloaded for stability
            await self.page.wait_for_load_state("domcontentloaded", timeout=POST_LOGIN_WAIT_MS)

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
                        logger.warning(f"Could not find left arrow button on iteration {i + 1}")
                        break

                    # Check if button is disabled
                    is_disabled = await left_arrow.is_disabled()
                    if is_disabled:
                        logger.warning("Left arrow is disabled, cannot go further back")
                        break

                    # Click the arrow
                    await left_arrow.click()
                    logger.debug(f"Clicked left arrow ({i + 1}/{days_diff})")

                    # Wait for page to update (fixed wait works better for date navigation)
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
                        logger.warning(f"Could not find right arrow button on iteration {i + 1}")
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
                    logger.debug(f"Clicked right arrow ({i + 1}/{days_forward})")

                    # Wait for page to update (fixed wait works better for date navigation)
                    await self.page.wait_for_timeout(1500)

            # Verify we reached the target date
            date_button = await self.page.query_selector('button:has-text(", 20")')
            if date_button:
                final_date_text = await date_button.inner_text()
                logger.info(f"Navigation complete. Current date: {final_date_text}")

        except Exception as e:
            logger.error(f"Error navigating to date {target_date}: {e}", exc_info=True)

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS
        ),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def get_daily_report_html(self, date: str, navigate_to_report: bool = True) -> str:
        """
        Get the HTML content of daily report page with retry logic and caching.

        Args:
            date: Date in YYYY-MM-DD format
            navigate_to_report: If True, navigate to report page first.
                              Set to False if already on the page.

        Returns:
            str: HTML content of the report page
        """
        try:
            # Check cache first
            if self.use_cache:
                cached_html = self.cache.get(date)
                if cached_html:
                    logger.info(f"Using cached report for {date}")
                    return cached_html

            logger.info(f"Fetching daily report for {date}")

            # Navigate to Projects & Tasks report if needed
            if navigate_to_report:
                report_url = f"{self.base_url}/projects-report"
                await self.page.goto(report_url, wait_until="load", timeout=PAGE_LOAD_TIMEOUT_MS)
                logger.debug(f"Navigated to {report_url}")
                await self.page.wait_for_load_state("domcontentloaded", timeout=REPORT_PAGE_LOAD_WAIT_MS)
                # Wait for date navigation buttons to appear before trying to navigate
                await self.page.wait_for_timeout(2000)
            else:
                logger.debug("Already on report page, skipping navigation")

            # Navigate to specific date
            await self.navigate_to_date(date)

            # Wait for the Angular app to render - look for "Time Tracked" column header
            try:
                await self.page.wait_for_selector(
                    'text=Time Tracked', timeout=10000
                )
                logger.debug("Time Tracked header found - page rendered")
                # Give Angular a moment to finish rendering
                await self.page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"Time Tracked header not found: {e}")

            # Click "Expand All" button to show all tasks
            try:
                expand_button = await self.page.wait_for_selector(
                    'button:has-text("Expand All")', timeout=5000
                )
                if expand_button:
                    await expand_button.click()
                    logger.debug("Clicked Expand All button")
                    # Wait for expansion to complete
                    await self.page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"Could not click Expand All: {e}")

            # Get page HTML
            html_content = await self.page.content()
            logger.info(f"Successfully retrieved report HTML ({len(html_content)} bytes)")

            # Cache the result
            if self.use_cache:
                self.cache.set(date, html_content)

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

    async def _scrape_single_date_in_context(
        self, context: BrowserContext, date: str
    ) -> dict[str, str]:
        """
        Helper method to scrape a single date using a specific browser context.
        Each context gets its own page and login session.

        Args:
            context: Browser context to use
            date: Date in YYYY-MM-DD format

        Returns:
            Dict with 'date' and 'html' keys
        """
        page = None
        try:
            # Create a new page in this context
            page = await context.new_page()
            page.set_default_timeout(self.timeout)

            # Check cache first
            if self.use_cache:
                cached_html = self.cache.get(date)
                if cached_html:
                    logger.info(f"[{date}] Using cached report")
                    return {"date": date, "html": cached_html}

            logger.info(f"[{date}] Starting parallel scrape")

            # Login for this context
            await page.goto(f"{self.base_url}/login", timeout=PAGE_LOAD_TIMEOUT_MS)
            await page.wait_for_load_state("domcontentloaded", timeout=LOGIN_FORM_LOAD_WAIT_MS)
            await page.wait_for_selector('input[type="email"]', timeout=EMAIL_SELECTOR_TIMEOUT_MS)

            await page.fill('input[type="email"]', self.email)
            await page.fill('input[type="password"]', self.password)

            await page.click('button[type="submit"]')
            await page.wait_for_url(
                f"{self.base_url}/dashboard-individual",
                timeout=LOGIN_NAVIGATION_TIMEOUT_MS,
                wait_until="load",
            )
            await page.wait_for_load_state("domcontentloaded", timeout=POST_LOGIN_WAIT_MS)
            logger.info(f"[{date}] Login successful")

            # Navigate to report page
            report_url = f"{self.base_url}/projects-report"
            await page.goto(report_url, wait_until="load", timeout=PAGE_LOAD_TIMEOUT_MS)
            await page.wait_for_load_state("domcontentloaded", timeout=REPORT_PAGE_LOAD_WAIT_MS)
            await page.wait_for_timeout(2000)  # Wait for date buttons to render

            # Navigate to the specific date using helper method
            await self._navigate_page_to_date(page, date)

            # Wait for content to render
            try:
                await page.wait_for_selector('text=Time Tracked', timeout=10000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"[{date}] Time Tracked header not found: {e}")

            # Click Expand All
            try:
                expand_button = await page.wait_for_selector(
                    'button:has-text("Expand All")', timeout=5000
                )
                if expand_button:
                    await expand_button.click()
                    await page.wait_for_timeout(2000)
            except Exception as e:
                logger.warning(f"[{date}] Could not click Expand All: {e}")

            # Get HTML
            html_content = await page.content()
            logger.info(f"[{date}] Successfully scraped ({len(html_content)} bytes)")

            # Cache the result
            if self.use_cache:
                self.cache.set(date, html_content)

            return {"date": date, "html": html_content}

        except Exception as e:
            logger.error(f"[{date}] Error in parallel scrape: {e}")
            raise
        finally:
            if page:
                await page.close()

    async def _navigate_page_to_date(self, page: Page, target_date: str):
        """
        Navigate a specific page to a target date.
        Extracted from navigate_to_date to work with any page, not just self.page.

        Args:
            page: The page to navigate
            target_date: Date in YYYY-MM-DD format
        """
        try:
            target = datetime.strptime(target_date, "%Y-%m-%d")

            # Get current date displayed on page
            date_button = await page.query_selector('button:has-text(", 20")')
            if not date_button:
                logger.warning(f"[{target_date}] Could not find date display button")
                return

            current_date_text = await date_button.inner_text()

            try:
                current_date = datetime.strptime(current_date_text.strip(), "%b %d, %Y")
            except ValueError:
                logger.warning(f"[{target_date}] Could not parse date from: {current_date_text}")
                return

            days_diff = (current_date - target).days

            if days_diff == 0:
                logger.info(f"[{target_date}] Already on target date")
                return

            # Navigate using arrow buttons
            if days_diff > 0:
                # Go back in time
                for i in range(days_diff):
                    left_arrow = await page.query_selector(
                        'button.navigation-button:has(mat-icon:has-text("keyboard_arrow_left"))'
                    )
                    if not left_arrow:
                        break
                    if await left_arrow.is_disabled():
                        break
                    await left_arrow.click()
                    await page.wait_for_timeout(1500)
            else:
                # Go forward in time
                days_forward = abs(days_diff)
                for i in range(days_forward):
                    right_arrow = await page.query_selector(
                        'button.navigation-button:has(mat-icon:has-text("keyboard_arrow_right"))'
                    )
                    if not right_arrow:
                        break
                    if await right_arrow.is_disabled():
                        break
                    await right_arrow.click()
                    await page.wait_for_timeout(1500)

            logger.info(f"[{target_date}] Navigation complete")

        except Exception as e:
            logger.error(f"[{target_date}] Error navigating: {e}")

    async def get_date_range_reports_parallel(
        self, start_date: str, end_date: str, max_parallel: int = MAX_PARALLEL_SESSIONS
    ) -> list[dict]:
        """
        Get reports for a date range using parallel browser contexts.

        WHEN TO USE:
        - Best for recent dates (< 7 days old) - less date navigation overhead
        - Good for non-consecutive dates (e.g., Mondays only) - each date independent
        - Beneficial when cache is cold and multiple dates needed

        NOT RECOMMENDED:
        - Consecutive dates far in the past (e.g., Oct 10-14 when today is Nov 5)
          Use get_date_range_reports() instead - it navigates incrementally

        PERFORMANCE:
        - Recent dates (7 days ago): ~2x faster than sequential
        - Old dates (30+ days ago): Similar or slower due to navigation overhead
        - Each parallel session does full navigation from today to target date

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_parallel: Maximum number of parallel sessions (default: 5)

        Returns:
            List[Dict]: List of dicts with 'date' and 'html' for each day, sorted by date
        """
        try:
            logger.info(f"Fetching date range reports (PARALLEL) from {start_date} to {end_date}")

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            # Generate list of dates
            dates = []
            current_date = start
            while current_date <= end:
                dates.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            logger.info(f"Scraping {len(dates)} dates in parallel (max {max_parallel} concurrent)")

            # Create browser contexts and scrape in parallel with semaphore
            semaphore = asyncio.Semaphore(max_parallel)

            async def scrape_with_semaphore(date: str) -> dict:
                async with semaphore:
                    context = await self.browser.new_context(
                        viewport={
                            "width": BROWSER_VIEWPORT_WIDTH,
                            "height": BROWSER_VIEWPORT_HEIGHT,
                        },
                        user_agent=BROWSER_USER_AGENT,
                    )
                    try:
                        return await self._scrape_single_date_in_context(context, date)
                    finally:
                        await context.close()

            # Run all scraping tasks in parallel
            tasks = [scrape_with_semaphore(date) for date in dates]
            reports = await asyncio.gather(*tasks)

            # Sort by date to maintain order
            reports.sort(key=lambda x: x["date"])

            logger.info(
                f"Successfully retrieved {len(reports)} daily reports in parallel session"
            )
            return reports

        except Exception as e:
            logger.error(f"Error fetching date range reports in parallel: {e}")
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
