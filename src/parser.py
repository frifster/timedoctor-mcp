"""
Time Doctor HTML Parser
Extracts time tracking data from Time Doctor HTML pages
"""

import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TimeDocorParser:
    """
    Parser for Time Doctor HTML content.
    Extracts time tracking entries from various report pages.
    """

    def __init__(self):
        """Initialize the parser."""
        logger.info("TimeDocorParser initialized")

    def parse_daily_report(self, html: str, date: str) -> list[dict]:
        """
        Parse daily report HTML and extract time tracking entries.

        Args:
            html: HTML content of the report page
            date: Date string in YYYY-MM-DD format

        Returns:
            List[Dict]: List of time entries with keys:
                - date: Date string
                - project: Project name
                - task: Task ID/name
                - description: Task description
                - seconds: Time in seconds
        """
        try:
            logger.info(f"Parsing daily report for {date}")
            soup = BeautifulSoup(html, "lxml")

            entries = []

            # Strategy 1: Parse Time Doctor mat-tree structure (Angular Material)
            entries.extend(self._parse_mat_tree(soup, date))

            # Strategy 2: Look for table rows with time data
            if not entries:
                entries.extend(self._parse_table_rows(soup, date))

            # Strategy 3: Look for div-based layouts (modern UI)
            if not entries:
                entries.extend(self._parse_div_layout(soup, date))

            # Strategy 4: Look for JSON data in script tags
            if not entries:
                entries.extend(self._parse_embedded_json(soup, date))

            logger.info(f"Parsed {len(entries)} time entries")
            return entries

        except Exception as e:
            logger.error(f"Error parsing daily report: {e}")
            raise

    def _parse_mat_tree(self, soup: BeautifulSoup, date: str) -> list[dict]:
        """
        Parse Time Doctor Angular Material tree structure.
        Projects are in first-level nodes, tasks are in second-level nodes.

        Args:
            soup: BeautifulSoup object
            date: Date string

        Returns:
            List[Dict]: Parsed entries
        """
        entries = []

        try:
            # Find all tree containers
            trees = soup.find_all("div", class_="tree")

            if not trees:
                logger.debug("No tree structures found")
                return entries

            current_project = ""

            for tree in trees:
                # Check if this is a project row (first-level)
                project_node = tree.find("div", class_="first-level")

                if project_node:
                    # Extract project name
                    project_name_elem = project_node.find("truncated-text", class_="project-name")
                    if project_name_elem:
                        project_text = project_name_elem.get_text(strip=True)
                        current_project = project_text
                        logger.debug(f"Found project: {current_project}")
                    continue

                # Check if this is a task row (second-level)
                task_node = tree.find("div", class_="second-level")

                if task_node and current_project:
                    # Extract task description
                    task_name_elem = task_node.find("truncated-text", class_="project-name")
                    if task_name_elem:
                        # Get text from span only (not from the link icon)
                        span_elem = task_name_elem.find("span", class_="truncated-content")
                        if span_elem:
                            task_text = span_elem.get_text(strip=True)
                        else:
                            task_text = task_name_elem.get_text(strip=True)
                            # Remove "launch" if it's at the end (from link icon)
                            task_text = task_text.replace("launch", "").strip()

                        # Extract task ID from description (e.g., "ABMS-606" from "Code Review - ABMS-606")
                        task_id = ""
                        import re

                        task_id_match = re.search(r"([A-Z]+-\d+)", task_text)
                        if task_id_match:
                            task_id = task_id_match.group(1)

                        # Extract time tracked
                        time_elem = task_node.find("span", class_="tracked-time")
                        if time_elem:
                            time_text = time_elem.get_text(strip=True)
                            seconds = self._parse_time_string(time_text)

                            if seconds > 0:
                                entry = {
                                    "date": date,
                                    "project": current_project,
                                    "task": task_id,
                                    "description": task_text,
                                    "seconds": seconds,
                                }
                                entries.append(entry)
                                logger.debug(f"Parsed entry: {task_id} - {seconds}s")

            logger.info(f"Extracted {len(entries)} entries from mat-tree structure")

        except Exception as e:
            logger.warning(f"Error parsing mat-tree structure: {e}")

        return entries

    def _parse_table_rows(self, soup: BeautifulSoup, date: str) -> list[dict]:
        """
        Parse table-based report layout.

        Args:
            soup: BeautifulSoup object
            date: Date string

        Returns:
            List[Dict]: Parsed entries
        """
        entries = []

        try:
            # Find tables that might contain time tracking data
            tables = soup.find_all(
                "table",
                class_=lambda x: x
                and any(
                    keyword in str(x).lower()
                    for keyword in ["report", "time", "task", "project", "data"]
                ),
            )

            if not tables:
                # Try finding any table
                tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(["td", "th"])

                    if len(cells) < 3:
                        continue

                    # Extract data from cells
                    # Common patterns: [Project, Task, Description, Time]
                    # or [Task, Project, Time, Actions]

                    project = ""
                    task = ""
                    description = ""
                    seconds = 0

                    # Try to identify which cell contains what
                    for _i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)

                        # Check for time patterns (HH:MM:SS or seconds or HH:MM)
                        time_match = re.search(r"(\d+):(\d+):(\d+)", cell_text)
                        if time_match:
                            hours = int(time_match.group(1))
                            minutes = int(time_match.group(2))
                            secs = int(time_match.group(3))
                            seconds = hours * 3600 + minutes * 60 + secs
                            continue

                        # Check for decimal hours (5.00, 1.50)
                        decimal_match = re.search(r"(\d+\.\d+)\s*h", cell_text)
                        if decimal_match:
                            hours = float(decimal_match.group(1))
                            seconds = int(hours * 3600)
                            continue

                        # Check for task IDs (e.g., ABMS-202)
                        if re.match(r"[A-Z]+-\d+", cell_text):
                            task = cell_text
                            continue

                        # First text cell is likely project
                        if not project and cell_text and len(cell_text) > 0:
                            project = cell_text
                        # Second text cell is likely description/task
                        elif not description and cell_text and len(cell_text) > 0:
                            if not task:
                                task = cell_text
                            else:
                                description = cell_text

                    # If we found time data, create entry
                    if seconds > 0:
                        entry = {
                            "date": date,
                            "project": project or "Unknown",
                            "task": task or "",
                            "description": description or task,
                            "seconds": seconds,
                        }
                        entries.append(entry)
                        logger.debug(f"Parsed entry: {entry}")

        except Exception as e:
            logger.warning(f"Error parsing table rows: {e}")

        return entries

    def _parse_div_layout(self, soup: BeautifulSoup, date: str) -> list[dict]:
        """
        Parse div-based report layout (modern UI).

        Args:
            soup: BeautifulSoup object
            date: Date string

        Returns:
            List[Dict]: Parsed entries
        """
        entries = []

        try:
            # Look for div containers with class patterns
            containers = soup.find_all(
                "div",
                class_=lambda x: x
                and any(
                    keyword in str(x).lower()
                    for keyword in ["task-item", "time-entry", "report-row", "activity"]
                ),
            )

            for container in containers:
                project = ""
                task = ""
                description = ""
                seconds = 0

                # Look for project name
                project_elem = container.find(class_=lambda x: x and "project" in str(x).lower())
                if project_elem:
                    project = project_elem.get_text(strip=True)

                # Look for task
                task_elem = container.find(class_=lambda x: x and "task" in str(x).lower())
                if task_elem:
                    task = task_elem.get_text(strip=True)

                # Look for description
                desc_elem = container.find(
                    class_=lambda x: x
                    and any(
                        keyword in str(x).lower() for keyword in ["description", "title", "name"]
                    )
                )
                if desc_elem:
                    description = desc_elem.get_text(strip=True)

                # Look for time/duration
                time_elem = container.find(
                    class_=lambda x: x
                    and any(keyword in str(x).lower() for keyword in ["time", "duration", "hours"])
                )
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    seconds = self._parse_time_string(time_text)

                if seconds > 0:
                    entry = {
                        "date": date,
                        "project": project or "Unknown",
                        "task": task or "",
                        "description": description or task,
                        "seconds": seconds,
                    }
                    entries.append(entry)
                    logger.debug(f"Parsed entry from div: {entry}")

        except Exception as e:
            logger.warning(f"Error parsing div layout: {e}")

        return entries

    def _parse_embedded_json(self, soup: BeautifulSoup, date: str) -> list[dict]:
        """
        Parse JSON data embedded in script tags.

        Args:
            soup: BeautifulSoup object
            date: Date string

        Returns:
            List[Dict]: Parsed entries
        """
        entries = []

        try:
            import json

            # Look for script tags with JSON data
            scripts = soup.find_all("script", type="application/json")
            scripts.extend(soup.find_all("script", string=lambda x: x and "window." in str(x)))

            for script in scripts:
                script_content = script.string

                if not script_content:
                    continue

                # Try to extract JSON objects
                json_matches = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", script_content)

                for json_str in json_matches:
                    try:
                        data = json.loads(json_str)

                        # Look for time tracking data patterns
                        if isinstance(data, dict):
                            entries.extend(self._extract_entries_from_dict(data, date))
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    entries.extend(self._extract_entries_from_dict(item, date))

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.warning(f"Error parsing embedded JSON: {e}")

        return entries

    def _extract_entries_from_dict(self, data: dict, date: str) -> list[dict]:
        """
        Extract time entries from a dictionary object.

        Args:
            data: Dictionary potentially containing time tracking data
            date: Date string

        Returns:
            List[Dict]: Parsed entries
        """
        entries = []

        # Look for common field names
        project = data.get("project", data.get("projectName", data.get("project_name", "")))
        task = data.get("task", data.get("taskName", data.get("task_name", data.get("taskId", ""))))
        description = data.get("description", data.get("title", data.get("name", "")))

        # Look for time/duration fields (in seconds)
        seconds = data.get("duration", data.get("time", data.get("seconds", data.get("length", 0))))

        # Convert if it's in milliseconds
        if isinstance(seconds, int | float) and seconds > 86400000:  # More than 24 hours in ms
            seconds = seconds / 1000

        if isinstance(seconds, int | float) and seconds > 0:
            entry = {
                "date": date,
                "project": str(project) if project else "Unknown",
                "task": str(task) if task else "",
                "description": str(description) if description else str(task),
                "seconds": int(seconds),
            }
            entries.append(entry)

        return entries

    def _parse_time_string(self, time_str: str) -> int:
        """
        Parse various time string formats to seconds.

        Args:
            time_str: Time string (e.g., "5:30:00", "5.5h", "330m", "3h 50m")

        Returns:
            int: Time in seconds
        """
        try:
            # Time Doctor format: "3h 50m" or "15m" or "2h"
            hours = 0
            minutes = 0

            if "h" in time_str:
                h_match = re.search(r"(\d+)h", time_str)
                if h_match:
                    hours = int(h_match.group(1))

            if "m" in time_str:
                m_match = re.search(r"(\d+)m", time_str)
                if m_match:
                    minutes = int(m_match.group(1))

            if hours > 0 or minutes > 0:
                return hours * 3600 + minutes * 60

            # HH:MM:SS format
            match = re.search(r"(\d+):(\d+):(\d+)", time_str)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                secs = int(match.group(3))
                return hours * 3600 + minutes * 60 + secs

            # HH:MM format
            match = re.search(r"(\d+):(\d+)", time_str)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return hours * 3600 + minutes * 60

            # Decimal hours (5.5h) - but no space
            match = re.search(r"(\d+\.?\d*)h", time_str.lower())
            if match and " " not in time_str:  # Avoid matching "3h 50m"
                hours = float(match.group(1))
                return int(hours * 3600)

            # Just minutes (330m)
            match = re.search(r"^(\d+)m$", time_str.lower())
            if match:
                minutes = int(match.group(1))
                return minutes * 60

            # Seconds (18000s)
            match = re.search(r"(\d+)s", time_str.lower())
            if match:
                return int(match.group(1))

        except Exception as e:
            logger.warning(f"Error parsing time string '{time_str}': {e}")

        return 0

    def aggregate_by_task(self, entries: list[dict]) -> list[dict]:
        """
        Aggregate multiple entries for the same task.

        Args:
            entries: List of time entries

        Returns:
            List[Dict]: Aggregated entries
        """
        task_map = {}

        for entry in entries:
            key = (entry["date"], entry["project"], entry["task"])

            if key in task_map:
                task_map[key]["seconds"] += entry["seconds"]
            else:
                task_map[key] = entry.copy()

        aggregated = list(task_map.values())
        logger.info(f"Aggregated {len(entries)} entries to {len(aggregated)} unique tasks")

        return aggregated


# Example usage
if __name__ == "__main__":
    # Sample HTML for testing
    sample_html = """
    <table class="report-table">
        <tr>
            <th>Project</th>
            <th>Task</th>
            <th>Description</th>
            <th>Time</th>
        </tr>
        <tr>
            <td>AYR</td>
            <td>ABMS-202</td>
            <td>Calendar Sync</td>
            <td>5:00:00</td>
        </tr>
        <tr>
            <td>AYR</td>
            <td>ABMS-3144</td>
            <td>Outlook Calendar Sync - Integration</td>
            <td>1:00:00</td>
        </tr>
    </table>
    """

    parser = TimeDocorParser()
    entries = parser.parse_daily_report(sample_html, "2025-01-15")

    for entry in entries:
        print(f"{entry['project']}/{entry['task']}: {entry['seconds']} seconds")
