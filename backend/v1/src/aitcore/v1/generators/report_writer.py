"""
Report writer - generates Markdown and JSON reports from workflow results.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from ..tools.file_handler import FileHandler
from ..utils.formatters import (
    format_markdown_heading,
    format_markdown_code_block,
    format_markdown_table,
    format_markdown_list,
    format_timestamp,
)
from ..utils.logger import get_logger


class ReportWriter:
    """Generates formatted reports from workflow and analysis results."""
    
    def __init__(self):
        """Initialize report writer."""
        self.logger = get_logger(__name__)
    
    def generate_suggestions_report(self, suggestions_data: Dict[str, Any]) -> str:
        """
        Generate Markdown report for tagging suggestions.
        
        Args:
            suggestions_data: Suggestions data from workflow
        
        Returns:
            Markdown formatted report
        """
        self.logger.info("Generating suggestions report")
        
        report = format_markdown_heading("Tagging Suggestions Report", 1) + "\n\n"
        
        # Metadata
        report += format_markdown_heading("Metadata", 2) + "\n"
        report += f"- **Generated**: {format_timestamp()}\n"
        report += f"- **Repository**: {suggestions_data.get('repo_path', 'Unknown')}\n"
        report += f"- **React Files**: {suggestions_data.get('react_files_count', 0)}\n"
        report += f"- **Total Suggestions**: {len(suggestions_data.get('suggestions', []))}\n\n"
        
        # Suggestions breakdown
        report += format_markdown_heading("Suggestions", 2) + "\n"
        suggestions = suggestions_data.get("suggestions", [])
        
        if suggestions:
            # Group by action type
            by_action = {}
            for sugg in suggestions:
                action = sugg.get("action", "unknown")
                if action not in by_action:
                    by_action[action] = []
                by_action[action].append(sugg)
            
            for action, items in by_action.items():
                report += f"\n**{action.title()}** ({len(items)} items)\n"
                for item in items[:5]:  # Show first 5
                    report += f"- {item.get('kpi', 'Unknown')} → {item.get('file', 'unknown.js')}\n"
                
                if len(items) > 5:
                    report += f"- ... and {len(items) - 5} more\n"
        else:
            report += "No suggestions generated.\n"
        
        return report
    
    def generate_apply_report(self, apply_data: Dict[str, Any]) -> str:
        """
        Generate Markdown report for tagging application.
        
        Args:
            apply_data: Application results from workflow
        
        Returns:
            Markdown formatted report
        """
        self.logger.info("Generating application report")
        
        report = format_markdown_heading("Tagging Application Report", 1) + "\n\n"
        
        # Summary
        report += format_markdown_heading("Summary", 2) + "\n"
        report += f"- **Repository**: {apply_data.get('repo_path', 'Unknown')}\n"
        report += f"- **Applied**: {apply_data.get('success_count', 0)}\n"
        report += f"- **Failed**: {apply_data.get('failed_count', 0)}\n\n"
        
        # Status
        success_pct = 0
        total = apply_data.get('success_count', 0) + apply_data.get('failed_count', 0)
        if total > 0:
            success_pct = (apply_data.get('success_count', 0) / total) * 100
        
        report += f"**Success Rate**: {success_pct:.1f}%\n\n"
        
        return report
    
    def generate_workflow_report(self, workflow_result: Dict[str, Any]) -> str:
        """
        Generate Markdown report for complete workflow.
        
        Args:
            workflow_result: Complete workflow result
        
        Returns:
            Markdown formatted report
        """
        self.logger.info("Generating workflow report")
        
        report = format_markdown_heading("Workflow Execution Report", 1) + "\n\n"
        
        # Overview
        report += format_markdown_heading("Overview", 2) + "\n"
        report += f"- **Workflow ID**: {workflow_result.get('workflow_id')}\n"
        report += f"- **Status**: {'✅ SUCCESS' if workflow_result.get('success') else '❌ FAILED'}\n"
        report += f"- **Started**: {workflow_result.get('started_at')}\n"
        report += f"- **Completed**: {workflow_result.get('completed_at')}\n\n"
        
        # Steps
        report += format_markdown_heading("Steps", 2) + "\n"
        steps = workflow_result.get("steps", [])
        
        for step in steps:
            status_icon = "✅" if step.get("status") == "completed" else "❌"
            report += f"{status_icon} **{step.get('step_name')}**\n"
            
            if step.get("error"):
                report += f"  - Error: {step.get('error')}\n"
        
        return report
    
    def save_report(self, report_content: str, output_path: Path) -> Path:
        """
        Save generated report to file.
        
        Args:
            report_content: Markdown report content
            output_path: Where to save the file
        
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        FileHandler.write_file(output_path, report_content)
        self.logger.info(f"Saved report to {output_path}")
        return output_path
