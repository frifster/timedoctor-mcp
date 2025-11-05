"""
Time Doctor MCP Server
Provides MCP tools for Time Doctor time tracking integration
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

# Handle both package import and direct execution
try:
    from .parser import TimeDocorParser
    from .scraper import TimeDocorScraper
    from .transformer import (
        TimeDocorTransformer,
        entries_to_csv_string,
        entries_to_json_string,
        get_hours_summary,
    )
except ImportError:
    # Fallback for direct execution
    from parser import TimeDocorParser
    from scraper import TimeDocorScraper
    from transformer import (
        TimeDocorTransformer,
        entries_to_csv_string,
        entries_to_json_string,
        get_hours_summary,
    )

# Configure logging
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
log_file = os.path.join(project_dir, "timedoctor_mcp.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr),  # Use stderr for MCP
    ],
)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("timedoctor-scraper")

# Global instances
scraper = None
parser = TimeDocorParser()
transformer = TimeDocorTransformer()


async def get_scraper() -> TimeDocorScraper:
    """Get or create scraper instance."""
    global scraper
    if scraper is None:
        scraper = TimeDocorScraper()
    return scraper


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_daily_report",
            description="Get time tracking report for a specific date from Time Doctor",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (e.g., 2025-01-15). Use 'today' for current date.",
                    }
                },
                "required": ["date"],
            },
        ),
        Tool(
            name="export_weekly_csv",
            description="Get time tracking data for ANY date range in CSV or JSON format. Works with any number of days (1 day, 7 days, 30 days, etc). Returns data as text that you can save or analyze. Supports parallel scraping for faster retrieval of recent dates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (e.g., 2025-01-15). Can be any date.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (e.g., 2025-01-21). Can be any date, any range length.",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["csv", "json"],
                        "description": "Output format: 'csv' for CSV format (default) or 'json' for JSON format with summary",
                        "default": "csv",
                    },
                    "parallel": {
                        "type": "string",
                        "enum": ["auto", "true", "false"],
                        "description": "Use parallel scraping: 'auto' (default, chooses based on date age), 'true' (force parallel), 'false' (force sequential). Parallel is 2x faster for recent dates.",
                        "default": "auto",
                    },
                    "min_hours": {
                        "type": "number",
                        "description": "Filter out entries with hours less than this value (excludes entries < 6 minutes by default). Set to 0 to disable filter.",
                        "default": 0.1,
                        "minimum": 0,
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Tool(
            name="get_hours_summary",
            description="Get a quick breakdown of hours by project for a specific date",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (e.g., 2025-01-15). Use 'today' for current date.",
                    }
                },
                "required": ["date"],
            },
        ),
        Tool(
            name="export_today_csv",
            description="Get today's time tracking data in CSV format. Returns CSV data as text.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


def normalize_date(date_str: str) -> str:
    """
    Normalize date string to YYYY-MM-DD format.

    Args:
        date_str: Date string (supports 'today', 'yesterday', or YYYY-MM-DD)

    Returns:
        str: Normalized date in YYYY-MM-DD format
    """
    if date_str.lower() == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_str.lower() == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # Validate format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError as e:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.") from e


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "get_daily_report":
            return await handle_get_daily_report(arguments)

        elif name == "export_weekly_csv":
            return await handle_export_weekly_csv(arguments)

        elif name == "get_hours_summary":
            return await handle_get_hours_summary(arguments)

        elif name == "export_today_csv":
            return await handle_export_today_csv(arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_get_daily_report(arguments: dict) -> list[TextContent]:
    """Handle get_daily_report tool call."""
    try:
        # Normalize date
        date = normalize_date(arguments["date"])

        logger.info(f"Getting daily report for {date}")

        # Get scraper instance
        td_scraper = await get_scraper()

        # Start browser and login
        await td_scraper.start_browser()
        login_success = await td_scraper.login()

        if not login_success:
            raise Exception("Failed to login to Time Doctor")

        # Get report HTML
        html = await td_scraper.get_daily_report_html(date)

        # Parse HTML
        entries = parser.parse_daily_report(html, date)

        # Aggregate by task
        entries = parser.aggregate_by_task(entries)

        # Transform to CSV format
        transformed = transformer.transform_entries(entries)

        # Close browser
        await td_scraper.close_browser()

        # Format response
        if not transformed:
            response = f"No time tracking entries found for {date}"
        else:
            total_hours = transformer.calculate_total(transformed)
            response = f"Daily Report for {date}\n"
            response += "=" * 60 + "\n\n"

            for entry in transformed:
                response += f"Date: {entry['Date']}\n"
                response += f"Project: {entry['Project']}\n"
                response += f"Task: {entry['Task']}\n"
                response += f"Description: {entry['Description']}\n"
                response += f"Hours: {entry['WORK HOUR']:.2f}\n"
                response += "-" * 60 + "\n"

            response += f"\nTOTAL HOURS: {total_hours:.2f}"

        logger.info(f"Successfully retrieved daily report for {date}")
        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error in get_daily_report: {e}")
        # Ensure browser is closed
        if td_scraper:
            try:
                await td_scraper.close_browser()
            except Exception:
                pass
        raise


async def handle_export_weekly_csv(arguments: dict) -> list[TextContent]:
    """Handle export_weekly_csv tool call - returns CSV or JSON data as text."""
    import time

    start_time = time.time()

    try:
        # Normalize dates
        start_date = normalize_date(arguments["start_date"])
        end_date = normalize_date(arguments["end_date"])
        output_format = arguments.get("format", "csv").lower()
        parallel_mode = arguments.get("parallel", "auto").lower()
        min_hours = float(arguments.get("min_hours", 0.1))

        # Get scraper instance
        td_scraper = await get_scraper()

        # Determine whether to use parallel scraping
        use_parallel = False
        method_name = "sequential"

        if parallel_mode == "true":
            use_parallel = True
            method_name = "parallel (forced)"
        elif parallel_mode == "false":
            use_parallel = False
            method_name = "sequential (forced)"
        else:  # auto
            # Auto-detect: use parallel if dates are recent (< 7 days old)
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            today = datetime.now()

            days_old = (today - end_dt).days

            if days_old <= 7:
                use_parallel = True
                method_name = "parallel (auto: recent dates)"
            else:
                use_parallel = False
                method_name = "sequential (auto: old dates)"

        logger.info(
            f"Getting date range report from {start_date} to {end_date} in {output_format.upper()} format using {method_name}"
        )

        # Scrape based on chosen method
        if use_parallel:
            # Parallel scraping - faster for recent dates
            await td_scraper.start_browser()
            all_reports = await td_scraper.get_date_range_reports_parallel(start_date, end_date)
            await td_scraper.close_browser()
        else:
            # Sequential scraping - use single-session method
            all_reports = await td_scraper.get_date_range_data_single_session(
                start_date, end_date
            )

        # Parse all HTMLs
        all_entries = []
        for report in all_reports:
            date_str = report["date"]
            html = report["html"]

            logger.info(f"Parsing data for {date_str}")
            entries = parser.parse_daily_report(html, date_str)
            all_entries.extend(entries)

        # Aggregate by task
        all_entries = parser.aggregate_by_task(all_entries)

        # Apply min_hours filter if specified
        entries_before_filter = len(all_entries)
        if min_hours > 0:
            all_entries = [e for e in all_entries if (e["seconds"] / 3600) >= min_hours]
            logger.info(
                f"Filtered {entries_before_filter - len(all_entries)} entries below {min_hours}h threshold"
            )

        # Calculate stats
        transformed = transformer.transform_entries(all_entries)
        total_hours = transformer.calculate_total(transformed)
        summary = transformer.get_hours_summary(transformed)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Generate output based on format
        if output_format == "json":
            # JSON format - cleaner output with execution time
            import json as json_lib

            json_data = entries_to_json_string(all_entries, include_total=True, indent=2)
            # Parse, add execution time, re-serialize
            json_obj = json_lib.loads(json_data)
            json_obj["execution_time_seconds"] = round(execution_time, 2)
            json_obj["scraping_method"] = method_name
            if min_hours > 0:
                json_obj["min_hours_filter"] = min_hours
                json_obj["entries_filtered"] = entries_before_filter - len(all_entries)
            json_data = json_lib.dumps(json_obj, indent=2, ensure_ascii=False)

            response = f"Time Doctor Report: {start_date} to {end_date} (JSON)\n"
            response += "=" * 60 + "\n\n"
            response += json_data

        else:
            # CSV format (default) - with summary header
            csv_data = entries_to_csv_string(all_entries, include_total=True)

            response = f"Time Doctor Report: {start_date} to {end_date}\n"
            response += "=" * 60 + "\n\n"
            response += f"Scraping method: {method_name}\n"
            response += f"Execution time: {execution_time:.2f}s\n"
            response += f"Days Retrieved: {len(all_reports)}\n"
            response += f"Total Entries: {len(all_entries)}\n"
            if min_hours > 0:
                response += f"Min hours filter: {min_hours}h (filtered out {entries_before_filter - len(all_entries)} entries)\n"
            response += f"Total Hours: {total_hours:.2f}\n\n"

            # Add summary by project
            response += "Hours by Project:\n"
            for project, hours in sorted(summary.items()):
                response += f"  {project}: {hours:.2f} hours\n"

            response += "\n" + "=" * 60 + "\n\n"
            response += "CSV Data:\n\n"
            response += csv_data

        logger.info(
            f"Successfully generated {output_format.upper()} date range report ({len(all_entries)} entries)"
        )
        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error in export_weekly_csv: {e}")
        raise


async def handle_get_hours_summary(arguments: dict) -> list[TextContent]:
    """Handle get_hours_summary tool call."""
    try:
        # Normalize date
        date = normalize_date(arguments["date"])

        logger.info(f"Getting hours summary for {date}")

        # Get scraper instance
        td_scraper = await get_scraper()

        # Start browser and login
        await td_scraper.start_browser()
        login_success = await td_scraper.login()

        if not login_success:
            raise Exception("Failed to login to Time Doctor")

        # Get report HTML
        html = await td_scraper.get_daily_report_html(date)

        # Parse HTML
        entries = parser.parse_daily_report(html, date)

        # Aggregate by task
        entries = parser.aggregate_by_task(entries)

        # Close browser
        await td_scraper.close_browser()

        # Get summary
        summary = get_hours_summary(entries)

        # Format response
        if not summary:
            response = f"No time tracking data found for {date}"
        else:
            response = transformer.format_summary_text(summary)
            response = f"Hours Summary for {date}\n" + "=" * 60 + "\n\n" + response

        logger.info(f"Successfully generated hours summary for {date}")
        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error in get_hours_summary: {e}")
        # Ensure browser is closed
        if td_scraper:
            try:
                await td_scraper.close_browser()
            except Exception:
                pass
        raise


async def handle_export_today_csv(arguments: dict) -> list[TextContent]:
    """Handle export_today_csv tool call - returns CSV data as text."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Getting today's report ({today})")

        # Get scraper instance
        td_scraper = await get_scraper()

        # Start browser and login
        await td_scraper.start_browser()
        login_success = await td_scraper.login()

        if not login_success:
            raise Exception("Failed to login to Time Doctor")

        # Get report HTML
        html = await td_scraper.get_daily_report_html(today)

        # Parse HTML
        entries = parser.parse_daily_report(html, today)

        # Aggregate by task
        entries = parser.aggregate_by_task(entries)

        # Close browser
        await td_scraper.close_browser()

        # Generate CSV string
        csv_data = entries_to_csv_string(entries, include_total=True)

        # Calculate stats
        transformed = transformer.transform_entries(entries)
        total_hours = transformer.calculate_total(transformed)

        response = f"Time Doctor Report: Today ({today})\n"
        response += "=" * 60 + "\n\n"
        response += f"Total Entries: {len(entries)}\n"
        response += f"Total Hours: {total_hours:.2f}\n\n"

        # Add summary by project
        if transformed:
            summary = transformer.get_hours_summary(transformed)
            response += "Hours by Project:\n"
            for project, hours in sorted(summary.items()):
                response += f"  {project}: {hours:.2f} hours\n"

        response += "\n" + "=" * 60 + "\n\n"
        response += "CSV Data:\n\n"
        response += csv_data

        logger.info(f"Successfully generated today's report ({len(entries)} entries)")
        return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Error in export_today_csv: {e}")
        # Ensure browser is closed
        if td_scraper:
            try:
                await td_scraper.close_browser()
            except Exception:
                pass
        raise


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Time Doctor MCP Server")

    try:
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


def run():
    """Entry point for console script (uvx timedoctor-mcp)."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
