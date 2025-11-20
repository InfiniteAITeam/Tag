"""
Data models for TechSpec and specifications.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class AdobeConfig:
    """Adobe Analytics configuration for a KPI."""
    variable: Optional[str] = None  # eVar1, prop5, etc.
    value: Optional[str] = None     # Value to assign
    
    def to_dict(self) -> Dict[str, Any]:
        return {"variable": self.variable, "value": self.value}


@dataclass
class SpecItem:
    """A single specification item from the TechSpec."""
    sheet: str
    row_index: int
    description: str  # KPI description
    action: str       # click, view, submit, etc.
    component: Optional[str] = None
    page: Optional[str] = None
    adobe: Optional[AdobeConfig] = None
    target_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sheet": self.sheet,
            "row_index": self.row_index,
            "description": self.description,
            "action": self.action,
            "component": self.component,
            "page": self.page,
            "adobe": self.adobe.to_dict() if self.adobe else None,
            "target_terms": self.target_terms,
        }


@dataclass
class TechSpec:
    """Complete TechSpec document."""
    file_path: str
    generated_at: datetime
    items: List[SpecItem] = field(default_factory=list)
    sheets_parsed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def item_count(self) -> int:
        """Get total number of items."""
        return len(self.items)
    
    def items_by_action(self, action: str) -> List[SpecItem]:
        """Get all items for a specific action type."""
        return [item for item in self.items if item.action == action]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "generated_at": self.generated_at.isoformat(),
            "item_count": self.item_count(),
            "sheets_parsed": self.sheets_parsed,
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata,
        }
