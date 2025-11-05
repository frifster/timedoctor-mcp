"""
Test new features: min_hours filter and execution_time in JSON output.
"""

import asyncio
import json
from datetime import datetime, timedelta
from src.mcp_server import handle_export_weekly_csv


async def test_min_hours_filter():
    """Test min_hours filtering."""
    print("=" * 60)
    print("TEST: min_hours Filter")
    print("=" * 60)

    # Get recent data
    today = datetime.now()
    start = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    # Test 1: No filter
    print(f"\n1. No filter (min_hours=0)")
    result = await handle_export_weekly_csv(
        {"start_date": start, "end_date": end, "format": "csv", "min_hours": 0}
    )
    response = result[0].text
    lines = response.split("\n")
    for line in lines:
        if "Total Entries:" in line:
            print(f"   {line.strip()}")
            break

    # Test 2: Filter < 0.1 hours (6 minutes)
    print(f"\n2. Filter entries < 0.1h (6 minutes)")
    result = await handle_export_weekly_csv(
        {"start_date": start, "end_date": end, "format": "csv", "min_hours": 0.1}
    )
    response = result[0].text
    lines = response.split("\n")
    for line in lines:
        if "Total Entries:" in line or "Min hours filter:" in line:
            print(f"   {line.strip()}")

    # Test 3: High filter (1 hour)
    print(f"\n3. Filter entries < 1.0h")
    result = await handle_export_weekly_csv(
        {"start_date": start, "end_date": end, "format": "csv", "min_hours": 1.0}
    )
    response = result[0].text
    lines = response.split("\n")
    for line in lines:
        if "Total Entries:" in line or "Min hours filter:" in line:
            print(f"   {line.strip()}")


async def test_json_execution_time():
    """Test execution_time in JSON output."""
    print("\n" + "=" * 60)
    print("TEST: JSON Execution Time")
    print("=" * 60)

    today = datetime.now()
    start = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    # Test with parallel
    print(f"\n1. JSON output with parallel scraping")
    result = await handle_export_weekly_csv(
        {
            "start_date": start,
            "end_date": end,
            "format": "json",
            "parallel": "auto",
            "min_hours": 0.1,
        }
    )

    response = result[0].text
    # Extract JSON part
    json_start = response.find("{")
    if json_start != -1:
        json_str = response[json_start:]
        data = json.loads(json_str)

        print(f"   Scraping method: {data.get('scraping_method', 'N/A')}")
        print(f"   Execution time: {data.get('execution_time_seconds', 'N/A')}s")
        print(f"   Total entries: {data.get('count', 0)}")
        if "min_hours_filter" in data:
            print(f"   Min hours filter: {data['min_hours_filter']}h")
            print(f"   Entries filtered: {data.get('entries_filtered', 0)}")
        if "total_hours" in data:
            print(f"   Total hours: {data['total_hours']:.2f}h")


async def test_combined_features():
    """Test all features together."""
    print("\n" + "=" * 60)
    print("TEST: Combined Features")
    print("=" * 60)

    # Old dates, sequential, JSON, with filter
    print(f"\n1. Old dates + sequential + JSON + min_hours filter")
    result = await handle_export_weekly_csv(
        {
            "start_date": "2025-10-10",
            "end_date": "2025-10-14",
            "format": "json",
            "parallel": "false",  # Force sequential
            "min_hours": 1.0,  # Only entries >= 1 hour
        }
    )

    response = result[0].text
    json_start = response.find("{")
    if json_start != -1:
        json_str = response[json_start:]
        data = json.loads(json_str)

        print(f"   ✓ Scraping method: {data.get('scraping_method', 'N/A')}")
        print(f"   ✓ Execution time: {data.get('execution_time_seconds', 'N/A')}s")
        print(f"   ✓ Min hours filter: {data.get('min_hours_filter', 'N/A')}h")
        print(f"   ✓ Entries filtered: {data.get('entries_filtered', 'N/A')}")
        print(f"   ✓ Final entry count: {data.get('count', 0)}")
        print(f"   ✓ Total hours: {data.get('total_hours', 0):.2f}h")


async def main():
    print("\nTesting New Features: min_hours Filter & Execution Time\n")

    try:
        await test_min_hours_filter()
        await test_json_execution_time()
        await test_combined_features()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
