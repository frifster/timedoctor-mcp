# Changelog

All notable changes to Time Doctor MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.3] - 2025-11-05

### Changed
- **Reduced Maximum Limit from 15 to 7 Days**: Date range requests now limited to maximum 7 days per request
  - Prevents Claude Desktop timeout issues (60-second tool execution limit)
  - Testing showed 15-day requests timing out after 35 seconds
  - 7-day limit ensures reliable completion within Claude Desktop constraints
  - Example: 30-day request now suggests 5 × 7-day requests instead of 2 × 15-day requests
  - AI agents will naturally split larger requests into weekly chunks

### Benefits
- **Reliable with Claude Desktop**: All requests complete within 60-second timeout
- **Better UX**: No more timeout errors for large date ranges
- **Agent-Friendly**: Weekly chunks are intuitive and reliable

### Example Error Message
```
Date range too large: 30 days (max 7 days allowed).

To get 30 days of data, please split into multiple requests:
  1. 2025-10-01 to 2025-10-07 (7 days)
  2. 2025-10-08 to 2025-10-14 (7 days)
  3. 2025-10-15 to 2025-10-21 (7 days)
  4. 2025-10-22 to 2025-10-28 (7 days)
  5. 2025-10-29 to 2025-10-30 (2 days)
```

## [1.2.2] - 2025-11-05

**Note**: This version introduced a 15-day limit, but was superseded by v1.2.3 which reduced the limit to 7 days for better Claude Desktop compatibility.

### Added
- **15-Day Maximum Limit**: Date range requests now limited to maximum 15 days per request
  - Prevents overly long scraping sessions that can timeout or fail
  - Provides helpful error message with suggested date splits
  - Example: 30-day request automatically suggests 2 × 15-day requests
  - AI agents will naturally split larger requests into multiple calls

### Benefits
- **More Reliable**: Shorter scraping sessions are less likely to timeout
- **Better UX**: Clear guidance when range is too large
- **Agent-Friendly**: Forces AI agents to make multiple parallel requests for large ranges

### Example Error Message
```
Date range too large: 31 days (max 15 days allowed).

To get 31 days of data, please split into multiple requests:
  1. 2025-10-01 to 2025-10-15 (15 days)
  2. 2025-10-16 to 2025-10-30 (15 days)
  3. 2025-10-31 to 2025-10-31 (1 day)
```

## [1.2.1] - 2025-11-05

### Fixed
- **Playwright Browser Installation**: Added clear error message when browser binaries are missing
  - Detects "Executable doesn't exist" error and shows installation command
  - Helpful message directs users to run: `uvx --with playwright playwright install chromium`
  - Prevents confusing errors for first-time uvx users

### Documentation
- **README Improvements**: Enhanced Playwright browser installation instructions
  - Clarified one-time setup requirement (~130MB download)
  - Added dedicated troubleshooting section for Playwright browser errors
  - Added explicit step in Prerequisites section with clear commands

## [1.2.0] - 2025-11-05

### Added

#### MCP Server Enhancements
- **min_hours Filter**: New parameter to filter out entries below a minimum hours threshold
  - Default: 0.1 hours (6 minutes) - excludes very short entries
  - Set to 0 to disable filtering
  - Shows filtered entry count in output
  - Example: `min_hours: 1.0` keeps only entries >= 1 hour

- **Execution Time Tracking**: Reports now include scraping execution time
  - CSV format: Shows "Execution time: X.XXs" in header
  - JSON format: Includes `execution_time_seconds` field
  - Helps identify performance for different date ranges

- **Total Seconds Field**: JSON output now includes total tracked seconds
  - New field: `total_seconds` - sum of all entry seconds
  - Complements `total_hours` for precise time calculations
  - Example: 30000 seconds = 500 minutes = 8.33 hours

- **Parallel Scraping Integration**: MCP server now supports parallel scraping
  - New `parallel` parameter: "auto" (default), "true", "false"
  - **Auto-detection**: Uses parallel for recent dates (< 7 days), sequential for older
  - Shows scraping method used in output
  - Force parallel/sequential via parameter override

#### Parallel Scraping (Core Implementation)
- **Parallel Browser Contexts**: New `get_date_range_reports_parallel()` method
  - Scrapes multiple dates simultaneously using separate browser contexts
  - **2x faster for recent dates** (< 7 days old): 54s → 27s for 5 dates
  - Best for non-consecutive dates or when cache is cold
  - Configurable via `MAX_PARALLEL_SESSIONS` (default: 5)
  - New constants: `MAX_PARALLEL_SESSIONS`, `PARALLEL_THRESHOLD`
- **Smart Context Management**: Uses asyncio semaphore to limit concurrent sessions
- **Helper Methods**:
  - `_scrape_single_date_in_context()`: Scrape one date in isolated context
  - `_navigate_page_to_date()`: Navigate any page to target date (not just self.page)

#### When to Use Parallel vs Sequential

**Use Parallel (`get_date_range_reports_parallel()`)**:
- Recent dates (< 7 days ago): 2x faster
- Non-consecutive dates (e.g., every Monday): each date independent
- Cold cache with multiple dates needed

