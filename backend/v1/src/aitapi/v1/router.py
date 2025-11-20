"""
AIT API Router - FastAPI endpoints for AI Code Tagging workflow.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Core imports from new architecture
from aitcore.v1.config import init_config, get_config
from aitcore.v1.utils import get_logger
from aitcore.v1.workflow import (
    WorkflowOrchestrator,
    TechSpecGenerationStep,
    TaggingSuggestionStep,
    TaggingApplicationStep,
    RollbackStep,
)
from aitcore.v1.agents import TechSpecAgent, TaggingAgent, ApplicationAgent
from aitcore.v1.generators import AnalyticsGenerator, ReportWriter
from aitcore.v1.tools import DiffGenerator
from aitcore.v1.services import StateManager

logger = get_logger(__name__)

# Initialize config
config = init_config()

# Create FastAPI app
app = FastAPI(
    title="AI Code Tagging API",
    description="API for automated analytics tagging in React applications",
    version="2.0.0"
)

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GenerateTechSpecRequest(BaseModel):
    """Request for TechSpec generation."""
    figma_file_url: str
    ac_text: Optional[str] = None
    ac_local_file: Optional[str] = None
    output_dir: Optional[str] = None


class SuggestTaggingRequest(BaseModel):
    """Request for tagging suggestions."""
    techspec_path: str
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    branch: Optional[str] = None
    output_dir: Optional[str] = None


class ApplyTaggingRequest(BaseModel):
    """Request to apply tagging suggestions."""
    suggestions_path: str
    repo_path: str
    dry_run: bool = False
    output_dir: Optional[str] = None


class RollbackRequest(BaseModel):
    """Request to rollback changes."""
    repo_path: str
    delete_backups: bool = False
    output_dir: Optional[str] = None


class ViewDifferenceRequest(BaseModel):
    """Request to view differences."""
    repo_path: str
    output_dir: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Response from workflow execution."""
    workflow_id: str
    status: str
    success: bool
    started_at: str
    completed_at: str
    output: Dict[str, Any]


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.get("/status")
async def get_status():
    """Get API status."""
    state = StateManager()
    workflow_status = state.get_workflow_status()
    
    return {
        "status": "running",
        "config": {
            "outputs_dir": str(config.outputs_dir),
            "clone_base_dir": str(config.clone_base_dir),
            "use_llm": config.use_llm,
        },
        "workflow_status": workflow_status
    }


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/generate-techspec", response_model=WorkflowResponse)
async def generate_techspec(request: GenerateTechSpecRequest):
    """
    Generate TechSpec from acceptance criteria and Figma designs.
    
    This endpoint starts a workflow to parse and organize technical
    specifications for analytics tagging.
    """
    workflow_id = f"techspec_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting TechSpec generation: {workflow_id}")
    
    try:
        # Create workflow
        orchestrator = WorkflowOrchestrator(workflow_id)
        orchestrator.add_step(TechSpecGenerationStep())
        
        # Prepare input
        input_data = {
            "figma_file_url": request.figma_file_url,
            "ac_text": request.ac_text,
            "ac_local_file": request.ac_local_file,
            "output_dir": request.output_dir or str(config.outputs_dir),
        }
        
        # Execute workflow
        result = orchestrator.execute(input_data)
        
        # Extract output from first step
        output = {}
        if result.steps:
            output = result.steps[0].output or {}
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="completed" if result.success else "failed",
            success=result.success,
            started_at=result.started_at.isoformat(),
            completed_at=result.completed_at.isoformat(),
            output=output
        )
    
    except Exception as e:
        logger.error(f"TechSpec generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/suggest-tagging", response_model=WorkflowResponse)
async def suggest_tagging(request: SuggestTaggingRequest):
    """
    Generate tagging suggestions for code locations.
    
    Analyzes repository code and matches it to TechSpec items,
    generating suggestions for where to add tracking code.
    """
    workflow_id = f"suggest_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting tagging suggestion: {workflow_id}")
    
    try:
        # Create workflow
        orchestrator = WorkflowOrchestrator(workflow_id)
        orchestrator.add_step(TaggingSuggestionStep())
        
        # Prepare input
        input_data = {
            "techspec_path": request.techspec_path,
            "repo_url": request.repo_url,
            "repo_path": request.repo_path,
            "branch": request.branch,
            "output_dir": request.output_dir or str(config.outputs_dir),
        }
        
        # Execute workflow
        result = orchestrator.execute(input_data)
        
        # Extract output
        output = {}
        if result.steps:
            output = result.steps[0].output or {}
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="completed" if result.success else "failed",
            success=result.success,
            started_at=result.started_at.isoformat(),
            completed_at=result.completed_at.isoformat(),
            output=output
        )
    
    except Exception as e:
        logger.error(f"Tagging suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/apply-tagging", response_model=WorkflowResponse)
