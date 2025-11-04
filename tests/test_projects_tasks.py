"""
Test accessing Projects & Tasks report directly
"""

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def test_projects_tasks():
    """Test accessing Projects & Tasks report."""

    email = os.getenv("TD_EMAIL")
    password = os.getenv("TD_PASSWORD")

    print("═" * 70)
    print("Testing Projects & Tasks Report")
    print("═" * 70)
    print()

    playwright = None
    browser = None

    try:
        playwright = await async_playwright().start()

        print("Starting browser...")
        browser = await playwright.chromium.launch(headless=False, args=["--no-sandbox"])

        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        page = await context.new_page()
        page.set_default_timeout(60000)

        # Login
        print("Logging in...")
        await page.goto("https://2.timedoctor.com/login", wait_until="load")
        await page.wait_for_timeout(2000)

        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)

        print(f"✅ Logged in: {page.url}")
        print()

        # Try direct URL to Projects & Tasks
        print("Attempting direct URL to Projects & Tasks...")
        possible_urls = [
            "https://2.timedoctor.com/reports/projects",
            "https://2.timedoctor.com/reports/projects-tasks",
            "https://2.timedoctor.com/reports/project",
            "https://2.timedoctor.com/app/reports/projects",
        ]

        for url in possible_urls:
            print(f"  Trying: {url}")
            try:
                response = await page.goto(url, wait_until="load", timeout=10000)
                await page.wait_for_timeout(2000)

                if response.status == 200:
                    print(f"  ✅ Success! Status: {response.status}")
                    print(f"     Current URL: {page.url}")
                    break
                else:
                    print(f"  ❌ Status: {response.status}")
            except Exception as e:
                print(f"  ❌ Failed: {str(e)[:50]}")

        print()
        await page.screenshot(path="projects_tasks_page.png")
        print("📸 Screenshot: projects_tasks_page.png")
        print()

        # Look for data table
        print("Looking for data on page...")

        # Check for tables
        tables = await page.query_selector_all("table")
        print(f"  Found {len(tables)} tables")

        if tables:
            # Try to get first table's content
            first_table = tables[0]
            rows = await first_table.query_selector_all("tr")
            print(f"  First table has {len(rows)} rows")

            if rows and len(rows) > 0:
                print()
                print("  Sample data from first few rows:")
                for i, row in enumerate(rows[:5]):
                    cells = await row.query_selector_all("td, th")
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip())

                    if cell_texts:
                        print(f"    Row {i+1}: {' | '.join(cell_texts[:6])}")

        # Look for project/task specific elements
        print()
        print("Looking for project/task elements...")

        project_elems = await page.query_selector_all('[class*="project"], [data-*="project"]')
        print(f"  Found {len(project_elems)} project-related elements")

        task_elems = await page.query_selector_all('[class*="task"], [data-*="task"]')
        print(f"  Found {len(task_elems)} task-related elements")

        # Look for time data
        time_elems = await page.query_selector_all(
            '[class*="time"], [class*="duration"], [class*="hour"]'
        )
        print(f"  Found {len(time_elems)} time-related elements")

        print()
        print("Waiting 30 seconds for you to explore...")
        print("(Check the browser window!)")
        for i in range(30, 0, -5):
            print(f"  {i} seconds...")
            await asyncio.sleep(5)

        await page.screenshot(path="projects_tasks_final.png")
        print()
        print("📸 Final screenshot: projects_tasks_final.png")
        print(f"   Final URL: {page.url}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print()
        print("Closing browser...")
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

    print()
    print("═" * 70)
    print("Test Complete!")
    print("═" * 70)


if __name__ == "__main__":
    asyncio.run(test_projects_tasks())
