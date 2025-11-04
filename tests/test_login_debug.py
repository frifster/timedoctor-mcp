"""
Debug login issues - run with visible browser to see what's happening
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraper import TimeDocorScraper


async def test_login():
    """Test login with visible browser."""
    scraper = TimeDocorScraper()

    print(f"Email: {scraper.email}")
    print(f"Password: {'*' * len(scraper.password) if scraper.password else 'NOT SET'}")
    print(f"Base URL: {scraper.base_url}")
    print(f"Headless: {scraper.headless}")
    print()

    # Temporarily set to non-headless for debugging
    scraper.headless = False

    try:
        print("Starting browser (visible mode)...")
        await scraper.start_browser()
        print("✓ Browser started")
        print()

        print("Attempting login...")
        success = await scraper.login()

        if success:
            print("✅ Login successful!")
            print(f"Current URL: {scraper.page.url}")
        else:
            print("❌ Login failed!")
            print(f"Current URL: {scraper.page.url}")

            # Take screenshot
            screenshot_path = "login_failed.png"
            await scraper.page.screenshot(path=screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")

        # Keep browser open for 10 seconds so you can see
        print("\nKeeping browser open for 10 seconds...")
        await scraper.page.wait_for_timeout(10000)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close_browser()
        print("\n✓ Browser closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Time Doctor Login")
    print("=" * 60)
    print()
    asyncio.run(test_login())
