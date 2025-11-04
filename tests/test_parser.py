"""
Test the parser with real HTML from sample_report.html
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parser import TimeDocorParser
from transformer import TimeDocorTransformer


def test_parser():
    """Test parser with saved HTML."""
    print("\nTest: HTML Parser")
    print("=" * 60)

    # Read the saved HTML
    html_file = Path(__file__).parent / "sample_report.html"
    if not html_file.exists():
        print(f"✗ HTML file not found: {html_file}")
        return False

    with open(html_file, encoding="utf-8") as f:
        html = f.read()

    print(f"✓ Loaded HTML file: {len(html)} bytes")

    # Parse it
    parser = TimeDocorParser()
    entries = parser.parse_daily_report(html, "2025-11-04")

    print(f"✓ Parsed {len(entries)} entries")

    if len(entries) == 0:
        print("✗ No entries found!")
        return False

    # Display entries
    print("\nEntries found:")
    print("-" * 60)
    for entry in entries:
        print(f"  Project: {entry['project']}")
        print(f"  Task: {entry['task']}")
        print(f"  Description: {entry['description']}")
        print(f"  Time: {entry['seconds']}s ({entry['seconds']/3600:.2f}h)")
        print("-" * 60)

    # Transform to CSV format
    transformer = TimeDocorTransformer()
    transformed = transformer.transform_entries(entries)

    total_hours = transformer.calculate_total(transformed)
    print(f"\nTotal Hours: {total_hours:.2f}")

    summary = transformer.get_hours_summary(transformed)
    print("\nHours by Project:")
    for project, hours in sorted(summary.items()):
        print(f"  {project}: {hours:.2f}h")

    return True


if __name__ == "__main__":
    success = test_parser()
    print("\n" + "=" * 60)
    if success:
        print("✓ Parser test PASSED!")
    else:
        print("✗ Parser test FAILED!")
    print("=" * 60)
