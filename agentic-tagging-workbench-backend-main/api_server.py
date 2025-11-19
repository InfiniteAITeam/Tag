# api_server.py - place in project root
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# added 9/17/2025
import json, difflib
from fastapi import  Query
from fastapi.responses import HTMLResponse
# ended

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from core.services.metrics_parser import parse_apply_stdout

# ------------ env & logging ------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic-api")

# ------------ paths (one source of truth) ------------
BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / "core"
OUTPUTS_DIR = CORE_DIR / "outputs"

TECHSPEC_XLSX = CORE_DIR / "techSpecAgent" / "TechSpecOutputs" / "techspec.xlsx"

# added 9/18/2025
FIGMA_PNG     = CORE_DIR / "techSpecAgent" / "TechSpecOutputs" / "figma_screen.png"
# ended 

SCRIPT_TECHSPEC = CORE_DIR / "techSpecGenerate.py"
SCRIPT_SUGGEST = CORE_DIR / "taggingSuggestion.py"
SCRIPT_APPLY = CORE_DIR / "applyTaggingAgent.py"
SCRIPT_ROLLBACK = CORE_DIR / "rollback_changes.py"

TAGGING_MD = OUTPUTS_DIR / "tagging_unified.md"
TAGGING_JSON = OUTPUTS_DIR / "tagging_unified.json"
APPLY_LOG = OUTPUTS_DIR / "apply_log.json"


# added 9/17/2025
LAST_REPO_ROOT = OUTPUTS_DIR / ".last_repo_root"
# ended

# ------------ app ------------
app = FastAPI(
    title="Agentic Tagging System API",
    description="API for TechSpec generation and tagging workflow",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------ models ------------
class TechSpecRequest(BaseModel):
    # repo_path: str
    # ac_local_file: str      # local text file with acceptance criteria
    # figma_file_url: str

    # One of these must be present
    ac_local_file: Optional[str] = None  # absolute/relative path on server
    ac_text: Optional[str] = None        # raw contents from browser "Browse files"
    figma_file_url: str


class SuggestTaggingRequest(BaseModel):
    # repo_path: str  # absolute or relative path to your repo
    repo_url: str
    branch: str | None = None
    clone_base: str | None = None  # optional override; otherwise your script's default

class RollbackRequest(BaseModel):
        # Allow either a URL (preferred) or a direct path (optional)
    repo_url: str | None = None
    repo_cloned_path: str | None = None
    delete_backups: bool = True    

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None


# ------------ helpers ------------
async def run_python_script(script_path: Path | str, env_vars: dict | None = None, cwd: Path | None = None) -> dict:
    """Run a Python script and return {success, stdout, stderr, return_code? | error?}"""
    try:
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        cmd = [sys.executable, str(script_path)]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(cwd or BASE_DIR),
        )
        stdout, stderr = await proc.communicate()
        ok = (proc.returncode == 0)
        return {
            "success": ok,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            **({} if ok else {"return_code": proc.returncode}),
        }
    except Exception as e:
        logger.exception("Error running script %s", script_path)
        return {"success": False, "error": str(e)}

def require_file(path: Path, msg_if_missing: str) -> None:
    if not path.exists():
        raise HTTPException(status_code=400, detail=msg_if_missing)

# ------------ routes ------------
@app.get("/")
async def root():
    return {
        "message": "Agentic Tagging System API",
        "endpoints": {
            "generate_techspec": "POST /generate-techspec",
            "suggest_tagging": "POST /suggest-tagging",
            "apply_tagging": "POST /apply-tagging",
            "rollback_changes": "POST /rollback-changes",
            "get_tagging_markdown": "GET /tagging-markdown",
            "health": "GET /health",
            "status": "GET /status",
        },
    }

