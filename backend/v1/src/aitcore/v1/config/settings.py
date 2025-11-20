"""
Configuration management for the AIT system.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from ..exceptions import ConfigurationError
from ..utils.validators import validate_directory_exists
from ..utils.constants import (
    DEFAULT_OUTPUTS_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_CLONE_BASE,
    DEFAULT_LLM_MODEL,
)


class AITConfig:
    """Central configuration manager for the AIT system."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize AIT configuration from environment and .env file.
        
        Args:
            env_file: Path to .env file (auto-discovered if None)
        """
        # Load environment
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            load_dotenv(override=True)
        
        # Initialize paths
        self._init_paths()
        
        # Initialize API keys
        self._init_api_keys()
        
        # Initialize LLM settings
        self._init_llm_settings()
    
    def _init_paths(self):
        """Initialize and validate directory paths."""
        # Base directory (where AIT is installed)
        self.base_dir = Path(__file__).parent.parent.parent.parent.resolve()
        
        # Working directories
        self.outputs_dir = Path(
            os.getenv("AIT_OUT_DIR", str(self.base_dir / DEFAULT_OUTPUTS_DIR))
        ).expanduser().resolve()
        
        self.logs_dir = Path(
            os.getenv("AIT_LOG_DIR", str(self.base_dir / DEFAULT_LOGS_DIR))
        ).expanduser().resolve()
        
        self.clone_base_dir = Path(
            os.getenv("CLONE_BASE", DEFAULT_CLONE_BASE)
        ).expanduser().resolve()
        
        # Create directories if they don't exist
        for directory in [self.outputs_dir, self.logs_dir, self.clone_base_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _init_api_keys(self):
        """Initialize API keys from environment."""
        self.openai_api_key = os.getenv("GEMINI_API_KEY", "")
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        
        if not self.openai_api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY environment variable is required"
            )
    
    def _init_llm_settings(self):
        """Initialize LLM configuration."""
        self.llm_model = os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL)
        self.llm_timeout = int(os.getenv("LLM_TIMEOUT", "60"))
        self.use_llm = bool(self.openai_api_key)
    
    def get_output_file(self, filename: str) -> Path:
        """
        Get path to an output file.
        
        Args:
            filename: Output filename
        
        Returns:
            Full path to the output file
        """
        return self.outputs_dir / filename
    
    def get_log_file(self, filename: str) -> Path:
        """
        Get path to a log file.
        
        Args:
            filename: Log filename
        
        Returns:
            Full path to the log file
        """
        return self.logs_dir / filename
    
    def get_clone_path(self, repo_name: str) -> Path:
        """
        Get clone directory for a repository.
        
        Args:
            repo_name: Repository name
        
        Returns:
            Path to the clone directory
        """
        return self.clone_base_dir / repo_name
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        return {
            "base_dir": str(self.base_dir),
            "outputs_dir": str(self.outputs_dir),
            "logs_dir": str(self.logs_dir),
            "clone_base_dir": str(self.clone_base_dir),
            "llm_model": self.llm_model,
            "llm_timeout": self.llm_timeout,
            "use_llm": self.use_llm,
        }


# Global config instance
_config: Optional[AITConfig] = None


def get_config() -> AITConfig:
    """
    Get the global AIT configuration instance.
    
    Returns:
        AITConfig instance
    """
    global _config
    if _config is None:
        _config = AITConfig()
    return _config


def init_config(env_file: Optional[str] = None) -> AITConfig:
    """
    Initialize the global AIT configuration.
    
    Args:
        env_file: Optional path to .env file
    
    Returns:
        Initialized AITConfig instance
    """
    global _config
    _config = AITConfig(env_file)
    return _config
