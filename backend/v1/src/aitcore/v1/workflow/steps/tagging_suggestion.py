"""
Tagging suggestion workflow step.
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from aitcore.v1.tools.file_handler import FileHandler
from aitcore.v1.tools.openai_client import OpenAIClient
from aitcore.v1.services.repo_service import GitService, RepositoryService
from aitcore.v1.services.state_manager import StateManager
from aitcore.v1.utils.validators import validate_file_exists, validate_github_url
from aitcore.v1.exceptions import LLMError
from aitcore.v1.workflow.base_step import BaseStep


class TaggingSuggestionStep(BaseStep):
    """Step for generating tagging suggestions based on TechSpec and repository code."""
    
    def __init__(self):
        """Initialize tagging suggestion step."""
        super().__init__("TaggingSuggestion")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for tagging suggestion.
        
        Expected input:
        - techspec_path: str (path to TechSpec file)
        - repo_url or repo_path: str (repository URL or local path)
        - branch: str (optional, git branch)
        - clone_base: str (optional, where to clone repo)
        - output_dir: str (where to save suggestions)
        """
        if not input_data.get("techspec_path"):
            raise ValueError("techspec_path is required")
        
        has_url = "repo_url" in input_data and input_data["repo_url"]
        has_path = "repo_path" in input_data and input_data["repo_path"]
        
        if not (has_url or has_path):
            raise ValueError("Either repo_url or repo_path must be provided")
        
        return True
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tagging suggestion generation.
        
        Args:
            input_data: Input configuration with techspec and repo info
        
        Returns:
            Output with suggestions file path and metadata
        """
        from aitcore.v1.config.settings import get_config
        
        config = get_config()
        output_dir = Path(input_data.get("output_dir", config.outputs_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get or clone repository
        repo_path = None
        if "repo_path" in input_data:
            repo_path = Path(input_data["repo_path"])
        elif "repo_url" in input_data:
            # Clone repository
            clone_base = Path(input_data.get("clone_base", config.clone_base_dir))
            repo_name = input_data["repo_url"].split("/")[-1].replace(".git", "")
            repo_path = GitService.clone_repository(
                input_data["repo_url"],
                clone_base / repo_name,
                branch=input_data.get("branch")
            )
        
        if not repo_path:
            raise ValueError("Could not determine repository path")
        
        # Scan repository
        repo_info = RepositoryService.scan_repository(repo_path)
        self.logger.info(f"Scanned repo: {repo_info.react_file_count} React files")
        
        # Find React files
        react_files = FileHandler.find_react_files(repo_path)
        
        # TODO: Integrate with actual suggestion generation from tagging_agent.py
        # For now, create placeholder suggestions structure
        
        suggestions = {
            "repo_path": str(repo_path),
            "repo_info": repo_info.to_dict(),
            "react_files": react_files[:10],  # Sample first 10 files
            "total_files": len(react_files),
            "suggestions": [],  # Will be filled by agent
        }
        
        # Save suggestions
        suggestions_path = output_dir / "tagging_suggestions.json"
        FileHandler.write_json(suggestions_path, suggestions)
        
        # Save state
        state = StateManager()
        state.save_suggestions_state(
            spec_file=input_data.get("techspec_path", "unknown"),
            repo_path=str(repo_path),
            suggestion_count=0,
            generated_at=datetime.now()
        )
        
        self.logger.info(f"Tagging suggestions prepared at {suggestions_path}")
        
        return {
            "suggestions_path": str(suggestions_path),
            "repo_path": str(repo_path),
            "react_files_count": len(react_files),
            "output_dir": str(output_dir),
        }
