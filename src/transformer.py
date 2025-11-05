"""
Time Doctor Data Transformer
Transforms parsed time tracking data to CSV format
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Get project directories
script_dir = Path(__file__).parent
project_dir = script_dir.parent
output_dir = project_dir / "output"

# Ensure output directory exists
output_dir.mkdir(exist_ok=True)


class TimeDocorTransformer:
    """
    Transforms Time Doctor data to CSV format.
    Handles formatting, aggregation, and export.
    """

    def __init__(self):
        """Initialize the transformer."""
        logger.info("TimeDocorTransformer initialized")

    def seconds_to_decimal_hours(self, seconds: int) -> float:
        """
        Convert seconds to decimal hours.

        Args:
            seconds: Time in seconds

        Returns:
            float: Time in decimal hours (e.g., 5.00, 1.50)
        """
        return round(seconds / 3600, 2)

    def format_date(self, date_str: str, output_format: str = "%m/%d/%Y") -> str:
        """
        Format date string to desired output format.

        Args:
            date_str: Date in YYYY-MM-DD format
            output_format: Desired output format (default: MM/DD/YYYY)

        Returns:
            str: Formatted date string
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime(output_format)
        except Exception as e:
            logger.warning(f"Error formatting date '{date_str}': {e}")
            return date_str

    def transform_entries(self, entries: list[dict]) -> list[dict]:
        """
        Transform parsed entries to CSV-ready format.

        Args:
            entries: List of parsed time entries

        Returns:
            List[Dict]: Transformed entries with CSV columns
        """
        transformed = []

        for entry in entries:
            transformed_entry = {
                "Date": self.format_date(entry["date"]),
                "Project": entry["project"],
                "Task": entry["task"],
                "Description": entry["description"],
                "WORK HOUR": self.seconds_to_decimal_hours(entry["seconds"]),
            }
            transformed.append(transformed_entry)

        logger.info(f"Transformed {len(transformed)} entries")
        return transformed

    def calculate_total(self, entries: list[dict]) -> float:
        """
        Calculate total hours from entries.

        Args:
            entries: List of transformed entries

        Returns:
            float: Total hours
        """
        total = sum(entry["WORK HOUR"] for entry in entries)
        return round(total, 2)

    def sort_entries(self, entries: list[dict], sort_by: str = "Date") -> list[dict]:
        """
        Sort entries by specified field.

        Args:
            entries: List of entries
            sort_by: Field name to sort by (default: Date)

        Returns:
            List[Dict]: Sorted entries
        """
        try:
            return sorted(entries, key=lambda x: x.get(sort_by, ""))
        except Exception as e:
            logger.warning(f"Error sorting entries: {e}")
            return entries

    def export_to_csv(
        self, entries: list[dict], output_file: str, include_total: bool = True
    ) -> str:
        """
        Export transformed entries to CSV file.

        Args:
            entries: List of transformed entries (with CSV columns)
            output_file: Output CSV file path (relative or absolute)
            include_total: Whether to include TOTAL row (default: True)

        Returns:
            str: Path to the created CSV file
        """
        try:
            # Convert to absolute path if relative
            output_path = Path(output_file)
            if not output_path.is_absolute():
                output_path = output_dir / output_file

            logger.info(f"Exporting {len(entries)} entries to {output_path}")

            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Define CSV columns
            fieldnames = ["Date", "Project", "Task", "Description", "WORK HOUR"]

            # Write CSV
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()

                # Write data rows
                for entry in entries:
                    writer.writerow(entry)

                # Write TOTAL row if requested
                if include_total and entries:
                    total_hours = self.calculate_total(entries)
                    total_row = {
                        "Date": "TOTAL",
                        "Project": "",
                        "Task": "",
                        "Description": "",
                        "WORK HOUR": total_hours,
                    }
                    writer.writerow(total_row)

            logger.info(f"CSV exported successfully to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise

    def get_hours_summary(self, entries: list[dict]) -> dict[str, float]:
        """
        Get hours summary grouped by project.

        Args:
            entries: List of transformed entries

        Returns:
            Dict[str, float]: Project name to total hours mapping
        """
        summary = {}

        for entry in entries:
            project = entry["Project"]
            hours = entry["WORK HOUR"]

            if project in summary:
                summary[project] += hours
            else:
                summary[project] = hours

        # Round all values
        summary = {k: round(v, 2) for k, v in summary.items()}

        logger.info(f"Generated hours summary for {len(summary)} projects")
        return summary

    def format_summary_text(self, summary: dict[str, float]) -> str:
        """
        Format hours summary as readable text.

        Args:
            summary: Project to hours mapping

        Returns:
            str: Formatted summary text
        """
        lines = ["Hours Summary by Project:", "=" * 40]

        for project, hours in sorted(summary.items()):
            lines.append(f"{project}: {hours:.2f} hours")

        total = sum(summary.values())
        lines.append("=" * 40)
        lines.append(f"TOTAL: {total:.2f} hours")

        return "\n".join(lines)


def export_to_csv(entries: list[dict], output_file: str, include_total: bool = True) -> str:
    """
    Convenience function to transform and export entries to CSV.

    Args:
        entries: List of parsed time entries (raw format)
        output_file: Output CSV file path
        include_total: Whether to include TOTAL row

    Returns:
        str: Path to the created CSV file
    """
    transformer = TimeDocorTransformer()

    # Transform entries
    transformed = transformer.transform_entries(entries)

    # Sort by date
    transformed = transformer.sort_entries(transformed, sort_by="Date")

    # Export to CSV
    return transformer.export_to_csv(transformed, output_file, include_total)


def entries_to_csv_string(entries: list[dict], include_total: bool = True) -> str:
    """
    Convert entries to CSV string format (for MCP server output).

    Args:
        entries: List of parsed time entries (raw format)
        include_total: Whether to include TOTAL row

    Returns:
        str: CSV formatted string
    """
    import io

    transformer = TimeDocorTransformer()

    # Transform entries
    transformed = transformer.transform_entries(entries)

    # Sort by date
    transformed = transformer.sort_entries(transformed, sort_by="Date")

    # Create CSV in memory
    output = io.StringIO()
    fieldnames = ["Date", "Project", "Task", "Description", "WORK HOUR"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    # Write header
    writer.writeheader()

    # Write data rows
    for entry in transformed:
        writer.writerow(entry)

    # Add TOTAL row if requested
    if include_total and transformed:
        total_hours = transformer.calculate_total(transformed)
        total_row = {
            "Date": "TOTAL",
            "Project": "",
            "Task": "",
            "Description": "",
            "WORK HOUR": total_hours,
        }
        writer.writerow(total_row)

    return output.getvalue()


def entries_to_json_string(entries: list[dict], include_total: bool = True, indent: int = 2) -> str:
    """
    Convert entries to JSON string format (for MCP server output).

    Args:
        entries: List of parsed time entries (raw format)
        include_total: Whether to include total_hours field
        indent: JSON indentation level (default: 2, None for compact)

    Returns:
        str: JSON formatted string
    """
    transformer = TimeDocorTransformer()

    # Transform entries
    transformed = transformer.transform_entries(entries)

    # Sort by date
    transformed = transformer.sort_entries(transformed, sort_by="Date")

    # Create output structure
    output_data = {
        "entries": transformed,
        "count": len(transformed),
    }

    # Add total if requested
    if include_total and transformed:
        total_hours = transformer.calculate_total(transformed)
        output_data["total_hours"] = total_hours

        # Calculate total seconds from original entries
        total_seconds = sum(entry["seconds"] for entry in entries)
        output_data["total_seconds"] = total_seconds

        # Also add summary by project
        summary = transformer.get_hours_summary(transformed)
        output_data["summary_by_project"] = summary

    return json.dumps(output_data, indent=indent, ensure_ascii=False)


def get_hours_summary(entries: list[dict]) -> dict[str, float]:
    """
    Convenience function to get hours summary.

    Args:
        entries: List of parsed time entries (raw format)

    Returns:
        Dict[str, float]: Project to hours mapping
    """
    transformer = TimeDocorTransformer()

    # Transform entries
    transformed = transformer.transform_entries(entries)

    # Get summary
    return transformer.get_hours_summary(transformed)


# Example usage
if __name__ == "__main__":
    # Sample data
    sample_entries = [
        {
            "date": "2025-01-15",
            "project": "AYR",
            "task": "ABMS-202",
            "description": "Calendar Sync",
            "seconds": 18000,  # 5 hours
        },
        {
            "date": "2025-01-15",
            "project": "AYR",
            "task": "ABMS-3144",
            "description": "Outlook Calendar Sync - Integration",
            "seconds": 3600,  # 1 hour
        },
        {
            "date": "2025-01-16",
            "project": "Project X",
            "task": "TASK-123",
            "description": "Development Work",
            "seconds": 27000,  # 7.5 hours
        },
    ]

    # Export to CSV
    output_file = export_to_csv(sample_entries, "test_report.csv")
    print(f"CSV exported to: {output_file}")

    # Get summary
    summary = get_hours_summary(sample_entries)
    transformer = TimeDocorTransformer()
    print("\n" + transformer.format_summary_text(summary))
