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

def normalize_repo_url(repo_url: str) -> tuple[str, str]:
    """
    Accepts:
      - https://github.com/<owner>/<repo>
      - https://github.com/<owner>/<repo>.git
      - https://github.com/<owner>/<repo>/tree/<branch>
    Returns: (owner, repo)
    """
    repo_url = repo_url.strip()
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/[^/]+)?/?$", repo_url)
    if not m:
        raise ValueError(f"Invalid GitHub repo URL format: {repo_url!r}")
    return m.group(1), m.group(2)

def get_default_branch(owner: str, repo: str) -> str:
    """Ask GitHub for the repo’s default branch (no auth, 60 req/hr IP limit)."""
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=30)
    r.raise_for_status()
    branch = r.json().get("default_branch") or "main"
    log(f"Default branch for {owner}/{repo} is {branch}")
    return branch

def clone_repo(repo_url: str, local_dir: str, branch: Optional[str] = None) -> Path:
    """
    Clones a public GitHub repo into local_dir (which must not exist or must be empty).
    If branch is None, uses the repo’s default branch.
    """
    owner, repo = normalize_repo_url(repo_url)
    if branch is None:
        branch = get_default_branch(owner, repo)

    dest = Path(local_dir).expanduser().resolve()

    if dest.exists():
      shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    # git clone into an empty existing directory is allowed
    log(f"Cloning {repo_url} (branch: {branch}) into {dest}")
    run_command(["git", "clone", "--depth", "1", "--branch", branch, f"https://github.com/{owner}/{repo}.git", str(dest)])
    log(f"Clone complete at: {dest}")
    return dest

def clone_to_fixed_location(repo_url: str) -> Path:
    owner, repo = normalize_repo_url(repo_url)  
       # you already have this helper
    dest = (CLONE_BASE/repo).resolve()
    # optional: clean existing
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    return clone_repo(repo_url, str(dest))  

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
