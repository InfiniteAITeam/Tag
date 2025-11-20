"""
Application agent - applies tagging code changes to repository files.
"""

from typing import Dict, Any, List
from pathlib import Path
from ..tools.file_handler import FileHandler
from .base_agent import BaseAgent


class ApplicationAgent(BaseAgent):
    """Agent for applying tagging code modifications to files."""
    
    def __init__(self):
        """Initialize application agent."""
        super().__init__("ApplicationAgent", use_llm=True)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply tagging suggestions to repository files.
        
        Expected input:
        - suggestions: List[Dict] (tagging suggestions)
        - repo_path: str (repository path)
        - dry_run: bool (optional, simulate without writing)
        
        Returns:
            Application results with code modifications
        """
        self.log_step("Starting code application")
        
        suggestions = input_data.get("suggestions", [])
        repo_path = Path(input_data.get("repo_path", "."))
        dry_run = input_data.get("dry_run", False)
        
        applied_count = 0
        failed_count = 0
        modifications: List[Dict[str, Any]] = []
        
        # TODO: Implement actual code modification:
        # 1. Parse suggestion for target location
        # 2. Use LLM to generate code modification
        # 3. Apply to file or create diff
        # 4. Handle merge conflicts
        
        for suggestion in suggestions:
            try:
                file_path = repo_path / suggestion.get("file", "")
                
                if not file_path.exists():
                    self.log_warning(f"File not found: {file_path}")
                    failed_count += 1
                    continue
                
                # Read original file
                original_content = FileHandler.read_file(file_path)
                
                # Generate modifications using LLM if available
                modified_content = original_content
                if self.llm_client:
                    try:
                        code_gen = self.llm_client.generate_tracking_code(
                            action=suggestion.get("action", "unknown"),
                            event_name=suggestion.get("event_name", "event"),
                            params=suggestion.get("params", {}),
                            code_snippet=original_content[:500]
                        )
                        # TODO: Apply code_gen to modified_content
                    except Exception as e:
                        self.log_warning(f"LLM generation failed: {e}")
                
                # Write modifications if not dry run
                if not dry_run and modified_content != original_content:
                    FileHandler.write_file(file_path, modified_content)
                    applied_count += 1
                else:
                    applied_count += 1  # Count as applied even in dry run
                
                modifications.append({
                    "file": suggestion.get("file"),
                    "lines_added": len(modified_content.splitlines()) - len(original_content.splitlines()),
                    "status": "applied" if not dry_run else "dry_run"
                })
                
            except Exception as e:
                self.log_error(f"Error applying suggestion: {e}")
                failed_count += 1
        
        self.log_step(f"Application complete: {applied_count} applied, {failed_count} failed")
        
        return {
            "applied_count": applied_count,
            "failed_count": failed_count,
            "modifications": modifications,
            "dry_run": dry_run,
        }
