"""
State management service for persisting workflow state.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from ..exceptions import StateError, FileOperationError
from ..utils.logger import get_logger
from ..config.settings import get_config
from .repo_service import RepositoryService
from ..tools.file_handler import FileHandler

logger = get_logger(__name__)


class StateManager:
    """Manages workflow state persistence and retrieval."""
    
    # State file names
    STATE_REPO_ROOT = ".last_repo_root"
    STATE_TECHSPEC = ".techspec_state"
    STATE_SUGGESTIONS = ".suggestions_state"
    STATE_APPLY = ".apply_state"
    
    def __init__(self):
        """Initialize state manager with output directory."""
        config = get_config()
        self.state_dir = config.outputs_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_state_path(self, state_name: str) -> Path:
        """Get full path to state file."""
        return self.state_dir / state_name
    
    def save_repo_root(self, repo_path: str | Path) -> None:
        """
        Save the currently active repository root.
        
        Args:
            repo_path: Path to the repository
        
        Raises:
            StateError: If save fails
        """
        try:
            state_path = self._get_state_path(self.STATE_REPO_ROOT)
            repo_path = Path(repo_path).expanduser().resolve()
            
            # Atomic write
            tmp_path = state_path.with_suffix(state_path.suffix + ".tmp")
            tmp_path.write_text(str(repo_path), encoding="utf-8")
            tmp_path.replace(state_path)
            
            logger.info(f"Saved repo root: {repo_path}")
        except Exception as e:
            raise StateError(f"Failed to save repo root: {e}")
    
    def load_repo_root(self) -> Optional[Path]:
        """
        Load the last known repository root.
        
        Returns:
            Path to repository or None if not found
        """
        try:
            state_path = self._get_state_path(self.STATE_REPO_ROOT)
            if not state_path.exists():
                return None
            
            repo_path = Path(state_path.read_text(encoding="utf-8").strip())
            if repo_path.exists() and repo_path.is_dir():
                return repo_path
            
            logger.warning(f"Saved repo path does not exist: {repo_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load repo root: {e}")
            return None
    
    def save_state(self, state_name: str, state_data: Dict[str, Any]) -> None:
        """
        Save arbitrary state data as JSON.
        
        Args:
            state_name: State identifier (without directory)
            state_data: Data to save
        
        Raises:
            StateError: If save fails
        """
        try:
            state_path = self._get_state_path(state_name)
            FileHandler.write_json(state_path, state_data)
            logger.info(f"Saved state: {state_name}")
        except FileOperationError as e:
            raise StateError(f"Failed to save state {state_name}: {e}")
    
    def load_state(self, state_name: str) -> Optional[Dict[str, Any]]:
        """
        Load previously saved state data.
        
        Args:
            state_name: State identifier
        
        Returns:
            State dictionary or None if not found
        """
        try:
            state_path = self._get_state_path(state_name)
            if not state_path.exists():
                return None
            
            return FileHandler.read_json(state_path)
        except FileOperationError as e:
            logger.error(f"Failed to load state {state_name}: {e}")
            return None
    
    def clear_state(self, state_name: str) -> None:
        """
        Clear saved state.
        
        Args:
            state_name: State identifier
        """
        try:
            state_path = self._get_state_path(state_name)
            if state_path.exists():
                state_path.unlink()
                logger.info(f"Cleared state: {state_name}")
        except Exception as e:
            logger.error(f"Failed to clear state {state_name}: {e}")
    
    def save_techspec_state(self, spec_file: str, generated_at: datetime) -> None:
        """Save TechSpec generation state."""
        state = {
            "spec_file": str(spec_file),
            "generated_at": generated_at.isoformat(),
        }
        self.save_state(self.STATE_TECHSPEC, state)
    
    def save_suggestions_state(
        self,
        spec_file: str,
        repo_path: str,
        suggestion_count: int,
        generated_at: datetime
    ) -> None:
        """Save tagging suggestions state."""
        state = {
            "spec_file": str(spec_file),
            "repo_path": str(repo_path),
            "suggestion_count": suggestion_count,
            "generated_at": generated_at.isoformat(),
        }
        self.save_state(self.STATE_SUGGESTIONS, state)
    
    def save_apply_state(
        self,
        repo_path: str,
        applied_count: int,
        failed_count: int,
        completed_at: datetime
    ) -> None:
        """Save tagging application state."""
        state = {
            "repo_path": str(repo_path),
            "applied_count": applied_count,
            "failed_count": failed_count,
            "completed_at": completed_at.isoformat(),
        }
        self.save_state(self.STATE_APPLY, state)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get current workflow status from saved states.
        
        Returns:
            Dictionary with workflow status information
        """
        return {
            "repo_root": str(self.load_repo_root()) if self.load_repo_root() else None,
            "techspec": self.load_state(self.STATE_TECHSPEC),
            "suggestions": self.load_state(self.STATE_SUGGESTIONS),
            "apply": self.load_state(self.STATE_APPLY),
        }
