# Contributing to Time Doctor MCP

Thank you for your interest in contributing to Time Doctor MCP! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and considerate in all interactions.

**Expected Behavior:**
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.12 or 3.13
- Git
- A Time Doctor account for testing
- GitHub account

### Fork the Repository

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/timedoctor-mcp.git
   cd timedoctor-mcp
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/frifster/timedoctor-mcp.git
   ```

## Development Setup

### 1. Install Dependencies

**Using UV (recommended):**
```bash
brew install uv  # macOS
# or download from https://github.com/astral-sh/uv

./setup-with-uv.sh
```

**Using pip:**
```bash
python3.13 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file in the project root:
```env
TD_EMAIL=your-test-email@example.com
TD_PASSWORD=your-test-password
TD_BASE_URL=https://2.timedoctor.com
HEADLESS=true
```

**Important:** Never commit your `.env` file!

### 3. Verify Setup

Run the test suite to ensure everything is working:
```bash
source .venv/bin/activate
python tests/test_parser.py
python tests/test_complete_flow.py
```

## Making Changes

### 1. Create a Branch

Always create a new branch for your changes:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Your Changes

- Write clear, concise commit messages
- Keep commits focused on a single change
- Add tests for new features
- Update documentation as needed

### 3. Keep Your Branch Updated

Regularly sync with the upstream repository:
```bash
git fetch upstream
git rebase upstream/main
```

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

### Running Linting

**Check for issues:**
```bash
source .venv/bin/activate
ruff check src/ tests/
```

**Auto-fix issues:**
```bash
ruff check --fix src/ tests/
```

**Format code:**
```bash
ruff format src/ tests/
```

### Style Guidelines

- **Python Version:** Target Python 3.12+
- **Line Length:** 100 characters maximum
- **Type Hints:** Use modern type hints (`dict`, `list`, not `Dict`, `List`)
- **Imports:** Organized automatically by ruff (stdlib → third-party → local)
- **Strings:** Use double quotes (`"` not `'`)
- **Docstrings:** Use Google-style docstrings

**Example:**
```python
async def get_daily_report(date: str) -> list[dict]:
    """
    Get time tracking report for a specific date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns:
        list[dict]: List of time entries
    """
    entries = []
    # Implementation
    return entries
```

### What Ruff Checks

- **E/W:** pycodestyle (errors/warnings)
- **F:** pyflakes
- **I:** isort (import sorting)
- **N:** pep8-naming
- **UP:** pyupgrade (modern Python syntax)
- **B:** flake8-bugbear
- **C4:** flake8-comprehensions
- **SIM:** flake8-simplify

## Testing

### Running Tests

**All tests:**
```bash
source .venv/bin/activate

# Parser tests
python tests/test_parser.py

# Date navigation tests
python tests/test_date_navigation.py

# End-to-end tests
python tests/test_complete_flow.py
```

**Debug login (visible browser):**
```bash
python tests/debug_login.py
```

### Writing Tests

When adding new features, include tests:

1. **Unit tests** for individual functions
2. **Integration tests** for component interactions
3. **End-to-end tests** for complete workflows

Place test files in the `tests/` directory.

**Example test structure:**
```python
import asyncio
from scraper import TimeDocorScraper

async def test_new_feature():
    """Test description."""
    scraper = TimeDocorScraper()
    # Test implementation
    assert result == expected

if __name__ == "__main__":
    asyncio.run(test_new_feature())
```

## Submitting Changes

### 1. Ensure Quality

Before submitting, ensure:
- [ ] All tests pass
- [ ] Code is linted and formatted (`ruff check` and `ruff format`)
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No sensitive data (credentials, API keys) is included

### 2. Push Your Changes

```bash
git push origin your-branch-name
```

### 3. Create a Pull Request

1. Go to the GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:
   - **Title:** Clear, concise description
   - **Description:** What changes were made and why
   - **Testing:** How you tested the changes
   - **Related Issues:** Link any related issues

**PR Title Examples:**
- `feat: Add support for weekly summary reports`
- `fix: Handle login timeout errors gracefully`
- `docs: Update installation instructions for Windows`
- `refactor: Simplify date parsing logic`

### 4. Code Review

- Respond to feedback promptly
- Make requested changes in new commits
- Push updates to your branch (PR updates automatically)
- Be open to suggestions and discussion

## Reporting Issues

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check the documentation** for known solutions
3. **Try the latest version** to see if it's already fixed

### Creating a Good Issue

Include the following information:

**For Bug Reports:**
- **Description:** Clear description of the issue
- **Steps to Reproduce:** Numbered steps to reproduce the behavior
- **Expected Behavior:** What you expected to happen
- **Actual Behavior:** What actually happened
- **Environment:**
  - OS (macOS, Linux, Windows)
  - Python version
  - MCP client (Claude, Cursor, etc.)
- **Logs:** Relevant log output from `timedoctor_mcp.log`
- **Screenshots:** If applicable

**For Feature Requests:**
- **Description:** Clear description of the feature
- **Use Case:** Why this feature would be useful
- **Proposed Solution:** How you envision it working
- **Alternatives:** Other solutions you've considered

### Issue Labels

Issues are labeled to help organize and prioritize:
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed

## Development Workflow

### Project Structure

```
timedoctor-mcp/
├── src/
│   ├── scraper.py         # Browser automation
│   ├── parser.py          # HTML parsing
│   ├── transformer.py     # CSV formatting
│   └── mcp_server.py      # MCP server
├── tests/
│   ├── test_*.py          # Test files
│   └── debug_*.py         # Debug utilities
├── .env                   # Credentials (git-ignored)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Ruff configuration
└── README.md              # Main documentation
```

### Key Components

**`src/scraper.py`:**
- Playwright browser automation
- Login handling
- Date navigation
- HTML extraction

**`src/parser.py`:**
- Angular Material tree parsing
- Time string parsing (e.g., "3h 50m")
- Task aggregation

**`src/transformer.py`:**
- CSV generation
- Data formatting
- Hours calculation

**`src/mcp_server.py`:**
- MCP protocol implementation
- 4 tools: `export_weekly_csv`, `get_daily_report`, `get_hours_summary`, `export_today_csv`

### Adding New Features

When adding a new feature:

1. **Discuss first** - Open an issue to discuss major changes
2. **Plan the approach** - Consider architecture and impact
3. **Update documentation** - Keep README.md in sync
4. **Add tests** - Cover new functionality
5. **Follow code style** - Use ruff for consistency

## Questions?

If you have questions:
- Check the [README.md](README.md) for documentation
- Open a [Discussion](https://github.com/frifster/timedoctor-mcp/discussions) on GitHub
- Create an [Issue](https://github.com/frifster/timedoctor-mcp/issues) for bugs or feature requests

## Recognition

Contributors will be recognized in:
- Git commit history
- GitHub contributors page
- Release notes (for significant contributions)

Thank you for contributing to Time Doctor MCP! 🎉
