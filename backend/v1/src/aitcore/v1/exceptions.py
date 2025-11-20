"""
Custom exception classes for the Agentic Tagging System.
"""


class AITException(Exception):
    """Base exception for all AIT system errors."""
    pass


class ConfigurationError(AITException):
    """Raised when configuration is missing or invalid."""
    pass


class FileOperationError(AITException):
    """Raised when file operations fail."""
    pass


class RepoOperationError(AITException):
    """Raised when repository operations fail."""
    pass


class SpecParsingError(AITException):
    """Raised when TechSpec parsing fails."""
    pass


class MatchingError(AITException):
    """Raised when code matching/location fails."""
    pass


class LLMError(AITException):
    """Raised when LLM operations fail."""
    pass


class TaggingError(AITException):
    """Raised when tagging operations fail."""
    pass


class ApplyError(AITException):
    """Raised when applying tagging fails."""
    pass


class BackupError(AITException):
    """Raised when backup operations fail."""
    pass


class RollbackError(AITException):
    """Raised when rollback operations fail."""
    pass


class ValidationError(AITException):
    """Raised when input validation fails."""
    pass


class StateError(AITException):
    """Raised when workflow state is invalid."""
    pass
