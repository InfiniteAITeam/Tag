#!/usr/bin/env python3
import os
import re
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv


load_dotenv()
val = os.getenv("CLONE_BASE")

if not val:
    raise RuntimeError(
        "CLONE_BASE is not set. Add `CLONE_BASE=${HOME}/ATTagger/Test` (or an absolute path) to your .env"
    )

# expand ${HOME} and ~, then resolve
CLONE_BASE = Path(os.path.expandvars(val)).expanduser().resolve()

# CLONE_BASE = (Path.home() / "ATTagger" / "Test").expanduser().resolve()

# ---------------- logging setup ----------------
LOG_FILE = "clone_repo.log"
logger = logging.getLogger("analyze_repo")
logger.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

# console
_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(_fmt)
logger.addHandler(_ch)

# file
_fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
_fh.setLevel(logging.INFO)
_fh.setFormatter(_fmt)
logger.addHandler(_fh)

def log(msg: str) -> None:
    logger.info(msg)

# ---------------- utils ----------------
def run_command(command, cwd: Optional[str] = None, shell: bool = False, env=None) -> str:
    """
    Runs a shell command and logs its output. Raises on nonzero exit.
    Returns the command's stdout as a string.
    """
    if shell:
        # When shell=True, command should be a single string; we join here for convenience.
        command_str = " ".join(command) if isinstance(command, (list, tuple)) else str(command)
        log(f"Running (shell): {command_str}  | cwd={cwd or os.getcwd()}")
        result = subprocess.run(
            command_str,
            capture_output=True, text=True,
            cwd=cwd, check=True, shell=True, env=env, executable="/bin/bash"
        )
    else:
        if not isinstance(command, (list, tuple)):
            raise TypeError("run_command(command=...) must be a list/tuple when shell=False")
        log(f"Running: {' '.join(command)}  | cwd={cwd or os.getcwd()}")
        result = subprocess.run(
            command, capture_output=True, text=True,
            cwd=cwd, check=True, env=env
        )
    if result.stdout:
        log(f"STDOUT:\n{result.stdout.strip()}")
    if result.stderr:
        # stderr can contain warnings even on success
        log(f"STDERR:\n{result.stderr.strip()}")
    return result.stdout

def normalize_repo_url(repo_url: str) -> tuple[str, str, str]:
    """
    Accepts:
      - https://github.com/<owner>/<repo>
      - https://github.com/<owner>/<repo>.git
      - https://github.com/<owner>/<repo>/tree/<branch>
      - https://gitlab.com/<owner>/<repo>
      - https://gitlab.verizon.com/<group>/<repo>
      - Any git repo URL with .git extension
    
    Returns: (owner, repo, git_host)
    """
    repo_url = repo_url.strip()
    
    # Try GitHub format
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/[^/]+)?/?$", repo_url)
    if m:
        return m.group(1), m.group(2), "github"
    
    # Try GitLab format (gitlab.com or custom GitLab instance)
    m = re.match(r"https?://([^/]+)/(.+?)/([^/]+?)(?:\.git)?(?:/tree/[^/]+)?/?$", repo_url)
    if m:
        host, owner, repo = m.group(1), m.group(2), m.group(3)
        if "gitlab" in host.lower():
            return owner, repo, "gitlab"
        # Also support any git host
        return owner, repo, "git"
    
    raise ValueError(f"Invalid repository URL format: {repo_url!r}")

def get_default_branch(owner: str, repo: str, git_host: str = "github") -> str:
    """
    Get the default branch for a repository.
    Supports GitHub and GitLab APIs.
    Falls back to 'main' if API call fails.
    """
    try:
        if git_host == "github":
            r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=30)
            r.raise_for_status()
            branch = r.json().get("default_branch") or "main"
        elif git_host == "gitlab":
            # GitLab project ID is owner/repo URL-encoded
            project_id = f"{owner}%2F{repo}"
            r = requests.get(f"https://gitlab.com/api/v4/projects/{project_id}", timeout=30)
            r.raise_for_status()
            branch = r.json().get("default_branch") or "main"
        else:
            # For other git hosts, default to main
            branch = "main"
        
        log(f"Default branch for {owner}/{repo} is {branch}")
        return branch
    except Exception as e:
        log(f"Could not determine default branch, using 'main': {e}")
        return "main"

