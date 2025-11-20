"""
Rollback workflow step - restores repository from backups.
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from aitcore.v1.tools.backup_manager import BackupManager
from aitcore.v1.models.tagging import RollbackReport
from aitcore.v1.services.state_manager import StateManager
from aitcore.v1.workflow.base_step import BaseStep


class RollbackStep(BaseStep):
    """Step for rolling back applied tagging changes."""
    
    def __init__(self):
        """Initialize rollback step."""
        super().__init__("Rollback")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for rollback.
        
        Expected input:
        - repo_path: str (path to repository with backups)
        - backup_suffix: str (optional, backup file suffix)
        - delete_backups: bool (optional, delete backups after restore)
        - output_dir: str (optional, where to save rollback report)
        """
        if not input_data.get("repo_path"):
            raise ValueError("repo_path is required")
        
        return True
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute rollback operation.
        
        Args:
            input_data: Input with repo path and options
        
        Returns:
            Output with rollback results
        """
        from aitcore.v1.config.settings import get_config
        from aitcore.v1.utils.constants import BACKUP_SUFFIX
        
        config = get_config()
        repo_path = Path(input_data["repo_path"])
        backup_suffix = input_data.get("backup_suffix", BACKUP_SUFFIX)
        delete_backups = input_data.get("delete_backups", False)
        output_dir = Path(input_data.get("output_dir", config.outputs_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Starting rollback for {repo_path}")
        
        # Restore all backups
        started_at = datetime.now()
        restored_count, errors = BackupManager.restore_all_backups(
            repo_path,
            backup_suffix=backup_suffix,
            delete_backups=delete_backups
        )
        
        # Cleanup remaining backups if requested
        deleted_count = 0
        if delete_backups and restored_count > 0:
            deleted_count = BackupManager.cleanup_backups(repo_path, backup_suffix)
        
        # Create rollback report
        rollback_report = RollbackReport(
            run_id=f"rollback_{datetime.now().timestamp()}",
            repo_path=str(repo_path),
            started_at=started_at,
            completed_at=datetime.now(),
            restored_count=restored_count,
            deleted_backup_count=deleted_count,
            errors=errors
        )
        
        # Save report
        from aitcore.v1.tools.file_handler import FileHandler
        report_path = output_dir / "rollback_report.json"
        FileHandler.write_json(report_path, rollback_report.to_dict())
        
        # Clear state
        state = StateManager()
        state.clear_state(StateManager.STATE_APPLY)
        state.clear_state(StateManager.STATE_SUGGESTIONS)
        
        if rollback_report.success():
            self.logger.info(f"Rollback complete: {restored_count} files restored, {deleted_count} backups deleted")
        else:
            self.logger.warning(f"Rollback complete with errors: {len(errors)} error(s)")
        
        return {
            "report_path": str(report_path),
            "restored_count": restored_count,
            "deleted_count": deleted_count,
            "errors": errors,
            "success": rollback_report.success(),
        }
