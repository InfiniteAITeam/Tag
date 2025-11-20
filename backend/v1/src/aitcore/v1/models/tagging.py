"""
Data models for tagging application, diff reports, and repository information.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ApplyStatus(str, Enum):
    """Status of a tagging application result."""
    SUCCESS = "success"
    SKIPPED = "skipped"  # Already applied
    FAILED = "failed"
    ERROR = "error"


@dataclass
class ApplyResult:
    """Result of applying tagging to a single file."""
    file_path: str
    status: ApplyStatus
    message: Optional[str] = None
    backup_path: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "status": self.status.value,
            "message": self.message,
            "backup_path": self.backup_path,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "error": self.error,
        }


@dataclass
class ApplyReport:
    """Complete report of a tagging application run."""
    run_id: str
    repo_path: str
    started_at: datetime
    completed_at: datetime
    results: List[ApplyResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def success_count(self) -> int:
        """Get number of successful applications."""
        return sum(1 for r in self.results if r.status == ApplyStatus.SUCCESS)
    
    def failed_count(self) -> int:
        """Get number of failed applications."""
        return sum(1 for r in self.results if r.status == ApplyStatus.FAILED)
    
    def skipped_count(self) -> int:
        """Get number of skipped applications."""
        return sum(1 for r in self.results if r.status == ApplyStatus.SKIPPED)
    
    def total_lines_added(self) -> int:
        """Get total lines added across all files."""
        return sum(r.lines_added for r in self.results)
    
    def total_lines_removed(self) -> int:
        """Get total lines removed across all files."""
        return sum(r.lines_removed for r in self.results)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "repo_path": self.repo_path,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "success_count": self.success_count(),
            "failed_count": self.failed_count(),
            "skipped_count": self.skipped_count(),
            "total_lines_added": self.total_lines_added(),
            "total_lines_removed": self.total_lines_removed(),
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata,
        }


@dataclass
class FileDiff:
    """Diff information for a single file."""
    backup_path: str
    current_path: str
    relative_path: str
    diff_text: str
    lines_added: int = 0
    lines_removed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_path": self.backup_path,
            "current_path": self.current_path,
            "relative_path": self.relative_path,
            "diff_text": self.diff_text,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
        }


@dataclass
class DiffReport:
    """Complete diff report for a repository."""
    repo_path: str
    generated_at: datetime
    diffs: List[FileDiff] = field(default_factory=list)
    
    def total_files(self) -> int:
        """Get number of files with diffs."""
        return len(self.diffs)
    
    def total_lines_added(self) -> int:
        """Get total lines added."""
        return sum(d.lines_added for d in self.diffs)
    
    def total_lines_removed(self) -> int:
        """Get total lines removed."""
        return sum(d.lines_removed for d in self.diffs)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "generated_at": self.generated_at.isoformat(),
            "total_files": self.total_files(),
            "total_lines_added": self.total_lines_added(),
            "total_lines_removed": self.total_lines_removed(),
            "diffs": [d.to_dict() for d in self.diffs],
        }


@dataclass
class RepositoryInfo:
    """Information about a repository."""
    url: str
    owner: str
    name: str
    branch: str
    clone_path: str
    cloned_at: datetime
    file_count: int = 0
    react_file_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "owner": self.owner,
            "name": self.name,
            "branch": self.branch,
            "clone_path": self.clone_path,
            "cloned_at": self.cloned_at.isoformat(),
            "file_count": self.file_count,
            "react_file_count": self.react_file_count,
            "metadata": self.metadata,
        }


@dataclass
class RollbackReport:
    """Report of a rollback operation."""
    run_id: str
    repo_path: str
    started_at: datetime
    completed_at: datetime
    restored_count: int = 0
    deleted_backup_count: int = 0
    errors: List[str] = field(default_factory=list)
    
    def success(self) -> bool:
        """Whether rollback was completely successful."""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "repo_path": self.repo_path,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "restored_count": self.restored_count,
            "deleted_backup_count": self.deleted_backup_count,
            "success": self.success(),
            "errors": self.errors,
        }
