"""
Debug script to test Time Doctor login
Run with visible browser to see what's happening
"""

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def debug_login():
    """Test login with visible browser and better error handling."""

    email = os.getenv("TD_EMAIL")
    password = os.getenv("TD_PASSWORD")

    if not email or not password or email == "user@example.com":
        print("❌ Please configure TD_EMAIL and TD_PASSWORD in .env file")
        return False

    print(f"Testing login for: {email[:3]}***")
    print()

    playwright = None
    browser = None

    try:
        playwright = await async_playwright().start()

        print("1️⃣  Launching browser (visible mode)...")
        browser = await playwright.chromium.launch(
            headless=False,  # Visible browser to see what happens
            args=["--no-sandbox"],
        )

        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        page = await context.new_page()
        page.set_default_timeout(60000)  # Increased to 60 seconds

        login_url = "https://2.timedoctor.com/login"

        print(f"2️⃣  Navigating to {login_url}...")
        print("    (This might take a while...)")

        # Try with 'load' instead of 'networkidle' - less strict
        await page.goto(login_url, wait_until="load", timeout=60000)

        print("✅ Page loaded!")
        print()

        # Wait a bit for any dynamic content
        await page.wait_for_timeout(2000)

        print("3️⃣  Looking for login form...")

        # Look for email input with multiple possible selectors
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email"]',
            'input[placeholder*="email"]',
            "#email",
        ]

        email_input = None
        for selector in email_selectors:
            try:
                email_input = await page.query_selector(selector)
                if email_input:
                    print(f"✅ Found email input: {selector}")
                    break
            except Exception:
                continue

        if not email_input:
            print("❌ Could not find email input field")
            print("Page URL:", page.url)
            print()
            print("Let me take a screenshot...")
            await page.screenshot(path="debug_screenshot.png")
            print("Screenshot saved to: debug_screenshot.png")
            return False

        print("4️⃣  Filling in email...")
        await page.fill(email_selectors[0], email)

        print("5️⃣  Looking for password input...")
        password_input = await page.query_selector('input[type="password"]')

        if not password_input:
            print("❌ Could not find password input field")
            await page.screenshot(path="debug_screenshot.png")
            print("Screenshot saved to: debug_screenshot.png")
            return False

        print("6️⃣  Filling in password...")
        await page.fill('input[type="password"]', password)

        print("7️⃣  Looking for login button...")
        login_button_selectors = [
            'button[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            'input[type="submit"]',
        ]

        login_button = None
        for selector in login_button_selectors:
            try:
                login_button = await page.query_selector(selector)
                if login_button:
                    print(f"✅ Found login button: {selector}")
                    break
            except Exception:
                continue

        if not login_button:
            print("❌ Could not find login button")
            await page.screenshot(path="debug_screenshot.png")
            return False

        print("8️⃣  Clicking login button...")
        await page.click(login_button_selectors[0])

        print("9️⃣  Waiting for navigation...")

        # Wait for either success or error
        try:
            await page.wait_for_url("**/app/**", timeout=15000)
            print()
            print("✅ LOGIN SUCCESSFUL!")
            print(f"   Redirected to: {page.url}")
            print()

            # Take screenshot of logged in page
            await page.screenshot(path="logged_in_screenshot.png")
            print("Screenshot saved to: logged_in_screenshot.png")

            return True

        except Exception:
            print()
            print("⚠️  Did not redirect to app page")
            print(f"   Current URL: {page.url}")

            # Check for error messages
            error_elements = await page.query_selector_all('.error, .alert, [role="alert"]')
            if error_elements:
                print("   Found error messages:")
                for elem in error_elements:
                    text = await elem.inner_text()
                    if text:
                        print(f"   - {text}")

            await page.screenshot(path="debug_screenshot.png")
            print("   Screenshot saved to: debug_screenshot.png")

            # Check if we're actually logged in even if URL didn't change
            current_url = page.url
            if "/app/" in current_url and "/login" not in current_url:
                print()
                print("✅ Actually logged in! (URL different than expected)")
                return True

            return False

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        return False

    finally:
        print()
        print("🔟 Closing browser in 5 seconds...")
        print("   (Check the browser window now!)")
        await asyncio.sleep(5)

        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


if __name__ == "__main__":
    print("═" * 60)
    print("Time Doctor Login Debug Script")
    print("═" * 60)
    print()

    success = asyncio.run(debug_login())

    print()
    print("═" * 60)
    if success:
        print("✅ Login test PASSED")
        print()
        print("Your credentials work! The issue was just the timeout.")
        print("I'll update the scraper with better timeout settings.")
    else:
        print("❌ Login test FAILED")
        print()
        print("Check:")
        print("  1. Credentials in .env are correct")
        print("  2. debug_screenshot.png to see what happened")
        print("  3. Time Doctor website hasn't changed")
    print("═" * 60)
