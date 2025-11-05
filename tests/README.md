# Tests Directory

This directory contains all test files and debugging artifacts for the Time Doctor MCP project.

## Directory Structure

```
tests/
├── integration/          # Integration and performance tests
│   ├── test_parallel.py              # Sequential vs parallel comparison
│   ├── test_parallel_recent.py       # Recent dates parallel test
│   ├── test_mcp_parallel.py          # MCP server parallel integration
│   ├── test_new_features.py          # min_hours and execution_time tests
│   ├── test_total_seconds.py         # total_seconds field test
│   ├── test_complete_flow.py         # End-to-end flow test
│   ├── test_date_navigation.py       # Date navigation test
│   ├── test_projects_tasks.py        # Projects & Tasks report test
│   ├── test_parser.py                # HTML parser test
│   ├── test_login_debug.py           # Login debugging test
│   ├── debug_login.py                # Login debug helper
│   ├── quick_test.py                 # Quick smoke test
│   └── test_complete_flow_output.csv # Sample CSV output
│
└── screenshots/         # Debug screenshots from test runs
    ├── after_expand.png              # After clicking "Expand All"
    ├── before_expand.png             # Before clicking "Expand All"
    ├── debug_login_failed.png        # Login failure screenshot
    ├── debug_screenshot.png          # General debug screenshot
    ├── expanded_view.png             # Expanded task view
    ├── projects_report.png           # Projects report page
    ├── projects_tasks_final.png      # Final projects & tasks view
    ├── projects_tasks_page.png       # Projects & tasks page
    └── reports_page.png              # Reports overview page
```

## Test Categories

### Performance Tests
Test parallel vs sequential scraping performance:

```bash
# Compare sequential vs parallel for old dates (26 days ago)
python tests/integration/test_parallel.py

# Test parallel performance with recent dates (< 7 days)
python tests/integration/test_parallel_recent.py
```

**Expected Results**:
- Recent dates: Parallel ~2x faster (54s → 27s)
- Old dates: Similar performance (70s vs 71s)

### MCP Integration Tests
Test MCP server features:

```bash
# Test MCP server parallel integration and auto-detection
python tests/integration/test_mcp_parallel.py

# Test min_hours filter and execution_time tracking
python tests/integration/test_new_features.py

# Test total_seconds field in JSON output
python tests/integration/test_total_seconds.py
```

**Expected Results**:
- Auto-detection: Uses parallel for recent dates, sequential for old
- min_hours filter: Correctly filters entries below threshold
- Execution time: Reported in seconds
- total_seconds: Sum of all entry seconds

### End-to-End Tests
Test complete scraping flows:

```bash
# Test complete login → navigate → scrape → parse flow
python tests/integration/test_complete_flow.py

# Test date navigation (arrow clicks)
python tests/integration/test_date_navigation.py

# Test Projects & Tasks report scraping
python tests/integration/test_projects_tasks.py
```

### Component Tests
Test individual components:

```bash
# Test HTML parser
python tests/integration/test_parser.py

# Test login flow
python tests/integration/test_login_debug.py
```

## Running All Tests

```bash
# Run from project root
source .venv/bin/activate

# Run specific test
python tests/integration/test_parallel.py

# Run all integration tests (if using pytest)
pytest tests/integration/
```

## Test Data

### Dates Used in Tests
- **Recent dates**: Last 5-7 days (for parallel testing)
- **Historical dates**: Oct 10-14, 2025 (for sequential testing)
- **Test data**: Real Time Doctor account data

### Expected Data
- Oct 10, 2025: ~9 hours, 3 entries
- Oct 11, 2025: ~6 hours, 1 entry
- Oct 12, 2025: ~11 hours, 6 entries
- Oct 13, 2025: ~14 hours, 7 entries
- Oct 14, 2025: ~12 hours, 8 entries

## Screenshots

Screenshots are captured during test runs for debugging purposes. They show:

1. **Login flow**: Login page states
2. **Navigation**: Before/after expanding tasks
3. **Report views**: Different report page states
4. **Debugging**: Error states and unexpected behaviors

## Environment Requirements

Tests require:
- Valid Time Doctor credentials in `.env`
- Playwright browser installed
- Python 3.8+
- Virtual environment activated

```bash
# Setup
cp .env.example .env  # Add your credentials
source .venv/bin/activate
playwright install chromium
```

## Notes

- Tests use real Time Doctor data (not mocked)
- Some tests may take 1-2 minutes to run (browser automation)
- Cache may affect test results - clear `.cache/` for fresh runs
- Screenshots help debug browser automation issues
- Integration tests are safe to run multiple times

## Cleanup

To clean test artifacts:

```bash
# Remove cached data
rm -rf .cache/

# Remove test screenshots (keep for debugging)
# rm -rf tests/screenshots/*.png
```

## Contributing

When adding new tests:
1. Place in `tests/integration/`
2. Name with `test_` prefix
3. Include docstring explaining test purpose
4. Add to this README under appropriate category
5. Ensure tests are idempotent (can run multiple times)
