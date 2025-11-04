# Time Doctor MCP

**MCP Server** for extracting Time Doctor time tracking data via Claude AI.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=flat-square&logo=buy-me-a-coffee)](https://buymeacoffee.com/frifster)

## What It Does

Fetches time tracking reports from Time Doctor and returns them as CSV data. Integrates directly with Claude Desktop/Code as an MCP server.

**Features:**
- 🚀 Single-session scraping (login once, get multiple dates)
- 📅 Works with any date range (1 day to 365+ days)
- 📊 Returns CSV data as text (no file system issues)
- ⏱️ Parses Time Doctor's "3h 50m" format
- 📦 Aggregates duplicate tasks
- ✅ Includes TOTAL row

## Quick Setup

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/frifster/timedoctor-mcp.git
cd timedoctor-mcp

# Install UV (fastest method)
brew install uv

# Run setup
./setup-with-uv.sh
```

### 2. Configure Credentials

Create `.env` in the project root:
```bash
nano .env
```

Add your Time Doctor credentials:
```env
TD_EMAIL=your-email@example.com
TD_PASSWORD=your-password
TD_BASE_URL=https://2.timedoctor.com
HEADLESS=true
```

### 3. Add to Claude Desktop/Code

Edit your Claude MCP configuration:

**macOS:**
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

Add this configuration (replace `<PATH_TO_REPO>` with your actual path):

**Option A: Credentials in JSON**
```json
{
  "mcpServers": {
    "timedoctor": {
      "command": "<PATH_TO_REPO>/.venv/bin/python",
      "args": ["<PATH_TO_REPO>/src/mcp_server.py"],
      "env": {
        "TD_EMAIL": "your-email@example.com",
        "TD_PASSWORD": "your-password",
        "TD_BASE_URL": "https://2.timedoctor.com",
        "HEADLESS": "true"
      }
    }
  }
}
```

**Option B: Load from .env (Recommended)**
```json
{
  "mcpServers": {
    "timedoctor": {
      "command": "<PATH_TO_REPO>/.venv/bin/python",
      "args": ["<PATH_TO_REPO>/src/mcp_server.py"]
    }
  }
}
```

**Example paths:**
- macOS: `/Users/yourname/timedoctor-mcp/.venv/bin/python`
- Linux: `/home/yourname/timedoctor-mcp/.venv/bin/python`
- Windows: `C:\Users\yourname\timedoctor-mcp\.venv\Scripts\python.exe`

### 4. Restart Claude

Completely quit and reopen Claude Desktop/Code.

## Usage

**Get data for date range:**
```
Get my Time Doctor data from August 25 to September 5
```

**Today's data:**
```
Show me my Time Doctor hours for today
```

**Last week:**
```
Get my Time Doctor data for the last 7 days
```

**Custom analysis:**
```
Get my Time Doctor data from last month and tell me which project took the most time
```

Claude will receive CSV data like:
```csv
Date,Project,Task,Description,WORK HOUR
08/25/2025,Jira: AYR BMS,ABMS-606,Code Review,5.00
08/25/2025,Jira: AYR BMS,ABMS-700,Bug Fix,3.50
TOTAL,,,,8.50
```

You can then ask Claude to save it wherever you want!

## MCP Tools

### 1. `export_weekly_csv`
Get time tracking data for any date range in CSV format.

**Parameters:**
- `start_date` (required): YYYY-MM-DD format
- `end_date` (required): YYYY-MM-DD format

**Returns:** CSV data as text with summary statistics

### 2. `get_daily_report`
Get detailed report for a specific date.

**Parameters:**
- `date` (required): YYYY-MM-DD format or "today"

**Returns:** Formatted report with project breakdown

### 3. `get_hours_summary`
Quick hours breakdown by project.

**Parameters:**
- `date` (required): YYYY-MM-DD format or "today"

**Returns:** Summary by project

### 4. `export_today_csv`
Quick access to today's data.

**Parameters:** None

**Returns:** Today's CSV data with summary

## How It Works

1. **Login:** Playwright automation logs into Time Doctor web interface
2. **Navigate:** Goes to Projects & Tasks report
3. **Date Navigation:** Uses arrow buttons to change dates
4. **Extract:** Parses Angular Material tree structure for project/task data
5. **Parse:** Converts "3h 50m" format to decimal hours
6. **Aggregate:** Combines duplicate tasks
7. **Return:** CSV data as text in MCP response

## Architecture

**Single-Session Efficiency:**
- Login once
- Navigate through all dates in one session
- Extract data for each date
- Close browser once
- **Result:** 2-3x faster than logging in for each date

**CSV Data Format:**
```csv
Date,Project,Task,Description,WORK HOUR
11/04/2025,Jira: AYR BMS,ABMS-606,Code Review - ABMS-606,0.25
11/04/2025,Jira: AYR BMS,ABMS-4979,Deal template update,2.47
TOTAL,,,,2.72
```

- **Date:** MM/DD/YYYY format
- **WORK HOUR:** Decimal hours (5.00, 1.50, 0.25)
- **TOTAL:** Sum of all hours

## Project Structure

```
timedoctor-mcp/
├── .env                    # Your credentials (git-ignored)
├── .env.example            # Example configuration
├── requirements.txt        # Python dependencies
├── setup-with-uv.sh       # Setup script
└── src/
    ├── scraper.py         # Browser automation & login
    ├── parser.py          # HTML parsing (Angular Material tree)
    ├── transformer.py     # CSV formatting
    └── mcp_server.py      # MCP server with 4 tools
```

## Troubleshooting

### MCP Server Won't Start

Check the log:
```bash
tail -f timedoctor_mcp.log
```

Common issues:
- ❌ **Missing credentials:** Add to `.env` or MCP config
- ❌ **Wrong Python path:** Use `.venv/bin/python` (or `.venv/Scripts/python.exe` on Windows)
- ❌ **Dependencies not installed:** Run `./setup-with-uv.sh`

### Login Fails

**Check log for:**
```
Login failed - still on login page
```

**Solutions:**
- Verify credentials in `.env` are correct
- Check if Time Doctor requires 2FA (not supported)
- Try logging in manually at https://2.timedoctor.com/login
- Look for error messages in the log

**The scraper logs which email it's using:**
```
TimeDocorScraper initialized with email: your-email@example.com
```

### No Data Returned

**Check log for:**
```
Parsed 0 time entries
```

**Solutions:**
- Verify you have time tracking data for those dates
- Check that "Expand All" button appears on the report page
- Try with today's date first to confirm it works
- Check log for HTML parsing errors

### Claude Not Seeing Tools

**Solutions:**
1. Verify config path is correct
2. Check JSON syntax is valid (use a JSON validator)
3. Ensure Python path is absolute, not relative
4. Completely quit and restart Claude
5. Check Claude settings → MCP Servers

### Path Issues

Make sure all paths in your MCP config are **absolute paths**, not relative:

✅ **Good:**
- macOS/Linux: `/Users/name/timedoctor-mcp/.venv/bin/python`
- Windows: `C:\Users\name\timedoctor-mcp\.venv\Scripts\python.exe`

❌ **Bad:**
- `~/timedoctor-mcp/.venv/bin/python` (tilde not expanded)
- `./timedoctor-mcp/.venv/bin/python` (relative path)
- `timedoctor-mcp/.venv/bin/python` (relative path)

## Requirements

- **Python:** 3.12 or 3.13 (3.14 not supported yet)
- **Dependencies:** Playwright, BeautifulSoup4, MCP SDK, python-dotenv
- **System:** macOS, Linux, Windows
- **Time Doctor:** Active account with login credentials

## Performance

**Single-session architecture:**
- **7 days:** ~45 seconds (vs ~90 seconds with multiple logins)
- **30 days:** ~3 minutes
- **Login:** 5 seconds (once)
- **Per date:** 3-4 seconds (navigation + extraction)

## Security

- ✅ Credentials stored in `.env` (git-ignored)
- ✅ Headless browser (no GUI)
- ✅ Local execution only
- ✅ No data sent to third parties
- ⚠️ Store `.env` securely (`chmod 600 .env` recommended)

## Development

**Test login:**
```bash
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python debug_login.py
```

**Test parsing:**
```bash
python test_parser.py
```

**Test complete flow:**
```bash
python test_complete_flow.py
```

**View logs:**
```bash
tail -f timedoctor_mcp.log
```

## Why Web Scraping?

Time Doctor has an API, but this MCP server uses web automation because:
- ✅ No API token setup needed
- ✅ Same access as web interface
- ✅ Works with all Time Doctor plans
- ✅ More reliable for "Projects & Tasks" report

If you prefer API access, Time Doctor's API is available at: `https://api2.timedoctor.com/api/1.0/`

## Alternative Installation Methods

### Manual pip Installation

```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Using Python venv (without UV)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for personal use and automation of your own Time Doctor data. Ensure you comply with Time Doctor's Terms of Service and your organization's policies when using this scraper.

## Support

If this tool saves you time, consider buying me a coffee! ☕

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/frifster)

---

**Questions?** Check the log file: `timedoctor_mcp.log` in the project directory

**Working?** Ask Claude: "Get my Time Doctor data for today"
