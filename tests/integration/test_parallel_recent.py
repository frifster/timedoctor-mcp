"""
Test parallel scraping with RECENT dates to show the performance benefit.
"""

import asyncio
import time
from datetime import datetime, timedelta
from src.scraper import TimeDocorScraper
from src.parser import TimeDocorParser


async def test_recent_dates():
    """Test with recent dates (last 5 days)."""
    # Calculate last 5 days
    today = datetime.now()
    dates = []
    for i in range(5, 0, -1):
        date = today - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))

    start_date = dates[0]
    end_date = dates[-1]

    print(f"Testing with recent dates: {start_date} to {end_date}")
    print(f"(Only {5} days of navigation per date)")
    print()

    # Clear cache
    import os
    import shutil

    if os.path.exists(".cache"):
        shutil.rmtree(".cache")

    # Test sequential
    scraper1 = TimeDocorScraper()
    parser = TimeDocorParser()

    try:
        print("=" * 60)
        print("SEQUENTIAL (recent dates)")
        print("=" * 60)

        await scraper1.start_browser()
        await scraper1.login()

        start_time = time.time()
        reports = await scraper1.get_date_range_reports(start_date, end_date)
        elapsed_seq = time.time() - start_time

        print(f"\n✓ Sequential: {elapsed_seq:.1f}s")

        total = 0
        for report in reports:
            entries = parser.parse_daily_report(report["html"], report["date"])
            total += len(entries)
            hours = sum(e["seconds"] for e in entries) / 3600
            print(f"  {report['date']}: {len(entries)} entries, {hours:.2f}h")

        print(f"Total: {total} entries")

        await scraper1.close_browser()

    except Exception as e:
        print(f"ERROR: {e}")
        if scraper1.browser:
            await scraper1.close_browser()
        return

    # Clear cache again
    if os.path.exists(".cache"):
        shutil.rmtree(".cache")

    await asyncio.sleep(3)

    # Test parallel
    scraper2 = TimeDocorScraper()

    try:
        print("\n" + "=" * 60)
        print("PARALLEL (recent dates)")
        print("=" * 60)

        await scraper2.start_browser()

        start_time = time.time()
        reports = await scraper2.get_date_range_reports_parallel(start_date, end_date)
        elapsed_par = time.time() - start_time

        print(f"\n✓ Parallel: {elapsed_par:.1f}s")

        total = 0
        for report in reports:
            entries = parser.parse_daily_report(report["html"], report["date"])
            total += len(entries)
            hours = sum(e["seconds"] for e in entries) / 3600
            print(f"  {report['date']}: {len(entries)} entries, {hours:.2f}h")

        print(f"Total: {total} entries")

        await scraper2.close_browser()

        # Show comparison
        print("\n" + "=" * 60)
        print("COMPARISON")
        print("=" * 60)
        print(f"Sequential: {elapsed_seq:.1f}s")
        print(f"Parallel:   {elapsed_par:.1f}s")
        if elapsed_par < elapsed_seq:
            speedup = elapsed_seq / elapsed_par
            print(f"Speedup:    {speedup:.1f}x faster ✓")
            print(f"Time saved: {elapsed_seq - elapsed_par:.1f}s")
        else:
            print(f"Parallel was slower (expected for far historical dates)")

    except Exception as e:
        print(f"ERROR: {e}")
        if scraper2.browser:
            await scraper2.close_browser()


if __name__ == "__main__":
    asyncio.run(test_recent_dates())
