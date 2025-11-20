"""
Data models for tagging suggestions and recommendations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class CodeLocation:
    """A location in the code repository."""
    file: str          # Relative path to file
    line: int          # Line number (1-based)
    column: Optional[int] = None
    snippet: Optional[str] = None
    confidence: float = 0.0  # 0-1 confidence score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "snippet": self.snippet,
            "confidence": self.confidence,
        }


@dataclass
class CodeSection:
    """A section of code to be generated/modified."""
    imports: Optional[str] = None
    jsx_attrs: Optional[str] = None
    handler_wrap: Optional[str] = None
    hook: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            k: v for k, v in {
                "imports": self.imports,
                "jsx_attrs": self.jsx_attrs,
                "handler_wrap": self.handler_wrap,
                "hook": self.hook,
            }.items() if v is not None
        }


@dataclass
class AnalyticsEvent:
    """Analytics event to be tracked."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    vendor: str = "adobe"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "params": self.params,
            "vendor": self.vendor,
        }


@dataclass
class TaggingSuggestion:
    """A single tagging suggestion for a KPI."""
    spec_item_index: int
    kpi: str
    action: str
    best_match: Optional[CodeLocation] = None
    suggested_event: Optional[AnalyticsEvent] = None
    code_sections: Optional[CodeSection] = None
    implementation_note: Optional[str] = None
    risks: List[str] = field(default_factory=list)
    why_location: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_item_index": self.spec_item_index,
            "kpi": self.kpi,
            "action": self.action,
            "best_match": self.best_match.to_dict() if self.best_match else None,
            "suggested_event": self.suggested_event.to_dict() if self.suggested_event else None,
            "code_sections": self.code_sections.to_dict() if self.code_sections else None,
            "implementation_note": self.implementation_note,
            "risks": self.risks,
            "why_location": self.why_location,
        }


@dataclass
class TaggingReport:
    """Complete tagging suggestion report."""
    run_id: str
    spec_file: str
    repo_path: str
    generated_at: datetime
    suggestions: List[TaggingSuggestion] = field(default_factory=list)
    helper_file: Optional[Dict[str, str]] = None  # {path, contents}
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def suggestion_count(self) -> int:
        """Get total number of suggestions."""
        return len(self.suggestions)
    
    def matched_count(self) -> int:
        """Get number of suggestions with matched locations."""
        return sum(1 for s in self.suggestions if s.best_match is not None)
    
    def by_action(self, action: str) -> List[TaggingSuggestion]:
        """Get all suggestions for a specific action."""
        return [s for s in self.suggestions if s.action == action]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "spec_file": self.spec_file,
            "repo_path": self.repo_path,
            "generated_at": self.generated_at.isoformat(),
            "suggestion_count": self.suggestion_count(),
            "matched_count": self.matched_count(),
            "suggestions": [s.to_dict() for s in self.suggestions],
            "helper_file": self.helper_file,
            "metadata": self.metadata,
        }