async def apply_tagging(request: ApplyTaggingRequest):
    """
    Apply tagging suggestions to repository files.
    
    Modifies source code files to add tracking calls based on
    the generated suggestions. Creates backups before modifications.
    """
    workflow_id = f"apply_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting tagging application: {workflow_id}")
    
    try:
        # Create workflow
        orchestrator = WorkflowOrchestrator(workflow_id)
        orchestrator.add_step(TaggingApplicationStep())
        
        # Prepare input
        input_data = {
            "suggestions_path": request.suggestions_path,
            "repo_path": request.repo_path,
            "dry_run": request.dry_run,
            "output_dir": request.output_dir or str(config.outputs_dir),
        }
        
        # Execute workflow
        result = orchestrator.execute(input_data)
        
        # Extract output
        output = {}
        if result.steps:
            output = result.steps[0].output or {}
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="completed" if result.success else "failed",
            success=result.success,
            started_at=result.started_at.isoformat(),
            completed_at=result.completed_at.isoformat(),
            output=output
        )
    
    except Exception as e:
        logger.error(f"Tagging application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rollback-changes", response_model=WorkflowResponse)
async def rollback_changes(request: RollbackRequest):
    """
    Rollback applied tagging changes.
    
    Restores all modified files from backups, reverting any
    tagging code that was applied.
    """
    workflow_id = f"rollback_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting rollback: {workflow_id}")
    
    try:
        # Create workflow
        orchestrator = WorkflowOrchestrator(workflow_id)
        orchestrator.add_step(RollbackStep())
        
        # Prepare input
        input_data = {
            "repo_path": request.repo_path,
            "delete_backups": request.delete_backups,
            "output_dir": request.output_dir or str(config.outputs_dir),
        }
        
        # Execute workflow
        result = orchestrator.execute(input_data)
        
        # Extract output
        output = {}
        if result.steps:
            output = result.steps[0].output or {}
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="completed" if result.success else "failed",
            success=result.success,
            started_at=result.started_at.isoformat(),
            completed_at=result.completed_at.isoformat(),
            output=output
        )
    
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/view-difference")
async def view_difference(request: ViewDifferenceRequest):
    """
    View differences between backups and current files.
    
    Generates a detailed diff report showing all changes
    made by the tagging application.
    """
    try:
        report = DiffGenerator.generate_diff_report(request.repo_path)
        
        return {
            "repo_path": report.repo_path,
            "generated_at": report.generated_at.isoformat(),
            "files_modified": report.total_files(),
            "lines_added": report.total_lines_added(),
            "lines_removed": report.total_lines_removed(),
            "diffs": [d.to_dict() for d in report.diffs[:10]]  # First 10
        }
    
    except Exception as e:
        logger.error(f"Diff generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow-status")
async def get_workflow_status():
    """
    Get current workflow status and history.
    
    Returns saved state from the most recent workflow runs.
    """
    try:
        state = StateManager()
        status = state.get_workflow_status()
        
        return {
            "current_repo": status.get("repo_root"),
            "techspec": status.get("techspec"),
            "suggestions": status.get("suggestions"),
            "application": status.get("apply"),
        }
    
    except Exception as e:
        logger.error(f"Status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.post("/generate-track-js")
async def generate_track_js(suggestions_path: str):
    """
    Generate track.js analytics helper file.
    
    Creates a JavaScript utility file with tracking functions
    for all suggestions.
    """
    try:
        from aitcore.v1.tools import FileHandler
        
        suggestions_data = FileHandler.read_json(suggestions_path)
        
        generator = AnalyticsGenerator()
        track_js_code = generator.generate_track_js(
            suggestions_data.get("suggestions", [])
        )
        
        return {
            "code": track_js_code,
            "functions_generated": len(suggestions_data.get("suggestions", [])),
        }
    
    except Exception as e:
        logger.error(f"track.js generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-report")
async def generate_report(report_type: str, data_path: str):
    """
    Generate formatted reports.
    
    Creates Markdown reports from workflow results.
    Supported types: suggestions, apply, workflow
    """
    try:
        from aitcore.v1.tools import FileHandler
        
        data = FileHandler.read_json(data_path)
        writer = ReportWriter()
        
        if report_type == "suggestions":
            report = writer.generate_suggestions_report(data)
        elif report_type == "apply":
            report = writer.generate_apply_report(data)
        elif report_type == "workflow":
            report = writer.generate_workflow_report(data)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        return {
            "report": report,
            "type": report_type,
            "length": len(report),
        }
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8880)

