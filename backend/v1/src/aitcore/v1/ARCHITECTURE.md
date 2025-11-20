"""
AIT Core Architecture Documentation and Implementation Guide

This document describes the restructured architecture of the Agentic Tagging System (AIT).
"""

# =============================================================================
# ARCHITECTURE OVERVIEW
# =============================================================================

"""
The AIT system has been restructured into a clean, layered architecture with proper
separation of concerns, making it more maintainable, testable, and scalable.

ARCHITECTURE LAYERS (bottom to top):
"""

# Layer 1: Foundation Layer
# ├── exceptions.py          - Custom exception hierarchy
# ├── config/
# │   └── settings.py        - Centralized configuration management
# └── utils/
#     ├── constants.py       - System-wide constants and enums
#     ├── logger.py          - Logging utilities
#     ├── validators.py      - Input validation
#     └── formatters.py      - Output formatting

# Layer 2: Data Models Layer
# └── models/
#     ├── techspec.py        - TechSpec data structures
#     ├── suggestions.py     - Tagging suggestion models
#     └── tagging.py         - Application and repo models

# Layer 3: Tools Layer
# └── tools/
#     ├── file_handler.py    - File operations
#     ├── diff_generator.py  - Diff generation and comparison
#     ├── backup_manager.py  - Backup and restoration
#     └── openai_client.py   - LLM integration

# Layer 4: Services Layer
# └── services/
#     ├── repo_service.py    - Git and repository operations
#     ├── state_manager.py   - Workflow state persistence
#     └── metrics_service.py - [Planned] Metrics and analytics

# Layer 5: Workflow Layer (To be implemented)
# └── workflow/
#     ├── orchestrator.py    - Main workflow coordinator
#     └── steps/
#         ├── techspec_generation.py
#         ├── tagging_suggestion.py
#         ├── tagging_application.py
#         └── rollback.py

# Layer 6: Generators Layer (To be implemented)
# └── generators/
#     ├── analytics_generator.py   - track.js generation
#     ├── code_suggester.py        - Code suggestions
#     └── report_writer.py         - Report generation

# Layer 7: Agents Layer (To be implemented)
# └── agents/
#     ├── base_agent.py           - Abstract agent
#     ├── techspec_agent.py       - TechSpec generation agent
#     ├── tagging_agent.py        - Tagging suggestion agent
#     └── application_agent.py    - Application agent

# =============================================================================
# KEY DESIGN PRINCIPLES
# =============================================================================

"""
1. SEPARATION OF CONCERNS
   - Each module has a single, well-defined responsibility
   - Clear dependencies and minimal coupling
   - Easy to test and modify individual components

2. CONFIGURATION AS CODE
   - Centralized configuration in settings.py
   - Environment variable integration
   - Runtime configuration validation

3. PROPER ERROR HANDLING
   - Custom exception hierarchy for different error types
   - Graceful degradation with fallbacks
   - Clear error messages for debugging

4. DATA MODELS AS FIRST CLASS
   - Strong typing with dataclasses
   - Serialization support (to_dict methods)
   - Clear data contracts between layers

5. DEPENDENCY INJECTION
   - Services accept dependencies via __init__
   - Global singletons for configuration (get_config)
   - Easy to mock for testing

6. LOGGING AND OBSERVABILITY
   - Structured logging throughout
   - Logger instances per module
   - Integration with config for log levels

7. VALIDATION AND FORMATTING
   - Input validation at system boundaries
   - Output formatting for consistency
   - Human-readable error messages
"""

# =============================================================================
# MODULE REFERENCE
# =============================================================================

