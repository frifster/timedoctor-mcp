"""
Test MCP server parallel scraping integration.
"""

import asyncio
from datetime import datetime, timedelta
from src.mcp_server import handle_export_weekly_csv


async def test_auto_detection():
    """Test auto-detection of parallel vs sequential."""
    print("=" * 60)
    print("TEST: Auto-detection")
    print("=" * 60)

    # Test 1: Recent dates (should use parallel)
    today = datetime.now()
    recent_start = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    recent_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\n1. Recent dates ({recent_start} to {recent_end})")
    print("   Expected: parallel (auto: recent dates)")

    result = await handle_export_weekly_csv(
        {"start_date": recent_start, "end_date": recent_end, "format": "csv", "parallel": "auto"}
    )

    response = result[0].text
    if "parallel (auto: recent dates)" in response:
        print("   ✓ PASS: Used parallel scraping")
    else:
        print("   ✗ FAIL: Did not use parallel scraping")

    # Test 2: Old dates (should use sequential)
    old_start = "2025-10-10"
    old_end = "2025-10-14"

    print(f"\n2. Old dates ({old_start} to {old_end})")
    print("   Expected: sequential (auto: old dates)")

    result = await handle_export_weekly_csv(
        {"start_date": old_start, "end_date": old_end, "format": "csv", "parallel": "auto"}
    )

    response = result[0].text
    if "sequential (auto: old dates)" in response:
        print("   ✓ PASS: Used sequential scraping")
    else:
        print("   ✗ FAIL: Did not use sequential scraping")


async def test_force_modes():
    """Test forcing parallel/sequential modes."""
    print("\n" + "=" * 60)
    print("TEST: Force modes")
    print("=" * 60)

    # Test 3: Force parallel
    print(f"\n3. Force parallel (old dates)")
    print("   Expected: parallel (forced)")

    result = await handle_export_weekly_csv(
        {
            "start_date": "2025-10-10",
            "end_date": "2025-10-14",
            "format": "csv",
            "parallel": "true",
        }
    )

    response = result[0].text
    if "parallel (forced)" in response:
        print("   ✓ PASS: Used parallel scraping (forced)")
    else:
        print("   ✗ FAIL: Did not use parallel scraping")

    # Test 4: Force sequential
    today = datetime.now()
    recent_start = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    recent_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\n4. Force sequential (recent dates)")
    print("   Expected: sequential (forced)")

    result = await handle_export_weekly_csv(
        {
            "start_date": recent_start,
            "end_date": recent_end,
            "format": "csv",
            "parallel": "false",
        }
    )

    response = result[0].text
    if "sequential (forced)" in response:
        print("   ✓ PASS: Used sequential scraping (forced)")
    else:
        print("   ✗ FAIL: Did not use sequential scraping")


async def test_json_format():
    """Test JSON format with parallel."""
    print("\n" + "=" * 60)
    print("TEST: JSON format with parallel")
    print("=" * 60)

    today = datetime.now()
    recent_start = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    recent_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\n5. JSON format with auto-parallel ({recent_start} to {recent_end})")

    result = await handle_export_weekly_csv(
        {
            "start_date": recent_start,
            "end_date": recent_end,
            "format": "json",
            "parallel": "auto",
        }
    )

    response = result[0].text
    if "parallel (auto: recent dates)" in response and '"entries"' in response:
        print("   ✓ PASS: Used parallel with JSON format")
    else:
        print("   ✗ FAIL: Incorrect mode or format")


async def main():
    print("\nTesting MCP Server Parallel Integration\n")

    try:
        await test_auto_detection()
        await test_force_modes()
        await test_json_format()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
