"""
Test complete end-to-end flow:
1. Login once
2. Get data for multiple dates (single session)
3. Parse the data
4. Export to CSV

This tests the full single-session architecture with variable date ranges.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parser import TimeDocorParser
from scraper import TimeDocorScraper
from transformer import TimeDocorTransformer, export_to_csv


async def test_complete_flow():
    """Test complete flow with multiple dates in single session."""
    print("\nTest: Complete End-to-End Flow")
    print("=" * 60)

    scraper = TimeDocorScraper()
    parser = TimeDocorParser()
    transformer = TimeDocorTransformer()

    try:
        # Test with last 3 days
        today = datetime.now()
        start_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        print(f"\nDate Range: {start_date} to {end_date} (3 days)")
        print("-" * 60)

        # Step 1: Get data in single session
        print("\n1. Collecting data in single session...")
        reports = await scraper.get_date_range_data_single_session(start_date, end_date)
        print(f"   ✓ Got {len(reports)} reports")

        for report in reports:
            html_size = len(report["html"]) / 1024  # KB
            print(f"   - {report['date']}: {html_size:.1f} KB")

        # Step 2: Parse all reports
        print("\n2. Parsing HTML data...")
        all_entries = []
        for report in reports:
            entries = parser.parse_daily_report(report["html"], report["date"])
            all_entries.extend(entries)
            print(f"   - {report['date']}: {len(entries)} entries")

        print(f"   ✓ Total entries: {len(all_entries)}")

        # Step 3: Aggregate by task
        print("\n3. Aggregating entries by task...")
        aggregated = parser.aggregate_by_task(all_entries)
        print(f"   ✓ Aggregated to {len(aggregated)} unique tasks")

        # Step 4: Transform to CSV format
        print("\n4. Transforming to CSV format...")
        transformed = transformer.transform_entries(aggregated)
        print(f"   ✓ {len(transformed)} entries ready for export")

        # Step 5: Calculate summary
        print("\n5. Calculating summary...")
        total_hours = transformer.calculate_total(transformed)
        summary = transformer.get_hours_summary(transformed)

        print(f"   Total Hours: {total_hours:.2f}")
        print("\n   Hours by Project:")
        for project, hours in sorted(summary.items()):
            print(f"     - {project}: {hours:.2f}h")

        # Step 6: Export to CSV
        print("\n6. Exporting to CSV...")
        output_file = "test_complete_flow_output.csv"
        csv_path = export_to_csv(aggregated, output_file, include_total=True)
        print(f"   ✓ Exported to: {csv_path}")

        # Step 7: Verify CSV file
        print("\n7. Verifying CSV file...")
        with open(csv_path) as f:
            lines = f.readlines()
            print(f"   ✓ CSV has {len(lines)} lines (including header and TOTAL)")
            print("\n   First 5 lines:")
            for line in lines[:5]:
                print(f"     {line.strip()}")
            if len(lines) > 5:
                print("   ...\n   Last line:")
                print(f"     {lines[-1].strip()}")

        print("\n" + "=" * 60)
        print("✓ Complete flow test PASSED!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_single_day():
    """Test with a single day (edge case)."""
    print("\nTest: Single Day")
    print("=" * 60)

    scraper = TimeDocorScraper()

    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        print(f"\nDate: {yesterday}")
        print("-" * 60)

        reports = await scraper.get_date_range_data_single_session(yesterday, yesterday)
        print(f"✓ Got {len(reports)} report (should be 1)")

        if len(reports) == 1:
            print("✓ Single day test PASSED")
            return True
        else:
            print(f"✗ Expected 1 report, got {len(reports)}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_week():
    """Test with a full week."""
    print("\nTest: Full Week")
    print("=" * 60)

    scraper = TimeDocorScraper()

    try:
        today = datetime.now()
        start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        print(f"\nDate Range: {start_date} to {end_date} (7 days)")
        print("-" * 60)

        reports = await scraper.get_date_range_data_single_session(start_date, end_date)
        print(f"✓ Got {len(reports)} reports (should be 7)")

        if len(reports) == 7:
            print("✓ Week test PASSED")
            return True
        else:
            print(f"✗ Expected 7 reports, got {len(reports)}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("COMPLETE FLOW TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Complete flow with 3 days
    result1 = await test_complete_flow()
    results.append(("Complete Flow (3 days)", result1))

    # Test 2: Single day
    result2 = await test_single_day()
    results.append(("Single Day", result2))

    # Test 3: Full week
    result3 = await test_week()
    results.append(("Full Week", result3))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n✓ All tests PASSED!")
    else:
        print("\n✗ Some tests FAILED")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
