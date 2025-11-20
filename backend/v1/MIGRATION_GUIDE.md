"""
Migration Guide - Transitioning from old to new AIT architecture.

This guide provides step-by-step instructions for migrating code from the
monolithic old structure to the new layered architecture.
"""

# =============================================================================
# MIGRATION STRATEGY OVERVIEW
# =============================================================================

"""
PHASED APPROACH (Recommended Timeline: 2-3 weeks)

Phase 1: Foundation (Days 1-2)
├── Set up new environment and dependencies
├── Run initial tests
└── Parallel run old and new systems

Phase 2: Tool Migration (Days 3-5)
├── Replace file operations
├── Replace backup operations
├── Replace diff generation
└── Test compatibility

Phase 3: Service Migration (Days 6-8)
├── Migrate Git operations
├── Migrate state management
└── Update existing code

Phase 4: Workflow Integration (Days 9-12)
├── Integrate workflow orchestrator
├── Update API endpoints
├── Test end-to-end workflows
└── Performance testing

Phase 5: Cleanup & Optimization (Days 13-14)
├── Remove old code
├── Optimize performance
├── Final testing
└── Deployment

RISK MITIGATION:
- Keep old code running alongside new code
- Run parallel tests on both systems
- Use feature flags for gradual rollout
- Maintain backups of all changes
- Document any deviations from expected behavior
"""

# =============================================================================
# PHASE 1: FOUNDATION SETUP (Days 1-2)
# =============================================================================

"""
STEP 1.1: Install Dependencies

Required packages:
pip install fastapi pydantic python-dotenv openpyxl openai

Optional packages:
pip install pytest pytest-cov pytest-mock  # for testing
pip install black flake8 mypy  # for code quality

STEP 1.2: Set Up Environment

Create .env file:
OPENAI_API_KEY=sk-...
AIT_OUTPUT_DIR=/path/to/outputs
AIT_LOG_DIR=/path/to/logs
AIT_CLONE_BASE_DIR=/path/to/clones
AIT_USE_LLM=true
AIT_LOG_LEVEL=INFO

STEP 1.3: Verify New Architecture

from aitcore.v1.config import init_config, get_config
from aitcore.v1.utils import get_logger

config = init_config()
logger = get_logger(__name__)
logger.info(f"Outputs: {config.outputs_dir}")

STEP 1.4: Run Initial Tests

pytest backend/v1/tests/test_aitcore.py -v
pytest backend/v1/tests/test_aitcore.py::TestConfiguration -v
"""

# =============================================================================
# PHASE 2: TOOL MIGRATION (Days 3-5)
# =============================================================================

"""
MIGRATION MAPPING:

OLD: agentic-tagging-workbench-backend-main/core/utils/file_handler.py
NEW: aitcore.v1.tools.FileHandler

OLD CODE:
    from core.utils.file_handler import read_file_content, save_json
    content = read_file_content("path/to/file.js")
    save_json("output.json", data)

NEW CODE:
    from aitcore.v1.tools import FileHandler
    content = FileHandler.read_file("path/to/file.js")
    FileHandler.write_json("output.json", data)

COMPATIBILITY WRAPPER (optional):
    from aitcore.v1.tools import FileHandler
    def read_file_content(path):
        return FileHandler.read_file(path)
    def save_json(path, data):
        FileHandler.write_json(path, data)

---

OLD: core/utils/file_handler.py - find_react_files()
NEW: aitcore.v1.tools.FileHandler.find_react_files()

OLD CODE:
    from core.utils.file_handler import find_react_files
    files = find_react_files("./repo")

NEW CODE:
    from aitcore.v1.tools import FileHandler
    files = FileHandler.find_react_files("./repo")

---

OLD: core/rollback_changes.py - restore operations
NEW: aitcore.v1.tools.BackupManager

OLD CODE:
    from core.rollback_changes import restore_all_backups
    restore_all_backups("./repo")

NEW CODE:
    from aitcore.v1.tools import BackupManager
    count, errors = BackupManager.restore_all_backups("./repo")

TESTING TOOL MIGRATION:
    pytest backend/v1/tests/test_aitcore.py::TestFileHandler -v
    pytest backend/v1/tests/test_aitcore.py::TestBackupManager -v
"""

# =============================================================================
# PHASE 3: SERVICE MIGRATION (Days 6-8)
# =============================================================================

