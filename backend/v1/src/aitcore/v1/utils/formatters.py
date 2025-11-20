"""
Output formatting utilities for the AIT system.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format a dictionary as pretty JSON.
    
    Args:
        data: Dictionary to format
        indent: JSON indentation level
    
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def format_markdown_heading(text: str, level: int = 1) -> str:
    """
    Format text as a Markdown heading.
    
    Args:
        text: Heading text
        level: Heading level (1-6)
    
    Returns:
        Formatted Markdown heading
    """
    hashes = '#' * min(max(level, 1), 6)
    return f"{hashes} {text}"


def format_markdown_code_block(code: str, language: str = "javascript") -> str:
    """
    Format code as a Markdown code block.
    
    Args:
        code: Code to format
        language: Programming language for syntax highlighting
    
    Returns:
        Formatted code block
    """
    return f"```{language}\n{code}\n```"


def format_markdown_list(items: List[str], ordered: bool = False) -> str:
    """
    Format a list as Markdown.
    
    Args:
        items: List items
        ordered: Whether to create an ordered list
    
    Returns:
        Formatted Markdown list
    """
    lines = []
    for i, item in enumerate(items, 1):
        prefix = f"{i}." if ordered else "-"
        lines.append(f"{prefix} {item}")
    return "\n".join(lines)


def format_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Format a table as Markdown.
    
    Args:
        headers: Table column headers
        rows: Table rows (each row is a list of strings)
    
    Returns:
        Formatted Markdown table
    """
    lines = []
    # Headers
    lines.append("| " + " | ".join(headers) + " |")
    # Separator
    lines.append("|" + "|".join(["-" * 3 for _ in headers]) + "|")
    # Rows
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime as ISO 8601 string.
    
    Args:
        dt: Datetime object (defaults to now)
    
    Returns:
        ISO 8601 formatted string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable file size.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
    
    Returns:
        Slugified text
    """
    text = text.strip()
    text = re.sub(r'[^\w]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_').lower()
    return text


def format_relative_path(full_path: Path, base_path: Path) -> str:
    """
    Format a path relative to a base directory.
    
    Args:
        full_path: Full path
        base_path: Base directory path
    
    Returns:
        Relative path as string
    """
    try:
        return str(full_path.relative_to(base_path))
    except ValueError:
        # Path is not relative to base
        return str(full_path)


def format_code_snippet(code: str, line_number: int = 1, context_lines: int = 3) -> str:
    """
    Format a code snippet with line numbers.
    
    Args:
        code: Code string
        line_number: Starting line number
        context_lines: Lines of context to include
    
    Returns:
        Formatted code snippet
    """
    lines = code.splitlines()
    start_idx = max(0, line_number - context_lines)
    end_idx = min(len(lines), line_number + context_lines)
    
    formatted = []
    for i in range(start_idx, end_idx):
        num = i + 1
        marker = "→ " if num == line_number else "  "
        formatted.append(f"{marker}{num:5d}: {lines[i]}")
    
    return "\n".join(formatted)


def format_diff_summary(added: int, removed: int, modified: int) -> str:
    """
    Format a diff summary.
    
    Args:
        added: Number of added lines/files
        removed: Number of removed lines/files
        modified: Number of modified files
    
    Returns:
        Formatted summary
    """
    parts = []
    if added > 0:
        parts.append(f"+{added}")
    if removed > 0:
        parts.append(f"-{removed}")
    if modified > 0:
        parts.append(f"~{modified}")
    
    return " ".join(parts) if parts else "no changes"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """
    Format an exception as a user-friendly error message.
    
    Args:
        error: Exception object
        context: Additional context information
    
    Returns:
        Formatted error message
    """
    msg = str(error)
    if context:
        msg = f"{context}: {msg}"
    return msg
