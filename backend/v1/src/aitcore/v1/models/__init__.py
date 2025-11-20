"""
Models package - data structures for TechSpec, tagging, and repository operations.
"""

from .techspec import TechSpec, SpecItem, AdobeConfig
from .suggestions import (
    TaggingReport,
    TaggingSuggestion,
    CodeLocation,
    CodeSection,
    AnalyticsEvent,
)
from .tagging import (
    ApplyReport,
    ApplyResult,
    ApplyStatus,
    DiffReport,
    FileDiff,
    RepositoryInfo,
    RollbackReport,
)

__all__ = [
    # TechSpec models
    "TechSpec",
    "SpecItem",
    "AdobeConfig",
    # Tagging suggestion models
    "TaggingReport",
    "TaggingSuggestion",
    "CodeLocation",
    "CodeSection",
    "AnalyticsEvent",
    # Application & repo models
    "ApplyReport",
    "ApplyResult",
    "ApplyStatus",
    "DiffReport",
    "FileDiff",
    "RepositoryInfo",
    "RollbackReport",
]
