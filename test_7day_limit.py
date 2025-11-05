#!/usr/bin/env python3
"""Test script to verify 7-day limit validation."""

from datetime import datetime, timedelta


def test_date_range_validation():
    """Test the date range validation logic."""
    print("Testing 7-day limit validation...\n")

    # Test cases
    test_cases = [
        ("2025-10-01", "2025-10-07", 7, False, "Exactly 7 days - should PASS"),
        ("2025-10-01", "2025-10-06", 6, False, "6 days - should PASS"),
        ("2025-10-01", "2025-10-08", 8, True, "8 days - should FAIL"),
        ("2025-10-01", "2025-10-15", 15, True, "15 days - should FAIL"),
        ("2025-10-01", "2025-10-31", 31, True, "31 days - should FAIL"),
        ("2025-10-01", "2025-10-01", 1, False, "Single day - should PASS"),
    ]

    all_passed = True

    for start_date, end_date, expected_days, should_fail, description in test_cases:
        # Validate date range (max 7 days)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_diff = (end_dt - start_dt).days + 1  # +1 to include both start and end dates

        will_fail = days_diff > 7

        # Check if calculation is correct
        if days_diff != expected_days:
            print(f"❌ CALCULATION ERROR: {description}")
            print(f"   Expected {expected_days} days, got {days_diff} days")
            all_passed = False
            continue

        # Check if validation matches expectation
        if will_fail != should_fail:
            print(f"❌ VALIDATION ERROR: {description}")
            print(f"   Expected should_fail={should_fail}, got will_fail={will_fail}")
            all_passed = False
            continue

        status = "FAIL ❌" if will_fail else "PASS ✅"
        print(f"{status} {description}")
        print(f"     Range: {start_date} to {end_date} = {days_diff} days")

        if will_fail:
            # Generate suggestions
            num_requests = (days_diff + 6) // 7  # Round up
            print(f"     Suggested split: {num_requests} requests")
            suggestions = []
            current_start = start_dt
            for i in range(num_requests):
                chunk_end = min(current_start + timedelta(days=6), end_dt)
                chunk_days = (chunk_end - current_start).days + 1
                suggestions.append(
                    f"       {i+1}. {current_start.strftime('%Y-%m-%d')} to "
                    f"{chunk_end.strftime('%Y-%m-%d')} ({chunk_days} days)"
                )
                current_start = chunk_end + timedelta(days=1)
            print("\n".join(suggestions))

        print()

    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(test_date_range_validation())