"""
EXCEPTIONS (exceptions.py)
├── AITException (base)
├── ConfigurationError
├── FileOperationError
├── RepoOperationError
├── SpecParsingError
├── MatchingError
├── LLMError
├── TaggingError
├── ApplyError
├── BackupError
├── RollbackError
├── ValidationError
└── StateError

CONSTANTS (utils/constants.py)
├── File Extensions: REACT_FILE_EXTENSIONS, EXCEL_FILE_EXTENSION
├── Directories: DEFAULT_OUTPUTS_DIR, DEFAULT_LOGS_DIR
├── File Names: TECHSPEC_FILENAME, TAGGING_UNIFIED_JSON, etc.
├── Action Types: ActionType enum (click, view, submit, back, exit, select, nav)
├── LLM Settings: DEFAULT_LLM_MODEL, LLM_TEMPERATURE
└── ... (50+ constants defined)

CONFIGURATION (config/settings.py)
class AITConfig:
    ├── base_dir: Path               - Installation directory
    ├── outputs_dir: Path            - Output files directory
    ├── logs_dir: Path               - Log files directory
    ├── clone_base_dir: Path         - Repository clone directory
    ├── openai_api_key: str          - LLM API key
    ├── llm_model: str               - LLM model name
    ├── use_llm: bool                - Whether LLM is available
    ├── get_output_file()            - Get output file path
    ├── get_log_file()               - Get log file path
    └── get_clone_path()             - Get repo clone path

Global Functions:
├── get_config() -> AITConfig        - Get singleton instance
└── init_config() -> AITConfig       - Initialize config

DATA MODELS (models/)
TechSpec:
  ├── file_path: str
  ├── generated_at: datetime
  ├── items: List[SpecItem]
  ├── sheets_parsed: List[str]
  └── metadata: Dict

SpecItem:
  ├── sheet: str
  ├── row_index: int
  ├── description: str
  ├── action: str
  ├── component: str
  ├── page: str
  ├── adobe: AdobeConfig
  └── target_terms: List[str]

TaggingReport:
  ├── run_id: str
  ├── spec_file: str
  ├── repo_path: str
  ├── generated_at: datetime
  ├── suggestions: List[TaggingSuggestion]
  ├── helper_file: Dict
  └── metadata: Dict

ApplyReport:
  ├── run_id: str
  ├── repo_path: str
  ├── started_at: datetime
  ├── completed_at: datetime
  ├── results: List[ApplyResult]
  └── metadata: Dict

TOOLS (tools/)
FileHandler:
  ├── read_file(path) -> str
  ├── write_file(path, content)
  ├── read_json(path) -> Dict
  ├── write_json(path, data)
  ├── find_react_files(repo_path) -> List[str]
  ├── create_backup(path) -> Path
  └── delete_file(path)

DiffGenerator:
  ├── generate_unified_diff(old, new) -> str
  ├── count_diff_changes(diff) -> Tuple[int, int]
  ├── create_file_diff(backup, current) -> FileDiff
  ├── find_backup_pairs(repo) -> List[Tuple]
  └── generate_diff_report(repo) -> DiffReport

BackupManager:
  ├── create_backup(path) -> Path
  ├── restore_from_backup(backup, target)
  ├── find_backups(repo) -> List[Path]
  ├── restore_all_backups(repo) -> Tuple[int, List]
  └── cleanup_backups(repo) -> int

OpenAIClient:
  ├── call_chat(messages) -> str
  ├── extract_json(response) -> Dict
  ├── explain_mapping(spec, location, snippet) -> Dict
  └── generate_tracking_code(action, event, params) -> Dict

SERVICES (services/)
GitService:
  ├── clone_repository(url, path, branch) -> Path
  ├── get_default_branch(owner, repo) -> str
  └── [Internal] _run_git_command(cmd) -> str

RepositoryService:
  └── scan_repository(path) -> RepositoryInfo

StateManager:
  ├── save_repo_root(path)
  ├── load_repo_root() -> Optional[Path]
  ├── save_state(name, data)
  ├── load_state(name) -> Optional[Dict]
  ├── clear_state(name)
  ├── save_techspec_state(file, datetime)
  ├── save_suggestions_state(file, repo, count, datetime)
  ├── save_apply_state(repo, applied, failed, datetime)
  └── get_workflow_status() -> Dict
"""

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
EXAMPLE 1: Using Configuration
---
from aitcore.v1.config import get_config
from aitcore.v1.utils import get_logger

config = get_config()
logger = get_logger(__name__)

logger.info(f"Outputs directory: {config.outputs_dir}")
output_file = config.get_output_file("tagging_unified.json")


EXAMPLE 2: Reading and Writing Files
---
from aitcore.v1.tools import FileHandler

# Read a file with automatic encoding detection
content = FileHandler.read_file("src/pages/Home.js")

# Write JSON output
data = {"items": [], "status": "success"}
FileHandler.write_json("outputs/result.json", data)

# Find all React files in a repo
react_files = FileHandler.find_react_files("./my-repo")


EXAMPLE 3: Managing Backups
---
from aitcore.v1.tools import BackupManager

# Create backup before modification
backup_path = BackupManager.create_backup("src/pages/Home.js")

# Later, restore from backup
BackupManager.restore_from_backup(backup_path, delete_backup=True)

# Find all backups in a repo
backups = BackupManager.find_backups("./my-repo")


EXAMPLE 4: Working with Repositories
---
from aitcore.v1.services import GitService, RepositoryService
from aitcore.v1.config import get_config

config = get_config()

