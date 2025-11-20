"""
Backup management utilities for handling file backups and restoration.
"""

from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from ..exceptions import BackupError, FileOperationError
from ..utils.constants import BACKUP_SUFFIX
from ..utils.logger import get_logger
from .file_handler import FileHandler

logger = get_logger(__name__)


class BackupManager:
    """Manage file backups and restoration."""
    
    @staticmethod
    def create_backup(
        file_path: str | Path,
        backup_suffix: str = BACKUP_SUFFIX
    ) -> Path:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            backup_suffix: Suffix for backup file
        
        Returns:
            Path to the backup file
        
        Raises:
            BackupError: If backup cannot be created
        """
        path = Path(file_path)
        
        if not path.exists():
            raise BackupError(f"File not found: {path}")
        
        backup_path = path.with_suffix(path.suffix + backup_suffix)
        
        # Don't overwrite existing backup
        if backup_path.exists():
            logger.info(f"Backup already exists: {backup_path}")
            return backup_path
        
        try:
            return FileHandler.create_backup(path, backup_suffix)
        except FileOperationError as e:
            raise BackupError(f"Failed to create backup for {path}: {e}")
    
    @staticmethod
    def restore_from_backup(
        backup_path: str | Path,
        target_path: Optional[str | Path] = None,
        delete_backup: bool = False
    ) -> None:
        """
        Restore a file from its backup.
        
        Args:
            backup_path: Path to the backup file
            target_path: Path where to restore (if None, derives from backup path)
            delete_backup: Whether to delete backup after restoration
        
        Raises:
            BackupError: If restoration fails
        """
        backup = Path(backup_path)
        
        if not backup.exists():
            raise BackupError(f"Backup file not found: {backup}")
        
        # Derive target if not provided
        if target_path is None:
            backup_suffix = BACKUP_SUFFIX
            if not backup.name.endswith(backup_suffix):
                raise BackupError(f"Invalid backup file format: {backup}")
            target = backup.with_name(backup.name[:-len(backup_suffix)])
        else:
            target = Path(target_path)
        
        try:
            # Read backup and write to target
            content = FileHandler.read_file(backup)
            FileHandler.write_file(target, content)
            logger.info(f"Restored {target} from {backup}")
            
            # Delete backup if requested
            if delete_backup:
                FileHandler.delete_file(backup)
        
        except FileOperationError as e:
            raise BackupError(f"Failed to restore from {backup}: {e}")
    
    @staticmethod
    def find_backups(
        repo_root: str | Path,
        backup_suffix: str = BACKUP_SUFFIX
    ) -> List[Path]:
        """
        Find all backup files in a repository.
        
        Args:
            repo_root: Repository root path
            backup_suffix: Backup file suffix
        
        Returns:
            List of backup file paths
        """
        repo = Path(repo_root)
        backups = []
        
        try:
            for backup in repo.rglob(f"*{backup_suffix}"):
                if backup.is_file():
                    backups.append(backup)
        except Exception as e:
            logger.error(f"Error finding backups in {repo}: {e}")
        
        return sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
    
    @staticmethod
    def restore_all_backups(
        repo_root: str | Path,
        backup_suffix: str = BACKUP_SUFFIX,
        delete_backups: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Restore all backups in a repository.
        
        Args:
            repo_root: Repository root path
            backup_suffix: Backup file suffix
            delete_backups: Whether to delete backups after restoration
        
        Returns:
            Tuple of (restored_count, error_list)
        """
        backups = BackupManager.find_backups(repo_root, backup_suffix)
        restored_count = 0
        errors = []
        
        for backup in backups:
            try:
                BackupManager.restore_from_backup(
                    backup,
                    delete_backup=delete_backups
                )
                restored_count += 1
            except BackupError as e:
                error_msg = f"Failed to restore {backup}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return restored_count, errors
    
    @staticmethod
    def cleanup_backups(
        repo_root: str | Path,
        backup_suffix: str = BACKUP_SUFFIX
    ) -> int:
        """
        Delete all backup files in a repository.
        
        Args:
            repo_root: Repository root path
            backup_suffix: Backup file suffix
        
        Returns:
            Number of deleted backups
        """
        backups = BackupManager.find_backups(repo_root, backup_suffix)
        deleted_count = 0
        
        for backup in backups:
            try:
                FileHandler.delete_file(backup)
                deleted_count += 1
            except FileOperationError as e:
                logger.error(f"Failed to delete {backup}: {e}")
        
        return deleted_count
