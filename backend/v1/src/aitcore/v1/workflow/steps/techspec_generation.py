"""
TechSpec generation workflow step.
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from aitcore.v1.tools.file_handler import FileHandler
from aitcore.v1.services.state_manager import StateManager
from aitcore.v1.utils.validators import validate_file_exists, validate_directory_exists
from aitcore.v1.workflow.base_step import BaseStep


class TechSpecGenerationStep(BaseStep):
    """Step for generating TechSpec from acceptance criteria and Figma designs."""
    
    def __init__(self):
        """Initialize TechSpec generation step."""
        super().__init__("TechSpecGeneration")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for TechSpec generation.
        
        Expected input:
        - figma_file_url: str (Figma file URL)
        - ac_text or ac_local_file: str (acceptance criteria)
        - output_dir: str (where to save output)
        """
        # At least one AC source required
        has_ac_text = "ac_text" in input_data and input_data["ac_text"]
        has_ac_file = "ac_local_file" in input_data and input_data["ac_local_file"]
        
        if not (has_ac_text or has_ac_file):
            raise ValueError("Either ac_text or ac_local_file must be provided")
        
        if not input_data.get("figma_file_url"):
            raise ValueError("figma_file_url is required")
        
        return True
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute TechSpec generation.
        
        Args:
            input_data: Input configuration
        
        Returns:
            Output with techspec file path and metadata
        """
        from aitcore.v1.config.settings import get_config
        
        config = get_config()
        output_dir = Path(input_data.get("output_dir", config.outputs_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load acceptance criteria
        ac_content = ""
        if "ac_text" in input_data:
            ac_content = input_data["ac_text"]
        elif "ac_local_file" in input_data:
            ac_file = validate_file_exists(input_data["ac_local_file"])
            ac_content = FileHandler.read_file(ac_file)
        
        # TODO: Integrate with actual TechSpec generation from figma_capture.py
        # For now, create a placeholder that will be filled by agents
        
        techspec_path = output_dir / "techspec.xlsx"
        
        # Save AC to temp file for reference
        ac_file = output_dir / "acceptance_criteria.txt"
        FileHandler.write_file(ac_file, ac_content)
        
        # Save state
        state = StateManager()
        state.save_techspec_state(
            spec_file=str(techspec_path),
            generated_at=datetime.now()
        )
        
        self.logger.info(f"TechSpec generation prepared at {techspec_path}")
        
        return {
            "techspec_path": str(techspec_path),
            "ac_file": str(ac_file),
            "figma_url": input_data.get("figma_file_url"),
            "output_dir": str(output_dir),
        }
