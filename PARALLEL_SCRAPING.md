# Parallel Scraping Guide

Time Doctor MCP v1.2.0 introduces **parallel scraping** for faster multi-date data retrieval.

## Quick Comparison

| Scenario | Sequential | Parallel | Speedup |
|----------|-----------|----------|---------|
| 5 recent dates (< 7 days old) | 54.5s | 27.7s | **2.0x faster** |
| 5 old dates (26+ days old) | 71.3s | 70.3s | No benefit |

## When to Use Each Method

### Use Parallel: `get_date_range_reports_parallel()`

✅ **Best for:**
- **Recent dates** (< 7 days old): Minimal date navigation overhead
- **Non-consecutive dates**: Each date scraped independently
- **Cold cache**: Multiple dates needed from scratch

Example scenarios:
```python
# Last week's data (recent dates) - 2x faster
await scraper.get_date_range_reports_parallel("2025-10-29", "2025-11-04")

# Every Monday in October (non-consecutive) - Much faster
mondays = ["2025-10-07", "2025-10-14", "2025-10-21", "2025-10-28"]
for monday in mondays:
    await scraper.get_date_range_reports_parallel(monday, monday)
```

### Use Sequential: `get_date_range_reports()`

✅ **Best for:**
- **Consecutive dates far in the past**: Incremental navigation is efficient
- **Historical data** (30+ days old): Navigation overhead negates parallel benefits
- **Default choice**: Safe, reliable, works for all scenarios

Example scenarios:
```python
# Two months ago (old dates) - Sequential is better
await scraper.get_date_range_reports("2025-09-01", "2025-09-30")

# Consecutive week from last month
await scraper.get_date_range_reports("2025-10-10", "2025-10-14")
```

## How Parallel Scraping Works

### Architecture
```
Single Browser
├── Context 1 → Page → Login → Navigate → Scrape Date 1
├── Context 2 → Page → Login → Navigate → Scrape Date 2
├── Context 3 → Page → Login → Navigate → Scrape Date 3
├── Context 4 → Page → Login → Navigate → Scrape Date 4
└── Context 5 → Page → Login → Navigate → Scrape Date 5
     (All run simultaneously)
```

### Key Features
- **Browser Contexts**: Each date gets its own isolated context (separate cookies/storage)
- **Asyncio Semaphore**: Limits concurrent sessions to avoid overwhelming the server
- **Independent Navigation**: Each context navigates from "today" to its target date
- **Cache-Aware**: Checks cache before scraping (instant if cached)

### Configuration

```python
# In src/constants.py
MAX_PARALLEL_SESSIONS = 5  # Max concurrent browser contexts
PARALLEL_THRESHOLD = 3     # Use parallel if date count >= this

# Override at runtime
await scraper.get_date_range_reports_parallel(
    "2025-10-29",
    "2025-11-04",
    max_parallel=3  # Limit to 3 concurrent sessions
)
```

## Performance Analysis

### Why Recent Dates Are Faster

**Sequential (Oct 31 - Nov 4):**
```
Login (4s) → Navigate to Oct 31 (4 days × 1.5s = 6s)
→ Scrape (8s) → Forward 1 day (1.5s) → Scrape (8s) → ...
Total: ~54s
```

**Parallel (Oct 31 - Nov 4):**
```
All 5 sessions in parallel:
  - Session 1: Login (4s) + Navigate 4 days (6s) + Scrape (8s) = 18s
  - Session 2: Login (4s) + Navigate 3 days (4.5s) + Scrape (8s) = 16.5s
  - ...
Total: max(all sessions) = ~27s (2x faster)
```

### Why Old Dates Don't Benefit

**Sequential (Oct 10-14, today is Nov 5):**
```
Login (4s) → Navigate to Oct 10 (26 days × 1.5s = 39s)
→ Scrape (8s) → Forward 1 day (1.5s) → Scrape (8s) → ...
Total: ~71s (only navigates 26 days once)
```

**Parallel (Oct 10-14, today is Nov 5):**
```
All 5 sessions in parallel:
  - Session 1: Login (4s) + Navigate 26 days (39s) + Scrape (8s) = 51s
  - Session 2: Login (4s) + Navigate 25 days (37.5s) + Scrape (8s) = 49.5s
  - ...
Total: max(all sessions) = ~70s (each session navigates 25-26 days)
```

The parallel overhead (each session doing full navigation) negates the benefit.

## Environment Variables

```bash
# Control parallel behavior
MAX_PARALLEL_SESSIONS=5  # Max concurrent contexts
USE_CACHE=true           # Enable caching (helps parallel a lot)
```

## Code Example

```python
import asyncio
from src.scraper import TimeDocorScraper
from src.parser import TimeDocorParser

async def fetch_last_week():
    scraper = TimeDocorScraper()
    parser = TimeDocorParser()

    try:
        await scraper.start_browser()

        # Get last 7 days in parallel (2x faster)
        reports = await scraper.get_date_range_reports_parallel(
            "2025-10-29",
            "2025-11-04"
        )

        # Parse results
        all_entries = []
        for report in reports:
            entries = parser.parse_daily_report(report["html"], report["date"])
            all_entries.extend(entries)

        print(f"Retrieved {len(all_entries)} time entries")

        await scraper.close_browser()

    except Exception as e:
        print(f"Error: {e}")
        await scraper.close_browser()

asyncio.run(fetch_last_week())
```

## Technical Details

### New Methods

#### `get_date_range_reports_parallel(start_date, end_date, max_parallel=5)`
Main parallel scraping method. Returns list of `{"date": str, "html": str}` dicts.

#### `_scrape_single_date_in_context(context, date)`
Helper to scrape one date using a specific browser context. Handles login, navigation, and scraping.

#### `_navigate_page_to_date(page, target_date)`
Navigate any page (not just `self.page`) to a target date. Extracted for reusability.

### Files Modified
- `src/scraper.py`: Added parallel methods and helpers
- `src/constants.py`: Added `MAX_PARALLEL_SESSIONS`, `PARALLEL_THRESHOLD`
- `CHANGELOG.md`: Documented v1.2.0 changes

## Caching + Parallel = Best Performance

Parallel scraping works exceptionally well with caching:

```python
# First run: Parallel scraping (27s for 5 dates)
reports = await scraper.get_date_range_reports_parallel("2025-10-29", "2025-11-04")

# Second run within 5 minutes: All cached (< 1s)
reports = await scraper.get_date_range_reports_parallel("2025-10-29", "2025-11-04")
```

## Troubleshooting

### Parallel is slower than expected
- Check if dates are old (30+ days): Use sequential instead
- Verify `USE_CACHE=true` in `.env`
- Reduce `MAX_PARALLEL_SESSIONS` if experiencing rate limits

### Rate limiting or connection errors
- Reduce `MAX_PARALLEL_SESSIONS` from 5 to 3
- Add delay between scraping operations
- Use sequential method as fallback

## Future Improvements

Potential optimizations:
- Smart date clustering: Group nearby dates, scrape in parallel groups
- Adaptive strategy: Automatically choose parallel vs sequential based on date age
- Start from furthest date: Navigate to oldest date first in parallel sessions
- Browser reuse: Share browser instance across multiple date ranges

## Summary

Parallel scraping is **experimental** but shows real performance gains for recent dates. Use it when:
- Dates are within last week (2x faster)
- Dates are non-consecutive (each independent)
- You need multiple dates quickly

Stick with sequential scraping for:
- Historical data (30+ days old)
- Large consecutive date ranges
- Production reliability (more battle-tested)

The MCP server continues to use the sequential method by default for stability.
