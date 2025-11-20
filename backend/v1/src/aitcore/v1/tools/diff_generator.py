"""
Diff generation and comparison utilities.
"""

import difflib
from pathlib import Path
from typing import List, Tuple, Optional
from ..exceptions import FileOperationError
from ..models.tagging import FileDiff, DiffReport
from ..utils.constants import DIFF_CONTEXT_LINES
from ..utils.logger import get_logger
from .file_handler import FileHandler

logger = get_logger(__name__)


class DiffGenerator:
    """Generate and manage file differences."""
    
    @staticmethod
    def _read_lines(file_path: str | Path) -> List[str]:
        """Read file lines safely."""
        try:
            content = FileHandler.read_file(file_path)
            return content.splitlines(keepends=False)
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return []
    
    @staticmethod
    def generate_unified_diff(
        old_path: str | Path,
        new_path: str | Path,
        context_lines: int = DIFF_CONTEXT_LINES
    ) -> str:
        """
        Generate unified diff between two files.
        
        Args:
            old_path: Path to old file
            new_path: Path to new file
            context_lines: Number of context lines
        
        Returns:
            Unified diff as string
        """
        old_lines = DiffGenerator._read_lines(old_path)
        new_lines = DiffGenerator._read_lines(new_path)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(old_path),
            tofile=str(new_path),
            n=context_lines,
            lineterm=""
        )
        
        return "\n".join(diff)
    
    @staticmethod
    def count_diff_changes(diff_text: str) -> Tuple[int, int]:
        """
        Count added and removed lines in a diff.
        
        Args:
            diff_text: Unified diff text
        
        Returns:
            Tuple of (lines_added, lines_removed)
        """
        added = 0
        removed = 0
        
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        
        return added, removed
    
    @staticmethod
    def create_file_diff(
        backup_path: str | Path,
        current_path: str | Path,
        repo_root: Optional[str | Path] = None
    ) -> FileDiff:
        """
        Create a FileDiff object between backup and current files.
        
        Args:
            backup_path: Path to backup file
            current_path: Path to current file
            repo_root: Repository root for relative paths
        
        Returns:
            FileDiff object
        """
        diff_text = DiffGenerator.generate_unified_diff(backup_path, current_path)
        added, removed = DiffGenerator.count_diff_changes(diff_text)
        
        # Calculate relative path
        relative_path = str(current_path)
        if repo_root:
            try:
                relative_path = str(Path(current_path).relative_to(repo_root))
            except ValueError:
                pass
        
        return FileDiff(
            backup_path=str(backup_path),
            current_path=str(current_path),
            relative_path=relative_path,
            diff_text=diff_text,
            lines_added=added,
            lines_removed=removed
        )
    
    @staticmethod
    def find_backup_pairs(
        repo_root: str | Path,
        backup_suffix: str = ".taggingai.bak"
    ) -> List[Tuple[Path, Path]]:
        """
        Find all backup/current file pairs in a repository.
        
        Args:
            repo_root: Repository root path
            backup_suffix: Backup file suffix
        
        Returns:
            List of (backup_path, current_path) tuples
        """
        repo = Path(repo_root)
        pairs: List[Tuple[Path, Path]] = []
        
        try:
            for backup in repo.rglob(f"*{backup_suffix}"):
                if not backup.is_file():
                    continue
                
                # Derive current path by removing suffix
                current = backup.with_name(
                    backup.name[:-len(backup_suffix)]
                )
                
                if current.exists() and current.is_file():
                    pairs.append((backup, current))
        
        except Exception as e:
            logger.error(f"Error finding backup pairs in {repo}: {e}")
        
        # Sort by modification time (newest first)
        pairs.sort(key=lambda p: p[1].stat().st_mtime, reverse=True)
        return pairs
    
    @staticmethod
    def generate_diff_report(
        repo_root: str | Path,
        backup_suffix: str = ".taggingai.bak"
    ) -> DiffReport:
        """
        Generate a complete diff report for a repository.
        
        Args:
            repo_root: Repository root path
            backup_suffix: Backup file suffix
        
        Returns:
            DiffReport object
        """
        from datetime import datetime
        
        repo = Path(repo_root)
        pairs = DiffGenerator.find_backup_pairs(repo, backup_suffix)
        
        diffs = []
        for backup, current in pairs:
            try:
                diff = DiffGenerator.create_file_diff(backup, current, repo)
                diffs.append(diff)
            except Exception as e:
                logger.error(f"Error generating diff for {backup}: {e}")
        
        return DiffReport(
            repo_path=str(repo),
            generated_at=datetime.now(),
            diffs=diffs
        )
