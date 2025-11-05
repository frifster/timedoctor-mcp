"""
Constants and configuration values for Time Doctor MCP scraper.
All timeouts are in milliseconds unless otherwise noted.
"""

# Browser Configuration
BROWSER_DEFAULT_TIMEOUT_MS = 30000  # 30 seconds
BROWSER_VIEWPORT_WIDTH = 1920
BROWSER_VIEWPORT_HEIGHT = 1080
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Page Navigation Timeouts
PAGE_LOAD_TIMEOUT_MS = 60000  # 60 seconds for initial page loads
LOGIN_NAVIGATION_TIMEOUT_MS = 30000  # 30 seconds for login redirect
EMAIL_SELECTOR_TIMEOUT_MS = 10000  # 10 seconds to find email input

# Smart Wait Timeouts (for wait_for_load_state operations)
# These need to be longer than fixed waits because networkidle waits for all network activity
LOGIN_FORM_LOAD_WAIT_MS = 10000  # Wait for login form to reach networkidle (10s)
POST_LOGIN_WAIT_MS = 10000  # Wait after login for networkidle (10s)
REPORT_PAGE_LOAD_WAIT_MS = 10000  # Wait for report page networkidle (10s)
EXPAND_ALL_WAIT_MS = 5000  # Wait after clicking expand all (5s)
CONTENT_LOAD_WAIT_MS = 5000  # Wait for content DOM to load (5s)
DATE_NAVIGATION_WAIT_MS = 3000  # Wait for date navigation networkidle (3s)

# Caching Configuration
CACHE_TTL_SECONDS = 300  # 5 minutes cache time-to-live
CACHE_DIR_NAME = ".cache"

# Retry Configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 1
RETRY_MAX_WAIT_SECONDS = 10
RETRY_MULTIPLIER = 2  # Exponential backoff multiplier

# Parallel Scraping Configuration
MAX_PARALLEL_SESSIONS = 5  # Maximum number of parallel browser contexts
PARALLEL_THRESHOLD = 3  # Use parallel scraping if date count >= this value
