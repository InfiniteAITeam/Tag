"""
Tagging agent - matches code locations to TechSpec items using LLM and heuristics.
"""

from typing import Dict, Any, List
from pathlib import Path
from ..tools.file_handler import FileHandler
from ..models.suggestions import TaggingSuggestion, CodeLocation
from .base_agent import BaseAgent


class TaggingAgent(BaseAgent):
    """Agent for matching TechSpec items to code locations."""
    
    def __init__(self):
        """Initialize tagging agent."""
        super().__init__("TaggingAgent", use_llm=True)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match TechSpec items to code locations.
        
        Expected input:
        - techspec: dict (parsed TechSpec)
        - repo_path: str (repository path)
        - react_files: List[str] (React files to search)
        
        Returns:
            List of tagging suggestions
        """
        self.log_step("Starting code matching")
        
        techspec = input_data.get("techspec", {})
        repo_path = Path(input_data.get("repo_path", "."))
        react_files = input_data.get("react_files", [])
        
        suggestions: List[Dict[str, Any]] = []
        
        # TODO: Implement actual code matching using:
        # 1. Semantic search through React files
        # 2. LLM-based matching with explain_mapping
        # 3. Heuristic matching based on component names
        
        spec_items = techspec.get("items", [])
        for idx, item in enumerate(spec_items):
            # Sample suggestion structure
            suggestion = {
                "spec_item_index": idx,
                "kpi": item.get("description", "Unknown"),
                "action": item.get("action", "unknown"),
                "file": react_files[0] if react_files else "unknown.js",
                "line": 1,
                "confidence": 0.0,  # Will be filled by matching algorithm
                "code": {},
            }
            suggestions.append(suggestion)
        
        self.log_step(f"Generated {len(suggestions)} tagging suggestions")
        
        return {
            "suggestions": suggestions,
            "matched_count": len([s for s in suggestions if s.get("confidence", 0) > 0.5]),
            "total_count": len(suggestions),
        }
