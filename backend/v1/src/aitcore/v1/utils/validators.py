"""
Input validation utilities for the AIT system.
"""

import re
from pathlib import Path
from typing import Optional, Any
from ..exceptions import ValidationError
from .constants import GITHUB_URL_PATTERN, REACT_FILE_EXTENSIONS


def validate_file_exists(file_path: str | Path, error_msg: Optional[str] = None) -> Path:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to the file
        error_msg: Custom error message
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If file doesn't exist
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        msg = error_msg or f"File not found: {path}"
        raise ValidationError(msg)
    return path


def validate_directory_exists(dir_path: str | Path, error_msg: Optional[str] = None) -> Path:
    """
    Validate that a directory exists.
    
    Args:
        dir_path: Path to the directory
        error_msg: Custom error message
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If directory doesn't exist
    """
    path = Path(dir_path).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        msg = error_msg or f"Directory not found: {path}"
        raise ValidationError(msg)
    return path


def validate_github_url(url: str) -> tuple[str, str]:
    """
    Validate GitHub URL format and extract owner and repo.
    
    Args:
        url: GitHub repository URL
    
    Returns:
        Tuple of (owner, repo_name)
    
    Raises:
        ValidationError: If URL format is invalid
    """
    url = url.strip()
    match = re.match(GITHUB_URL_PATTERN, url)
    if not match:
        raise ValidationError(f"Invalid GitHub URL format: {url}")
    return match.group(1), match.group(2)


def validate_excel_file(file_path: str | Path) -> Path:
    """
    Validate that a file is a valid Excel file.
    
    Args:
        file_path: Path to the Excel file
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If not a valid Excel file
    """
    path = validate_file_exists(file_path)
    if path.suffix.lower() != '.xlsx':
        raise ValidationError(f"File must be .xlsx format: {path}")
    return path


def validate_react_file(file_path: str | Path) -> Path:
    """
    Validate that a file is a React/JavaScript file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Resolved Path object
    
    Raises:
        ValidationError: If not a React file
    """
    path = validate_file_exists(file_path)
    if path.suffix.lower() not in REACT_FILE_EXTENSIONS:
        raise ValidationError(
            f"File must be React/JS file ({REACT_FILE_EXTENSIONS}): {path}"
        )
    return path


def validate_non_empty_string(value: Any, field_name: str) -> str:
    """
    Validate that a value is a non-empty string.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error message)
    
    Returns:
        Trimmed string
    
    Raises:
        ValidationError: If value is not a non-empty string
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def validate_positive_int(value: Any, field_name: str, minimum: int = 1) -> int:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error message)
        minimum: Minimum allowed value
    
    Returns:
        Validated integer
    
    Raises:
        ValidationError: If value is not a positive integer
    """
    try:
        int_val = int(value)
        if int_val < minimum:
            raise ValueError
        return int_val
    except (TypeError, ValueError):
        raise ValidationError(
            f"{field_name} must be an integer >= {minimum}"
        )


def validate_dict_keys(data: dict, required_keys: list[str], field_name: str = "data") -> dict:
    """
    Validate that a dictionary contains all required keys.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required keys
        field_name: Name of the field (for error message)
    
    Returns:
        The validated dictionary
    
    Raises:
        ValidationError: If required keys are missing
    """
    if not isinstance(data, dict):
        raise ValidationError(f"{field_name} must be a dictionary")
    
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValidationError(
            f"{field_name} missing required keys: {missing}"
        )
    return data
