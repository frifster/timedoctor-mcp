#!/usr/bin/env python3
"""
Debug script to test login with new smart waits
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraper import TimeDocorScraper


async def main():
    print("=" * 60)
    print("Testing Time Doctor Login with Smart Waits")
    print("=" * 60)
    print()

    # Create scraper
    scraper = TimeDocorScraper()

    try:
        print("1. Starting browser...")
        await scraper.start_browser()
        print("   ✓ Browser started\n")

        print("2. Attempting login...")
        print(f"   Email: {scraper.email}")
        print(f"   URL: {scraper.base_url}/login")
        print()

        success = await scraper.login()

        if success:
            print("   ✓ Login successful!")
            print(f"   Current URL: {scraper.page.url}")
        else:
            print("   ✗ Login failed!")
            print(f"   Current URL: {scraper.page.url}")

            # Take screenshot for debugging
            screenshot_path = Path(__file__).parent / "debug_login_failed.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            print(f"   Screenshot saved: {screenshot_path}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n3. Closing browser...")
        await scraper.close_browser()
        print("   ✓ Browser closed")

    print()
    print("=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
