"""
System-wide constants and configuration values.
"""

from enum import Enum
from typing import Final

# File Extensions
REACT_FILE_EXTENSIONS: Final = {'.jsx', '.tsx', '.js', '.ts'}
EXCEL_FILE_EXTENSION: Final = '.xlsx'
BACKUP_SUFFIX: Final = '.taggingai.bak'
MARKDOWN_EXTENSION: Final = '.md'
JSON_EXTENSION: Final = '.json'

# Directories
DEFAULT_OUTPUTS_DIR: Final = 'outputs'
DEFAULT_LOGS_DIR: Final = 'logs'
DEFAULT_CLONE_BASE: Final = '~/ATTagger/Clones'

# File Names
TECHSPEC_FILENAME: Final = 'techspec.xlsx'
TAGGING_UNIFIED_JSON: Final = 'tagging_unified.json'
TAGGING_UNIFIED_MD: Final = 'tagging_unified.md'
APPLY_LOG_FILENAME: Final = 'apply_log.json'
METRICS_FILENAME: Final = 'metrics.json'
LAST_REPO_ROOT_FILE: Final = '.last_repo_root'
FIGMA_SCREENSHOT_FILE: Final = 'figma_screen.png'

# Analytics/Tracking
DEFAULT_TRACK_HELPER_PATH: Final = 'src/analytics/track.js'
ANALYTICS_VENDOR_ADOBE: Final = 'adobe'

# LLM Settings
DEFAULT_LLM_MODEL: Final = 'Gemini 2.5 Flash'
LLM_TEMPERATURE: Final = 0
DEFAULT_LLM_TIMEOUT: Final = 60

# Regex Patterns
GITHUB_URL_PATTERN: Final = r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/[^/]+)?/?$'
EVAR_PROP_PATTERN: Final = r'^(eVar|prop)\d+$'

# Action Types
class ActionType(str, Enum):
    """Enumeration of supported action types."""
    CLICK = "click"
    SUBMIT = "submit"
    VIEW = "view"
    BACK = "back"
    EXIT = "exit"
    SELECT = "select"
    NAV = "nav"
    UNKNOWN = "unknown"

# Page View Marker
PAGE_VIEW_MARKER: Final = '__pv'
PAGE_NAME_KEY: Final = 'pageName'

# Backup Settings
BACKUP_SEARCH_PATTERN: Final = f'*{BACKUP_SUFFIX}'
MAX_BACKUPS_PER_FILE: Final = 5

# Clone Settings
GIT_CLONE_DEPTH: Final = 1
GITHUB_API_TIMEOUT: Final = 30

# Diff Settings
DIFF_CONTEXT_LINES: Final = 3
DIFF_LINE_RADIUS: Final = 6

# Snippet Settings
SNIPPET_LINE_RADIUS: Final = 40
MIN_SNIPPET_MATCH_SCORE: Final = 0.6

# File Read Encodings (fallback order)
FILE_ENCODINGS: Final = ['utf-8', 'utf-8-sig', 'latin-1']

# Skip Patterns for Directory Scanning
SKIP_PATTERNS: Final = {'node_modules', 'build', 'dist', '.git', '.next', 'coverage', '.venv', 'venv'}

# LLM Retry Settings
LLM_MAX_RETRIES: Final = 2
LLM_RETRY_DELAY: Final = 1.0

# Logging Levels
LOG_LEVEL_DEBUG: Final = 'DEBUG'
LOG_LEVEL_INFO: Final = 'INFO'
LOG_LEVEL_WARNING: Final = 'WARNING'
LOG_LEVEL_ERROR: Final = 'ERROR'
