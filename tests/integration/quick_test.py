import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def quick_test():
    email = os.getenv("TD_EMAIL")
    password = os.getenv("TD_PASSWORD")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await (await browser.new_context()).new_page()

    # Login
    await page.goto("https://2.timedoctor.com/login", wait_until="load")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"]', email)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_timeout(5000)

    print(f"✅ Logged in: {page.url}")

    # Try the suggested URL
    print("\nTrying: https://2.timedoctor.com/projects-report")
    await page.goto("https://2.timedoctor.com/projects-report", wait_until="load")
    await page.wait_for_timeout(3000)

    print(f"Current URL: {page.url}")
    await page.screenshot(path="projects_report.png")
    print("Screenshot: projects_report.png")

    # Look for data
    tables = await page.query_selector_all("table")
    print(f"\nFound {len(tables)} tables")

    if tables:
        rows = await tables[0].query_selector_all("tr")
        print(f"First table has {len(rows)} rows")
        print("\nSample data:")
        for _i, row in enumerate(rows[:5]):
            cells = await row.query_selector_all("td, th")
            texts = [await c.inner_text() for c in cells]
            print(f"  {' | '.join(texts[:6])}")

    print("\nWaiting 20 seconds...")
    await asyncio.sleep(20)

    await browser.close()
    await playwright.stop()


asyncio.run(quick_test())