**Use Sequential (`get_date_range_reports()`)**:
- Consecutive dates far in the past: incremental navigation more efficient
- Dates 30+ days old: navigation overhead negates parallel benefits
- Example: Oct 10-14 when today is Nov 5 → similar or slower in parallel

#### Performance Metrics
- Recent dates (5 days ago): Sequential 54.5s, Parallel 27.7s → **2.0x speedup**
- Old dates (26 days ago): Sequential 71.3s, Parallel 70.3s → **no benefit**
- Parallel overhead: Each session does full navigation from today to target date

### Changed
- **Version**: Bumped from 1.1.0 to 1.2.0
- **Import**: Added `asyncio` import for parallel task management

## [1.1.0] - 2025-11-05

### Fixed
- **Load State Detection**: Changed from `networkidle` to `domcontentloaded` for most page wait operations
  - Time Doctor pages have continuous background network activity that prevents networkidle state
  - `domcontentloaded` is more appropriate for modern web apps with analytics/tracking
  - Fixes timeout errors during login and navigation
  - Login now completes in ~4 seconds instead of timing out

- **Date Navigation Reliability**: Fixed date navigation after load state changes
  - Added 2-second wait after loading report page to ensure date navigation buttons render
  - Kept original `wait_for_timeout(1500)` for date arrow clicks (Angular needs time to re-render)
  - Navigation now successfully reaches historical dates (e.g., Oct 10, 2025 from Nov 5)
  - Fixes "Could not find date display button" warnings

### Added

#### Performance Improvements
- **Smart Wait Detection**: Replaced fixed `wait_for_timeout()` calls with intelligent `wait_for_load_state()` detection
  - 30-40% faster page navigation
  - More reliable operation by detecting actual page state instead of arbitrary delays
  - Reduced total execution time for date range operations

- **File-Based Caching System** (`src/cache.py`)
  - Caches daily reports with 5-minute TTL (configurable)
  - Instant responses for recently requested dates
  - Automatic cache expiration and cleanup
  - Cache statistics tracking
  - Control via `USE_CACHE` environment variable (default: enabled)
  - Cache stored in `.cache/` directory

#### Reliability Improvements
- **Retry Logic with Exponential Backoff**
  - Automatic retry on transient failures using `tenacity` library
  - Applied to critical operations: `start_browser()`, `login()`, `get_daily_report_html()`
  - Configurable retry attempts (default: 3) and wait times
  - Exponential backoff with multiplier: 2x (1s → 2s → 4s)
  - Significantly improved resilience against network issues

#### Code Quality Improvements
- **Constants Module** (`src/constants.py`)
  - Centralized configuration for all timeouts and delays
  - Makes performance tuning easier
  - Improves code maintainability
  - All magic numbers extracted to named constants
  - Grouped by category: Browser Config, Timeouts, Cache, Retry

#### New Features
- **JSON Output Format Support**
  - New `format` parameter in `export_weekly_csv` tool
  - Supports both `"csv"` (default) and `"json"` formats
  - JSON output includes:
    - Structured entries with metadata
    - Total hours calculation
    - Summary by project
    - Entry count
  - Better for programmatic consumption and API integration

### Changed
- **Version**: Bumped from 1.0.1 to 1.1.0
- **Dependencies**: Added `tenacity>=8.2.0` for retry logic
- **Tool Description**: Updated `export_weekly_csv` to mention JSON format support

### Performance Metrics
- **Navigation Speed**: 30-40% faster due to smart detection
- **Repeat Requests**: Nearly instant (0ms) for cached data within TTL
- **Network Reliability**: 3x retry attempts with exponential backoff
- **Date Range Operations**: Faster overall due to cumulative improvements

### Technical Details

#### New Files
- `src/constants.py` - Configuration constants
- `src/cache.py` - Caching system implementation

#### Modified Files
- `src/scraper.py` - Retry decorators, smart waits, cache integration
- `src/transformer.py` - Added `entries_to_json_string()` function
- `src/mcp_server.py` - Added format parameter to export tool
- `pyproject.toml` - Added tenacity dependency, version bump
- `requirements.txt` - Added tenacity==8.2.3

#### Environment Variables
- `USE_CACHE` - Enable/disable caching (default: "true")
- `BROWSER_TIMEOUT` - Browser default timeout (default: 30000ms)
- `LOG_LEVEL` - Logging level (default: "INFO")

### Example Usage

#### JSON Format
```
Get my Time Doctor data from last week in JSON format
```

The MCP tool will use:
```json
{
  "start_date": "2025-10-29",
  "end_date": "2025-11-04",
  "format": "json"
}
```

#### Cache Control
To disable cache:
```env
USE_CACHE=false
```

### Breaking Changes
None - All changes are backwards compatible.

## [1.0.1] - 2025-11-04

### Added
- PyPI publication support
- uvx installation method
- Automated publishing workflow

### Changed
- Updated README with uvx instructions

## [1.0.0] - 2025-11-03

### Added
- Initial release
- Time Doctor web scraping via Playwright
- MCP server with 4 tools
- Single-session date range fetching
- CSV output format
- Project and task aggregation