"""
MIGRATION MAPPING:

OLD: core/cloneRepo.py
NEW: aitcore.v1.services.GitService

OLD CODE:
    from core.cloneRepo import clone_repo
    clone_repo("https://github.com/user/repo", "/path/to/clone")

NEW CODE:
    from aitcore.v1.services import GitService
    repo_path = GitService.clone_repository(
        "https://github.com/user/repo",
        Path("/path/to/clone")
    )

DIFFERENCES:
- Old: Returns None, saves to filesystem
- New: Returns Path object to cloned repository
- Old: Function named clone_repo()
- New: Method named clone_repository()

---

OLD: core/agents/agent.py - write_outputs()
NEW: aitcore.v1.services.StateManager

OLD CODE:
    from core.agents.agent import write_outputs
    write_outputs(results, output_dir)

NEW CODE:
    from aitcore.v1.services import StateManager
    state = StateManager()
    state.save_suggestions_state(
        spec_file="techspec.xlsx",
        repo_path="/repo/path",
        suggestion_count=42,
        generated_at=datetime.now()
    )

TESTING SERVICE MIGRATION:
    pytest backend/v1/tests/test_aitcore.py::TestIntegration -v
"""

# =============================================================================
# PHASE 4: WORKFLOW INTEGRATION (Days 9-12)
# =============================================================================

"""
UPDATING API ENDPOINTS:

OLD: aitapi/v1/router.py - monolithic implementation
NEW: aitcore.v1.workflow + aitcore.v1.agents

OLD ENDPOINT STRUCTURE:
    @app.post("/api/generate-techspec")
    async def generate_techspec(req):
        # Direct implementation
        # Mix of file handling, LLM, writing
        return results

NEW ENDPOINT STRUCTURE:
    @app.post("/generate-techspec")
    async def generate_techspec(req: GenerateTechSpecRequest):
        orchestrator = WorkflowOrchestrator(workflow_id)
        orchestrator.add_step(TechSpecGenerationStep())
        result = orchestrator.execute(input_data)
        return WorkflowResponse(...)

WORKFLOW INTEGRATION EXAMPLE:

from aitcore.v1.workflow import (
    WorkflowOrchestrator,
    TechSpecGenerationStep,
    TaggingSuggestionStep,
    TaggingApplicationStep,
)

# Create workflow
orchestrator = WorkflowOrchestrator("workflow_123")
orchestrator.add_step(TechSpecGenerationStep())
orchestrator.add_step(TaggingSuggestionStep())
orchestrator.add_step(TaggingApplicationStep())

# Register callbacks (optional)
orchestrator.on_step_complete(lambda result: print(f"Step {result.step_name} done"))
orchestrator.on_workflow_complete(lambda result: print(f"Workflow {'success' if result.success else 'failed'}"))

# Execute
result = orchestrator.execute({
    "figma_file_url": "...",
    "repo_url": "...",
    "output_dir": "..."
})

print(f"Success: {result.success}")
for step in result.steps:
    print(f"  {step.step_name}: {step.status.value}")

UPDATING EXISTING ENDPOINTS:

OLD: POST /tagging/suggest
    - Direct agent call
    - Monolithic code

NEW: POST /suggest-tagging
    - Workflow-based
    - Clean separation of concerns
    - Easier to test and maintain

TESTING WORKFLOW INTEGRATION:
    pytest backend/v1/tests/test_aitcore.py::TestWorkflow -v
    pytest backend/v1/src/aitapi/v1/test_router.py -v
"""

# =============================================================================
# PHASE 5: CLEANUP & OPTIMIZATION (Days 13-14)
# =============================================================================

"""
DEPRECATION STRATEGY:

Step 1: Add deprecation warnings to old code
    import warnings
    warnings.warn(
        "core.agents.agent is deprecated. Use aitcore.v1.workflow instead.",
        DeprecationWarning,
        stacklevel=2
    )

Step 2: Update all imports in codebase
    # Find all occurrences
    grep -r "from core.agents" agentic-tagging-workbench-backend-main/

    # Replace with new imports
    from aitcore.v1.agents import TechSpecAgent

Step 3: Remove old code once fully migrated
    # Create backup
    cp -r agentic-tagging-workbench-backend-main/ agentic-tagging-workbench-backend-main.backup/
    
    # Remove old directories after verifying functionality
    rm -rf agentic-tagging-workbench-backend-main/core/agents
    rm -rf agentic-tagging-workbench-backend-main/core/tools

PERFORMANCE OPTIMIZATION:

1. Profile code execution
    python -m cProfile -s cumulative main.py

2. Identify bottlenecks
    - File I/O operations (cache frequently accessed files)
    - LLM calls (implement caching, batch processing)
    - Repository operations (use shallow clones)

3. Apply optimizations
    - Add caching to FileHandler
    - Batch LLM requests
    - Implement async file operations
    - Use connection pooling for Git

FINAL TESTING:
    # Run full test suite
    pytest backend/v1/tests/ -v --cov=aitcore
    
    # Test API endpoints
    pytest backend/v1/src/aitapi/v1/test_router.py -v
    
    # Performance tests
    pytest backend/v1/tests/test_aitcore.py::TestPerformance -v
    
    # Integration tests
    pytest backend/v1/tests/test_aitcore.py::TestIntegration -v
"""

