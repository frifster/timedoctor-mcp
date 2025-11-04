"""
Test script for date navigation functionality.
Tests navigating to different dates using arrow buttons.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime, timedelta

from scraper import TimeDocorScraper


async def test_date_navigation():
    """Test navigating to different dates."""
    scraper = TimeDocorScraper()

    try:
        # Start browser (set HEADLESS=false in .env to see browser)
        await scraper.start_browser()
        print("✓ Browser started")

        # Login
        success = await scraper.login()
        if not success:
            print("✗ Login failed")
            return
        print("✓ Login successful")

        # Navigate to projects report
        report_url = f"{scraper.base_url}/projects-report"
        await scraper.page.goto(report_url, wait_until="load", timeout=60000)
        await scraper.page.wait_for_timeout(3000)
        print("✓ Navigated to projects report")

        # Get current date on page
        date_button = await scraper.page.query_selector('button:has-text(", 20")')
        if date_button:
            current_date_text = await date_button.inner_text()
            print(f"  Current date on page: {current_date_text}")

        # Test 1: Navigate to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\nTest 1: Navigating to yesterday ({yesterday})...")
        await scraper.navigate_to_date(yesterday)

        # Verify
        date_button = await scraper.page.query_selector('button:has-text(", 20")')
        if date_button:
            final_date = await date_button.inner_text()
            print(f"  Result: {final_date}")

        # Wait a bit
        await scraper.page.wait_for_timeout(2000)

        # Test 2: Navigate to 3 days ago
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        print(f"\nTest 2: Navigating to 3 days ago ({three_days_ago})...")
        await scraper.navigate_to_date(three_days_ago)

        # Verify
        date_button = await scraper.page.query_selector('button:has-text(", 20")')
        if date_button:
            final_date = await date_button.inner_text()
            print(f"  Result: {final_date}")

        # Wait a bit
        await scraper.page.wait_for_timeout(2000)

        # Test 3: Navigate to 7 days ago
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        print(f"\nTest 3: Navigating to 7 days ago ({week_ago})...")
        await scraper.navigate_to_date(week_ago)

        # Verify
        date_button = await scraper.page.query_selector('button:has-text(", 20")')
        if date_button:
            final_date = await date_button.inner_text()
            print(f"  Result: {final_date}")

        # Wait to see final result
        print("\nWaiting 5 seconds before closing...")
        await scraper.page.wait_for_timeout(5000)

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close_browser()
        print("\n✓ Browser closed")


if __name__ == "__main__":
    print("Testing Date Navigation")
    print("=" * 60)
    asyncio.run(test_date_navigation())
