"""
Repository service for git and repository operations.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from ..exceptions import RepoOperationError
from ..models.tagging import RepositoryInfo
from ..utils.validators import validate_github_url
from ..utils.logger import get_logger
from ..config.settings import get_config

logger = get_logger(__name__)


class GitService:
    """Service for Git repository operations."""
    
    @staticmethod
    def _run_git_command(cmd: list[str], cwd: Optional[str] = None) -> str:
        """
        Execute a git command.
        
        Args:
            cmd: Command arguments (without 'git')
            cwd: Working directory
        
        Returns:
            Command output
        
        Raises:
            RepoOperationError: If command fails
        """
        try:
            result = subprocess.run(
                ["git"] + cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RepoOperationError(f"Git command failed: {e.stderr}")
        except Exception as e:
            raise RepoOperationError(f"Git operation error: {e}")
    
    @staticmethod
    def get_default_branch(owner: str, repo: str) -> str:
        """
        Get the default branch for a GitHub repository via API.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Default branch name
        
        Raises:
            RepoOperationError: If API call fails
        """
        try:
            import requests
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("default_branch", "main")
        except Exception as e:
            logger.warning(f"Could not fetch default branch: {e}")
            return "main"  # Fallback to main
    
    @staticmethod
    def clone_repository(
        repo_url: str,
        clone_path: str | Path,
        branch: Optional[str] = None,
        depth: int = 1
    ) -> Path:
        """
        Clone a GitHub repository.
        
        Args:
            repo_url: Repository URL
            clone_path: Local path for clone
            branch: Branch to clone (None = default)
            depth: Clone depth for shallow clone
        
        Returns:
            Path to cloned repository
        
        Raises:
            RepoOperationError: If clone fails
        """
        clone_path = Path(clone_path)
        
        # Validate URL
        try:
            owner, repo_name = validate_github_url(repo_url)
        except Exception as e:
            raise RepoOperationError(f"Invalid repository URL: {e}")
        
        # Get default branch if not specified
        if branch is None:
            branch = GitService.get_default_branch(owner, repo_name)
        
        # Clean up existing clone
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)
        
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cmd = [
                "clone",
                "--depth", str(depth),
                "--branch", branch,
                repo_url,
                str(clone_path)
            ]
            GitService._run_git_command(cmd)
            logger.info(f"Cloned {repo_url} to {clone_path}")
            return clone_path.resolve()
        except Exception as e:
            raise RepoOperationError(f"Failed to clone repository: {e}")


class RepositoryService:
    """Service for repository scanning and analysis."""
    
    @staticmethod
    def scan_repository(repo_path: str | Path) -> RepositoryInfo:
        """
        Scan a repository for information.
        
        Args:
            repo_path: Path to repository
        
        Returns:
            RepositoryInfo object
        
        Raises:
            RepoOperationError: If repository is invalid
        """
        repo = Path(repo_path)
        
        if not repo.exists() or not repo.is_dir():
            raise RepoOperationError(f"Repository not found: {repo}")
        
        # Count files
        total_files = sum(1 for _ in repo.rglob("*") if _.is_file())
        
        # Count React files
        from ..tools.file_handler import FileHandler
        react_files = FileHandler.find_react_files(repo)
        
        # Try to get git info
        url = ""
        branch = "unknown"
        try:
            url = GitService._run_git_command(["config", "--get", "remote.origin.url"], cwd=str(repo))
            branch = GitService._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=str(repo))
        except Exception as e:
            logger.warning(f"Could not get git info: {e}")
        
        # Extract owner/repo from URL if possible
        owner = "unknown"
        name = repo.name
        if url:
            try:
                from ..utils.validators import validate_github_url
                owner, name = validate_github_url(url)
            except Exception:
                pass
        
        return RepositoryInfo(
            url=url,
            owner=owner,
            name=name,
            branch=branch,
            clone_path=str(repo),
            cloned_at=datetime.now(),
            file_count=total_files,
            react_file_count=len(react_files)
        )
