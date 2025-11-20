"""
Utilities package - logging, validation, formatting, and constants.
"""

from .logger import setup_logger, get_logger
from .validators import (
    validate_file_exists,
    validate_directory_exists,
    validate_github_url,
    validate_excel_file,
    validate_react_file,
    validate_non_empty_string,
    validate_positive_int,
    validate_dict_keys,
)
from .formatters import (
    format_json,
    format_markdown_heading,
    format_markdown_code_block,
    format_markdown_list,
    format_markdown_table,
    format_timestamp,
    format_file_size,
    slugify,
    format_relative_path,
    format_code_snippet,
    format_diff_summary,
    truncate_string,
    format_error_message,
)
from .constants import (
    REACT_FILE_EXTENSIONS,
    BACKUP_SUFFIX,
    ActionType,
    DEFAULT_OUTPUTS_DIR,
    DEFAULT_LLM_MODEL,
)

__all__ = [
    # Logger
    "setup_logger",
    "get_logger",
    # Validators
    "validate_file_exists",
    "validate_directory_exists",
    "validate_github_url",
    "validate_excel_file",
    "validate_react_file",
    "validate_non_empty_string",
    "validate_positive_int",
    "validate_dict_keys",
    # Formatters
    "format_json",
    "format_markdown_heading",
    "format_markdown_code_block",
    "format_markdown_list",
    "format_markdown_table",
    "format_timestamp",
    "format_file_size",
    "slugify",
    "format_relative_path",
    "format_code_snippet",
    "format_diff_summary",
    "truncate_string",
    "format_error_message",
    # Constants
    "REACT_FILE_EXTENSIONS",
    "BACKUP_SUFFIX",
    "ActionType",
    "DEFAULT_OUTPUTS_DIR",
    "DEFAULT_LLM_MODEL",
]
