"""
Test total_seconds in JSON output.
"""

import asyncio
import json
from datetime import datetime, timedelta
from src.mcp_server import handle_export_weekly_csv


async def test_total_seconds():
    """Test that total_seconds appears in JSON output."""
    print("=" * 60)
    print("TEST: total_seconds in JSON Output")
    print("=" * 60)

    # Get recent data
    today = datetime.now()
    start = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nFetching data from {start} to {end}")

    result = await handle_export_weekly_csv(
        {"start_date": start, "end_date": end, "format": "json", "parallel": "auto", "min_hours": 0}
    )

    response = result[0].text

    # Extract JSON
    json_start = response.find("{")
    if json_start != -1:
        json_str = response[json_start:]
        data = json.loads(json_str)

        print(f"\n✓ JSON Output Fields:")
        print(f"  - entries: {data.get('count', 0)} items")
        print(f"  - total_hours: {data.get('total_hours', 0):.2f}h")
        print(f"  - total_seconds: {data.get('total_seconds', 'MISSING')}s")

        if "total_seconds" in data:
            total_seconds = data["total_seconds"]
            total_hours = data["total_hours"]

            # Verify calculation
            calculated_hours = total_seconds / 3600
            print(f"\n✓ Verification:")
            print(f"  {total_seconds}s ÷ 3600 = {calculated_hours:.2f}h")
            print(f"  Matches total_hours ({total_hours:.2f}h): {abs(calculated_hours - total_hours) < 0.01}")

            # Show example calculation
            print(f"\n✓ Example Usage:")
            print(f"  Total time tracked: {total_hours:.2f} hours")
            print(f"  Total time tracked: {total_seconds:,} seconds")
            print(f"  Total time tracked: {total_seconds // 60:,} minutes")

        else:
            print("\n✗ FAIL: total_seconds field is missing from JSON output!")

        # Show full JSON structure
        print(f"\n✓ Full JSON Structure:")
        print(f"  {json.dumps(data, indent=2)[:500]}...")


async def main():
    print("\nTesting total_seconds Field in JSON Output\n")

    try:
        await test_total_seconds()

        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