@app.post("/generate-techspec")
async def generate_techspec(request: TechSpecRequest):
    """
    Generate TechSpec by running core/techSpecGenerate.py with provided inputs.
    """
    try:
        logger.info("Generating TechSpec")

        # resolve AC file path and validate
        # ac_path = Path(request.ac_local_file)
        # if not ac_path.is_absolute():
        #     ac_path = (BASE_DIR / ac_path).resolve()
        # if not ac_path.exists():
        #     raise HTTPException(status_code=400, detail=f"ac_local_file not found: {ac_path}")

        # Resolve AC source: prefer ac_text (from browser) else ac_local_file (path on server)
        if request.ac_text and request.ac_text.strip():
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            ac_path = (OUTPUTS_DIR / "ac_from_browser.txt").resolve()
            ac_path.write_text(request.ac_text, encoding="utf-8")
        elif request.ac_local_file:
            ac_path = Path(request.ac_local_file)
            if not ac_path.is_absolute():
                ac_path = (BASE_DIR / ac_path).resolve()
            if not ac_path.exists():
                raise HTTPException(status_code=400, detail=f"ac_local_file not found: {ac_path}")
        else:
            raise HTTPException(status_code=400, detail="Provide either ac_text or ac_local_file.")

        # ensure output folder exists & tell script where to write
        TECHSPEC_XLSX.parent.mkdir(parents=True, exist_ok=True)
        env_vars = {
            # "REPO_PATH": request.repo_path,
            "AC_LOCAL_FILE": str(ac_path),
            "FIGMA_FILE_URL": request.figma_file_url,
            # "TECHSPEC_PATH": str(TECHSPEC_XLSX),
        }

        result = await run_python_script(SCRIPT_TECHSPEC, env_vars=env_vars, cwd=CORE_DIR)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"TechSpec generation failed: {result.get('stderr') or result.get('error') or 'Unknown error'}",
            )

        if TECHSPEC_XLSX.exists():
            return JSONResponse(content={
                "status": "success",
                "message": "TechSpec generated successfully",
                "output_path": str(TECHSPEC_XLSX),
                "file_size": TECHSPEC_XLSX.stat().st_size,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "TechSpec generation completed but output file not found",
                    "expected_path": str(TECHSPEC_XLSX),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("generate_techspec error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    
@app.get("/techspec-file")
async def get_techspec_file():
    """Return the generated TechSpec Excel file."""
    try:
        require_file(TECHSPEC_XLSX, "TechSpec file not found. Please generate TechSpec first.")
        return FileResponse(
            path=str(TECHSPEC_XLSX),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="techspec.xlsx",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_techspec_file error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/suggest-tagging")
async def suggest_tagging(request: SuggestTaggingRequest):
    """
    Generate tagging files (JSON/MD) by running core/taggingSuggestion.py.
    Expects repo_url; cloning & repo scanning are handled inside the script.
    """
    try:
        logger.info("Suggesting tagging")

        # Ensure TechSpec exists first
        require_file(TECHSPEC_XLSX, "TechSpec file not found. Please generate TechSpec first.")
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

        # Prepare env for the script (NO path math here)
        env_vars = {
            "TECHSPEC_PATH": str(TECHSPEC_XLSX),
            "REPO_URL": request.repo_url,
        }
        if request.branch:
            env_vars["REPO_BRANCH"] = request.branch
        if request.clone_base:
            env_vars["CLONE_BASE"] = request.clone_base

        # Run the generator script from core/
        result = await run_python_script(SCRIPT_SUGGEST, env_vars=env_vars, cwd=CORE_DIR)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Tagging generation failed: {result.get('stderr') or result.get('error') or 'Unknown error'}",
            )

        # Collect outputs
        files_generated = {"markdown": TAGGING_MD.exists(), "json": TAGGING_JSON.exists()}
        markdown_content = TAGGING_MD.read_text(encoding="utf-8") if files_generated["markdown"] else ""

        # Optional: if your script writes the repo path it used, surface it
        repo_path_used = None
        try:
            if LAST_REPO_ROOT.exists():
                repo_path_used = LAST_REPO_ROOT.read_text(encoding="utf-8").strip()
        except Exception:
            pass

        return JSONResponse(content={
            "status": "success",
            "message": "Tagging files generated successfully",
            "files": {
                "markdown": str(TAGGING_MD) if files_generated["markdown"] else None,
                "json": str(TAGGING_JSON) if files_generated["json"] else None,
            },
            "files_generated": files_generated,
            "markdown_content": markdown_content,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "repo_url": request.repo_url,
            "repo_path_used": repo_path_used,  # may be None if your script doesn't write it
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("suggest_tagging error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/tagging-markdown")
async def get_tagging_markdown():
    """Return the generated tagging markdown content."""
    try:
        require_file(TAGGING_MD, "Tagging markdown file not found. Please generate tagging first.")
        return FileResponse(path=str(TAGGING_MD), media_type="text/markdown", filename="tagging_unified.md")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_tagging_markdown error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/apply-tagging")
async def apply_tagging():
    """
    Apply tagging to repository by running core/applyTaggingAgent.py.
    """
    try:
        logger.info("Applying tagging to repository")
        require_file(TAGGING_JSON, "Tagging JSON file not found. Please generate tagging first.")

        result = await run_python_script(SCRIPT_APPLY, cwd=CORE_DIR)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Tagging application failed: {result.get('stderr') or result.get('error') or 'Unknown error'}",
            )
        
        stdout = result.get("stdout", "") or ""
        metrics = parse_apply_stdout(stdout)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        return JSONResponse(content={
            "status": "success",
            "message": "Tagging applied successfully",
            "log_path": str(APPLY_LOG) if APPLY_LOG.exists() else None,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "metrics": metrics,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("apply_tagging error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/metrics")
def get_metrics():
    p = OUTPUTS_DIR / "metrics.json"
    if not p.exists(): raise HTTPException(404, "No metrics yet")
    import json
    return json.loads(p.read_text(encoding="utf-8"))

@app.post("/rollback-changes")
async def rollback_changes(request: RollbackRequest):
    """
    Thin wrapper: pass REPO_URL or REPO_CLONED_PATH to core/rollback_changes.py.
    The script figures out the actual folder and does the work.
    """
    try:
        logger.info("Rolling back changes (pass-through)")

        env_vars = {
            "DELETE_BACKUPS": "1" if request.delete_backups else "0",
        }
        if request.repo_cloned_path:
            env_vars["REPO_CLONED_PATH"] = request.repo_cloned_path
        if request.repo_url:
            env_vars["REPO_URL"] = request.repo_url
        # pass CLONE_BASE through if set so script derives the same path layout
        if "CLONE_BASE" in os.environ:
            env_vars["CLONE_BASE"] = os.environ["CLONE_BASE"]

        # Let the script handle path resolution and validation
        result = await run_python_script(SCRIPT_ROLLBACK, env_vars=env_vars, cwd=CORE_DIR)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Rollback failed: {result.get('stderr') or result.get('error') or 'Unknown error'}",
            )

        return JSONResponse(content={
            "status": "success",
            "message": "Changes rolled back successfully",
            "deleted_backups": request.delete_backups,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("rollback_changes error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agentic-tagging-system",
        "files": {
            "techspec_exists": TECHSPEC_XLSX.exists(),
            "tagging_md_exists": TAGGING_MD.exists(),
            "tagging_json_exists": TAGGING_JSON.exists(),
            "apply_log_exists": APPLY_LOG.exists(),
        },
    }

@app.get("/status")
async def get_status():
    """Get current system status and available files."""
    return {
        "system_status": "running",
        "workflow_files": {
            "techspec": {
                "path": str(TECHSPEC_XLSX),
                "exists": TECHSPEC_XLSX.exists(),
                "size": TECHSPEC_XLSX.stat().st_size if TECHSPEC_XLSX.exists() else 0,
            },
            "tagging_markdown": {
                "path": str(TAGGING_MD),
                "exists": TAGGING_MD.exists(),
                "size": TAGGING_MD.stat().st_size if TAGGING_MD.exists() else 0,
            },
            "tagging_json": {
                "path": str(TAGGING_JSON),
                "exists": TAGGING_JSON.exists(),
                "size": TAGGING_JSON.stat().st_size if TAGGING_JSON.exists() else 0,
            },
            "apply_log": {
                "path": str(APPLY_LOG),
                "exists": APPLY_LOG.exists(),
                "size": APPLY_LOG.stat().st_size if APPLY_LOG.exists() else 0,
            },
        },
    }

# added 9/17/2025
BACKUP_SUFFIX = ".taggingai.bak"  # keep it simple: one suffix

def _read_text_any(p: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try: return p.read_text(encoding=enc, errors="replace")
        except Exception: continue
    return p.read_bytes().decode("utf-8", errors="replace")

def _require_repo_root() -> Path:
    if not LAST_REPO_ROOT.exists():
        raise HTTPException(
            status_code=400,
            detail="Repo root not set. Run /suggest-tagging with a valid repo_path first."
        )
    root = Path(LAST_REPO_ROOT.read_text(encoding="utf-8").strip()).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Stored repo root is invalid: {root}")
    return root

def _discover_pairs(root: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for bak in root.rglob(f"*{BACKUP_SUFFIX}"):
        new_p = bak.with_name(bak.name[:-len(BACKUP_SUFFIX)])
        if new_p.exists() and new_p.is_file():
            pairs.append((bak, new_p))
    pairs.sort(key=lambda ab: ab[1].stat().st_mtime, reverse=True)
    return pairs

@app.get("/view-difference")
def diff_data():
    """
    Returns JSON with all diffs under LAST_REPO_ROOT.
    Each item has: old (backup path), new (current path), diff (unified text).
    """
    repo_root = _require_repo_root()
    pairs = _discover_pairs(repo_root)
    if not pairs:
        raise HTTPException(status_code=404, detail=f"No differences found under {repo_root}.")

    items = []
    for old_p, new_p in pairs:
        old_lines = _read_text_any(old_p).splitlines(False)
        new_lines = _read_text_any(new_p).splitlines(False)
        udiff = "\n".join(
            difflib.unified_diff(
                old_lines, new_lines,
                fromfile=str(old_p), tofile=str(new_p),
                n=3, lineterm=""
            )
        )
        items.append({"old": str(old_p), "new": str(new_p), "diff": udiff})

    return {"repo_root": str(repo_root), "count": len(items), "items": items}

# ended


# added 9/18/2025
@app.get("/figma-image")
async def get_figma_image():
    """
    Return the latest Figma screenshot produced during TechSpec generation.
    """
    try:
        require_file(FIGMA_PNG, "Figma screenshot not found. Please generate TechSpec first.")
        # Add cache-busting in the frontend with ?t=Date.now()
        return FileResponse(path=str(FIGMA_PNG), media_type="image/png", filename="figma_screen.png")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_figma_image error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
# ended


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
