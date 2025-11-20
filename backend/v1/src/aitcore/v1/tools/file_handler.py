"""
File handling utilities for the AIT system.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from ..exceptions import FileOperationError
from ..utils.constants import REACT_FILE_EXTENSIONS, SKIP_PATTERNS, FILE_ENCODINGS
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Utilities for file operations."""
    
    @staticmethod
    def read_file(file_path: str | Path, encoding: Optional[str] = None) -> str:
        """
        Read file content with fallback encoding support.
        
        Args:
            file_path: Path to the file
            encoding: Encoding to use (tries fallbacks if fails)
        
        Returns:
            File content as string
        
        Raises:
            FileOperationError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise FileOperationError(f"File not found: {path}")
        
        encodings_to_try = [encoding] if encoding else FILE_ENCODINGS
        
        for enc in encodings_to_try:
            if enc is None:
                continue
            try:
                return path.read_text(encoding=enc, errors="replace")
            except Exception:
                continue
        
        raise FileOperationError(f"Could not read file with any encoding: {path}")
    
    @staticmethod
    def write_file(file_path: str | Path, content: str, encoding: str = "utf-8") -> None:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding
        
        Raises:
            FileOperationError: If file cannot be written
        """
        path = Path(file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding, newline="")
            logger.info(f"Wrote file: {path}")
        except Exception as e:
            raise FileOperationError(f"Failed to write file {path}: {e}")
    
    @staticmethod
    def read_json(file_path: str | Path) -> Dict[str, Any]:
        """
        Read JSON file.
        
        Args:
            file_path: Path to the JSON file
        
        Returns:
            Parsed JSON data
        
        Raises:
            FileOperationError: If file cannot be read or parsed
        """
        try:
            content = FileHandler.read_file(file_path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise FileOperationError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise FileOperationError(f"Failed to read JSON file {file_path}: {e}")
    
    @staticmethod
    def write_json(file_path: str | Path, data: Dict[str, Any], indent: int = 2) -> None:
        """
        Write data as JSON file.
        
        Args:
            file_path: Path to the JSON file
            data: Data to write
            indent: JSON indentation level
        
        Raises:
            FileOperationError: If file cannot be written
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            FileHandler.write_file(file_path, content)
        except Exception as e:
            raise FileOperationError(f"Failed to write JSON file {file_path}: {e}")
    
    @staticmethod
    def find_react_files(repo_path: str | Path) -> List[str]:
        """
        Find all React/JavaScript files in a repository.
        
        Args:
            repo_path: Path to the repository
        
        Returns:
            List of relative file paths
        """
        repo = Path(repo_path)
        if not repo.exists():
            logger.warning(f"Repository path not found: {repo}")
            return []
        
        react_files = []
        try:
            for file_path in repo.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip files in skip patterns
                if any(skip in file_path.parts for skip in SKIP_PATTERNS):
                    continue
                
                # Check file extension
                if file_path.suffix.lower() in REACT_FILE_EXTENSIONS:
                    relative = file_path.relative_to(repo)
                    react_files.append(str(relative))
        
        except Exception as e:
            logger.error(f"Error scanning repository {repo}: {e}")
        
        return sorted(react_files)
    
    @staticmethod
    def create_backup(file_path: str | Path, backup_suffix: str = ".bak") -> Path:
        """
        Create a backup copy of a file.
        
        Args:
            file_path: Path to the file
            backup_suffix: Suffix for backup file
        
        Returns:
            Path to the backup file
        
        Raises:
            FileOperationError: If backup cannot be created
        """
        path = Path(file_path)
        if not path.exists():
            raise FileOperationError(f"Cannot backup non-existent file: {path}")
        
        backup_path = path.with_suffix(path.suffix + backup_suffix)
        
        try:
            content = FileHandler.read_file(path)
            FileHandler.write_file(backup_path, content)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            raise FileOperationError(f"Failed to create backup for {path}: {e}")
    
    @staticmethod
    def delete_file(file_path: str | Path) -> None:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file
        
        Raises:
            FileOperationError: If file cannot be deleted
        """
        path = Path(file_path)
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {path}")
        except Exception as e:
            raise FileOperationError(f"Failed to delete file {path}: {e}")
    
    @staticmethod
    def file_exists(file_path: str | Path) -> bool:
        """Check if a file exists."""
        return Path(file_path).is_file()
    
    @staticmethod
    def directory_exists(dir_path: str | Path) -> bool:
        """Check if a directory exists."""
        return Path(dir_path).is_dir()