def clone_repo(repo_url: str, local_dir: str, branch: Optional[str] = None) -> Path:
    """
    Clones a public GitHub or GitLab repo into local_dir (which must not exist or must be empty).
    If branch is None, uses the repo's default branch.
    """
    owner, repo, git_host = normalize_repo_url(repo_url)
    if branch is None:
        branch = get_default_branch(owner, repo, git_host)

    dest = Path(local_dir).expanduser().resolve()

    if dest.exists():
      shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    # git clone into an empty existing directory is allowed
    log(f"Cloning {repo_url} (branch: {branch}) into {dest}")
    run_command(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(dest)])
    log(f"Clone complete at: {dest}")
    return dest

def setup_tagging_framework(repo_path: Path, tagging_source_dir: Optional[Path] = None) -> Path:
    """
    Setup tagging framework in cloned repo:
    1. Create src/pages/ExpressStore/Tagging/ if it doesn't exist
    2. Copy index.js and dlStructure.js from tagging_source_dir
    
    Args:
        repo_path: Path to cloned repository
        tagging_source_dir: Path to source directory containing tagging files (index.js, dlStructure.js)
                           If None, looks in the current project root
    
    Returns:
        Path to the created Tagging folder
    """
    tagging_target = repo_path / "src" / "pages" / "ExpressStore" / "Tagging"
    
    # Create Tagging folder if it doesn't exist
    if not tagging_target.exists():
        tagging_target.mkdir(parents=True, exist_ok=True)
        log(f"Created Tagging folder: {tagging_target}")
    
    # Determine source directory
    if tagging_source_dir is None:
        # Look for tagging files in the project root or core directory
        project_root = Path(__file__).resolve().parent.parent
        tagging_source_dir = project_root
    
    tagging_source_dir = Path(tagging_source_dir).resolve()
    
    # Files to copy
    tagging_files = ["index.js", "dlStructure.js"]
    
    for file_name in tagging_files:
        source_file = tagging_source_dir / file_name
        target_file = tagging_target / file_name
        
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            log(f"Copied tagging file: {source_file} → {target_file}")
        else:
            log(f"Warning: Tagging file not found: {source_file}")
    
    log(f"Tagging framework setup complete at: {tagging_target}")
    return tagging_target

def clone_to_fixed_location(repo_url: str, setup_tagging: bool = True, tagging_source_dir: Optional[str] = None) -> Path:
    """
    Clone repository to fixed location and optionally setup tagging framework.
    
    Args:
        repo_url: GitHub or GitLab repository URL
        setup_tagging: Whether to setup tagging framework after cloning (default: True)
        tagging_source_dir: Path to directory containing tagging files (optional)
    
    Returns:
        Path to cloned repository
    """
    owner, repo, git_host = normalize_repo_url(repo_url)
    dest = (CLONE_BASE / repo).resolve()
    
    # optional: clean existing
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # Clone the repository
    cloned_path = clone_repo(repo_url, str(dest))
    
    # Setup tagging framework if requested
    if setup_tagging:
        tagging_source = Path(tagging_source_dir) if tagging_source_dir else None
        setup_tagging_framework(cloned_path, tagging_source)
    
    return cloned_path  

# ---------------- CLI ----------------
def _usage() -> None:
    print("Usage: python cloneRepo.py <github_repo_url> ", file=sys.stderr)
    print("Example:", file=sys.stderr)
    print("  python cloneRepo.py https://github.com/SushilaGadal91/ResidentPortal", file=sys.stderr)

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            _usage()
            sys.exit(2)
        repo_url = sys.argv[1]
        # local_dir = sys.argv[2]
        result = clone_to_fixed_location(repo_url)
        # print(json.dumps(result, indent=2))
        print(f"\nLogs written to: {LOG_FILE}")
    except Exception as e:
        logger.exception("Fatal error")
        print(f"\nERROR: {e}", file=sys.stderr)
        print(f"See logs: {LOG_FILE}", file=sys.stderr)
        sys.exit(1)
