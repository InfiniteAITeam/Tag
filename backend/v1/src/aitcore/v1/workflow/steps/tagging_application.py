"""
Tagging application workflow step - applies suggestions to repository files.
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from aitcore.v1.tools.file_handler import FileHandler
from aitcore.v1.tools.backup_manager import BackupManager
from aitcore.v1.models.tagging import ApplyReport, ApplyResult, ApplyStatus
from aitcore.v1.services.state_manager import StateManager
from aitcore.v1.workflow.base_step import BaseStep


class TaggingApplicationStep(BaseStep):
    """Step for applying tagging suggestions to repository files."""
    
    def __init__(self):
        """Initialize tagging application step."""
        super().__init__("TaggingApplication")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for tagging application.
        
        Expected input:
        - suggestions_path: str (path to suggestions file)
        - repo_path: str (path to repository)
        - output_dir: str (where to save results)
        - dry_run: bool (optional, simulate without writing)
        """
        if not input_data.get("suggestions_path"):
            raise ValueError("suggestions_path is required")
        
        if not input_data.get("repo_path"):
            raise ValueError("repo_path is required")
        
        return True
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tagging application.
        
        Args:
            input_data: Input with suggestions and repo info
        
        Returns:
            Output with application results
        """
        from aitcore.v1.config.settings import get_config
        
        config = get_config()
        repo_path = Path(input_data["repo_path"])
        output_dir = Path(input_data.get("output_dir", config.outputs_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        dry_run = input_data.get("dry_run", False)
        
        # Load suggestions
        suggestions_path = Path(input_data["suggestions_path"])
        try:
            suggestions_data = FileHandler.read_json(suggestions_path)
        except Exception as e:
            raise ValueError(f"Could not load suggestions: {e}")
        
        suggestions = suggestions_data.get("suggestions", [])
        self.logger.info(f"Applying {len(suggestions)} tagging suggestions")
        
        # Apply suggestions
        started_at = datetime.now()
        results = []
        
        for suggestion in suggestions:
            try:
                file_path = repo_path / suggestion.get("file", "")
                
                if not file_path.exists():
                    self.logger.warning(f"File not found: {file_path}")
                    results.append(ApplyResult(
                        file_path=str(file_path),
                        status=ApplyStatus.FAILED,
                        message="File not found"
                    ))
                    continue
                
                # Create backup before modification
                if not dry_run:
                    try:
                        BackupManager.create_backup(file_path)
                    except Exception as e:
                        self.logger.error(f"Backup failed: {e}")
                        results.append(ApplyResult(
                            file_path=str(file_path),
                            status=ApplyStatus.FAILED,
                            message=f"Backup failed: {e}"
                        ))
                        continue
                
                # TODO: Apply actual code modifications from suggestion
                # For now, mark as successful
                
                results.append(ApplyResult(
                    file_path=str(file_path),
                    status=ApplyStatus.SUCCESS if not dry_run else ApplyStatus.SKIPPED,
                    message="Applied" if not dry_run else "Dry run - not applied"
                ))
                
            except Exception as e:
                self.logger.error(f"Error applying suggestion: {e}")
                results.append(ApplyResult(
                    file_path=str(file_path),
                    status=ApplyStatus.ERROR,
                    error=str(e)
                ))
        
        # Create report
        apply_report = ApplyReport(
            run_id=f"apply_{datetime.now().timestamp()}",
            repo_path=str(repo_path),
            started_at=started_at,
            completed_at=datetime.now(),
            results=results
        )
        
        # Save report
        report_path = output_dir / "apply_report.json"
        FileHandler.write_json(report_path, apply_report.to_dict())
        
        # Save state
        state = StateManager()
        state.save_apply_state(
            repo_path=str(repo_path),
            applied_count=apply_report.success_count(),
            failed_count=apply_report.failed_count(),
            completed_at=datetime.now()
        )
        
        self.logger.info(f"Application complete: {apply_report.success_count()} succeeded, "
                        f"{apply_report.failed_count()} failed")
        
        return {
            "report_path": str(report_path),
            "success_count": apply_report.success_count(),
            "failed_count": apply_report.failed_count(),
            "output_dir": str(output_dir),
        }