# Clone a repository
repo_path = GitService.clone_repository(
    "https://github.com/user/my-repo",
    config.get_clone_path("my-repo")
)

# Scan the repository
repo_info = RepositoryService.scan_repository(repo_path)
print(f"React files: {repo_info.react_file_count}")


EXAMPLE 5: State Management
---
from aitcore.v1.services import StateManager
from datetime import datetime

state_mgr = StateManager()

# Save workflow state
state_mgr.save_suggestions_state(
    spec_file="techspec.xlsx",
    repo_path="/path/to/repo",
    suggestion_count=42,
    generated_at=datetime.now()
)

# Load and check status
status = state_mgr.get_workflow_status()
print(status)

# Clear state when done
state_mgr.clear_state(StateManager.STATE_SUGGESTIONS)


EXAMPLE 6: LLM Operations
---
from aitcore.v1.tools import OpenAIClient

client = OpenAIClient()

# Get LLM explanation for a mapping
explanation = client.explain_mapping(
    spec_item={"description": "Track button click", "action": "click"},
    code_location={"file": "src/pages/Home.js", "line": 42},
    snippet="<button onClick={handleClick}>Submit</button>"
)

# Generate tracking code
code = client.generate_tracking_code(
    action="click",
    event_name="button_click",
    params={"button_type": "submit"},
    code_snippet="<button>Submit</button>"
)


EXAMPLE 7: Generating Diffs
---
from aitcore.v1.tools import DiffGenerator

# Create diff between two files
diff = DiffGenerator.generate_unified_diff(
    "backup/Home.js.bak",
    "src/pages/Home.js"
)

# Count changes
added, removed = DiffGenerator.count_diff_changes(diff)
print(f"Added: {added}, Removed: {removed}")

# Generate complete diff report
report = DiffGenerator.generate_diff_report("./my-repo")
for file_diff in report.diffs:
    print(f"{file_diff.relative_path}: +{file_diff.lines_added} -{file_diff.lines_removed}")


EXAMPLE 8: Data Models and Serialization
---
from aitcore.v1.models import TechSpec, SpecItem, AdobeConfig
from datetime import datetime

# Create a spec item
item = SpecItem(
    sheet="Requirements",
    row_index=2,
    description="Track button click",
    action="click",
    adobe=AdobeConfig(variable="eVar27", value="button_click")
)

# Create TechSpec
spec = TechSpec(
    file_path="techspec.xlsx",
    generated_at=datetime.now(),
    items=[item],
    sheets_parsed=["Requirements"]
)

# Serialize to dict
spec_dict = spec.to_dict()

# Convert to JSON
from aitcore.v1.utils import format_json
json_str = format_json(spec_dict)
"""

# =============================================================================
# NEXT STEPS (Remaining Implementation)
# =============================================================================

"""
PENDING IMPLEMENTATION:

1. WORKFLOW ORCHESTRATOR (workflow/orchestrator.py)
   - Coordinate the entire tagging workflow
   - Step sequencing and error handling
   - Progress tracking and callbacks

2. WORKFLOW STEPS (workflow/steps/)
   - TechSpec generation step
   - Tagging suggestion step
   - Tagging application step
   - Rollback step

3. GENERATORS (generators/)
   - Analytics helper (track.js) generation
   - Code suggestion engine
   - Report generation (Markdown, JSON)

4. AGENTS (agents/)
   - Abstract agent base class
   - TechSpec parsing agent
   - Code matching/suggestion agent
   - Code modification/application agent

5. METRICS SERVICE (services/metrics_service.py)
   - Parse and aggregate metrics
   - Generate performance reports
   - Tracking statistics

6. API INTEGRATION (aitapi/)
   - REST endpoints for each workflow step
   - Request/response validation
   - Error handling and status codes
"""

# =============================================================================
# INTEGRATION WITH EXISTING API
# =============================================================================

"""
The new architecture maps to the existing API endpoints as follows:

POST /generate-techspec
  → workflow/steps/techspec_generation.py
  → agents/techspec_agent.py
  → generators/report_writer.py

POST /suggest-tagging
  → workflow/steps/tagging_suggestion.py
  → agents/tagging_agent.py
  → generators/code_suggester.py
  → tools/openai_client.py

POST /apply-tagging
  → workflow/steps/tagging_application.py
  → agents/application_agent.py
  → tools/backup_manager.py

GET /view-difference
  → tools/diff_generator.py
  → services/state_manager.py

POST /rollback-changes
  → workflow/steps/rollback.py
  → tools/backup_manager.py
  → services/state_manager.py
"""

print(__doc__)
