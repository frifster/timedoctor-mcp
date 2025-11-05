"""
Test parallel scraping performance vs sequential scraping.
"""

import asyncio
import time
from src.scraper import TimeDocorScraper
from src.parser import TimeDocorParser


async def test_sequential():
    """Test sequential scraping (current method)."""
    scraper = TimeDocorScraper()
    parser = TimeDocorParser()

    try:
        print("=" * 60)
        print("SEQUENTIAL SCRAPING TEST")
        print("=" * 60)

        await scraper.start_browser()
        await scraper.login()

        start_time = time.time()

        # Get 5 dates sequentially
        reports = await scraper.get_date_range_reports("2025-10-10", "2025-10-14")

        elapsed = time.time() - start_time

        print(f"\n✓ Sequential: Retrieved {len(reports)} dates in {elapsed:.1f}s")
        print(f"  Average: {elapsed / len(reports):.1f}s per date")

        # Parse and show results
        total_entries = 0
        for report in reports:
            entries = parser.parse_daily_report(report["html"], report["date"])
            total_entries += len(entries)
            hours = sum(e["seconds"] for e in entries) / 3600
            print(f"  {report['date']}: {len(entries)} entries, {hours:.2f}h")

        print(f"\nTotal: {total_entries} entries")

        await scraper.close_browser()
        return elapsed

    except Exception as e:
        print(f"ERROR: {e}")
        if scraper.browser:
            await scraper.close_browser()
        raise


async def test_parallel():
    """Test parallel scraping (new method)."""
    scraper = TimeDocorScraper()
    parser = TimeDocorParser()

    try:
        print("\n" + "=" * 60)
        print("PARALLEL SCRAPING TEST")
        print("=" * 60)

        await scraper.start_browser()

        start_time = time.time()

        # Get 5 dates in parallel
        reports = await scraper.get_date_range_reports_parallel("2025-10-10", "2025-10-14")

        elapsed = time.time() - start_time

        print(f"\n✓ Parallel: Retrieved {len(reports)} dates in {elapsed:.1f}s")
        print(f"  Average: {elapsed / len(reports):.1f}s per date")

        # Parse and show results
        total_entries = 0
        for report in reports:
            entries = parser.parse_daily_report(report["html"], report["date"])
            total_entries += len(entries)
            hours = sum(e["seconds"] for e in entries) / 3600
            print(f"  {report['date']}: {len(entries)} entries, {hours:.2f}h")

        print(f"\nTotal: {total_entries} entries")

        await scraper.close_browser()
        return elapsed

    except Exception as e:
        print(f"ERROR: {e}")
        if scraper.browser:
            await scraper.close_browser()
        raise


async def main():
    # Clear cache to ensure fair comparison
    import os
    import shutil

    if os.path.exists(".cache"):
        shutil.rmtree(".cache")
        print("Cleared cache for fair comparison\n")

    # Test sequential first
    sequential_time = await test_sequential()

    # Clear cache again
    if os.path.exists(".cache"):
        shutil.rmtree(".cache")

    # Wait a bit between tests
    await asyncio.sleep(3)

    # Test parallel
    parallel_time = await test_parallel()

    # Show comparison
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"Sequential: {sequential_time:.1f}s")
    print(f"Parallel:   {parallel_time:.1f}s")
    print(f"Speedup:    {sequential_time / parallel_time:.1f}x faster")
    print(f"Time saved: {sequential_time - parallel_time:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