# =============================================================================
# MIGRATION CHECKLIST
# =============================================================================

"""
PHASE 1: FOUNDATION
☐ Install dependencies
☐ Set up .env file
☐ Initialize config
☐ Run basic tests
☐ Verify logger setup
☐ Create wrapper modules for compatibility

PHASE 2: TOOLS
☐ Replace FileHandler usage
☐ Replace BackupManager usage
☐ Replace DiffGenerator usage
☐ Update OpenAI client calls
☐ Test file operations
☐ Test backup/restore

PHASE 3: SERVICES
☐ Update Git operations
☐ Update state management
☐ Update repository scanning
☐ Test service integration
☐ Verify error handling

PHASE 4: WORKFLOW
☐ Integrate workflow orchestrator
☐ Update API endpoints
☐ Update request/response models
☐ Test end-to-end workflows
☐ Verify callback system
☐ Performance testing

PHASE 5: CLEANUP
☐ Add deprecation warnings
☐ Update all imports
☐ Remove old code
☐ Final testing
☐ Documentation update
☐ Deployment

VALIDATION TESTS:
☐ All tests pass
☐ API endpoints working
☐ Workflows execute successfully
☐ Performance meets requirements
☐ Error handling working
☐ Logging comprehensive
☐ Backwards compatibility (if needed)
"""

# =============================================================================
# COMMON ISSUES & SOLUTIONS
# =============================================================================

"""
ISSUE 1: Import Errors
SYMPTOM: ModuleNotFoundError: No module named 'aitcore.v1'
SOLUTION:
    1. Verify PYTHONPATH includes backend/v1/src
    2. Check __init__.py files exist in all packages
    3. Ensure dependencies installed: pip install -r requirements.txt

ISSUE 2: OpenAI API Errors
SYMPTOM: AuthenticationError from OpenAI client
SOLUTION:
    1. Check OPENAI_API_KEY in .env file
    2. Verify API key is valid: openai.api_key_valid()
    3. Check API rate limits

ISSUE 3: File Operation Errors
SYMPTOM: FileNotFoundError during operations
SOLUTION:
    1. Verify paths are absolute or relative to correct directory
    2. Check file permissions
    3. Ensure directories exist: mkdir -p /path/to/dir

ISSUE 4: Git Clone Failures
SYMPTOM: Repository clone fails
SOLUTION:
    1. Verify URL is valid: git ls-remote <url>
    2. Check network connectivity
    3. Verify branch exists: git ls-remote <url> <branch>
    4. Check SSH keys if using private repos

ISSUE 5: State Management Issues
SYMPTOM: State not being persisted
SOLUTION:
    1. Verify state directory writable
    2. Check JSON serialization of objects
    3. Ensure StateManager initialized before use
    4. Check file permissions in state directory

ISSUE 6: Workflow Step Failures
SYMPTOM: Workflow stops at particular step
SOLUTION:
    1. Check step input validation
    2. Review step execution logs
    3. Verify step dependencies
    4. Check error handling in step
"""

# =============================================================================
# ROLLBACK PROCEDURES
# =============================================================================

"""
IF MIGRATION FAILS - Rollback Plan:

1. IMMEDIATE ROLLBACK (within 1 hour):
   - Switch API to use old code
   - Revert database changes
   - Notify users of service interruption

2. INVESTIGATION (next 24 hours):
   - Analyze logs from failed migration
   - Identify root cause
   - Plan fixes

3. FIX & RETRY:
   - Address identified issues
   - Run comprehensive tests
   - Plan second migration attempt

BACKUP STRATEGY:
   # Before migration
   cp -r backend/v1 backend/v1.backup
   cp -r agentic-tagging-workbench-backend-main/ agentic-tagging-workbench-backend-main.backup/
   
   # Restore if needed
   rm -rf backend/v1
   cp -r backend/v1.backup backend/v1
"""

# =============================================================================
# SUCCESS CRITERIA
# =============================================================================

"""
MIGRATION IS SUCCESSFUL WHEN:

✓ All unit tests pass (100% pass rate)
✓ All integration tests pass
✓ API endpoints respond correctly
✓ Workflows execute end-to-end
✓ Error handling works properly
✓ Logging captures all important events
✓ Performance meets or exceeds old system
✓ File operations work reliably
✓ State persistence works
✓ No data loss during migration
✓ Backwards compatibility maintained (if required)
✓ Documentation updated
✓ Team trained on new architecture

PERFORMANCE BENCHMARKS:
- TechSpec generation: < 5 minutes
- Tagging suggestion: < 10 minutes (10K LOC)
- Tagging application: < 5 minutes (50 files)
- Rollback operation: < 1 minute
- API response time: < 2 seconds
- Error recovery: automatic within 10 seconds
"""

print(__doc__)
