"""
Base agent class - abstract foundation for all AI agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..utils.logger import get_logger
from ..tools.openai_client import OpenAIClient
from ..config.settings import get_config


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""
    
    def __init__(self, name: str, use_llm: bool = True):
        """
        Initialize agent.
        
        Args:
            name: Agent name for identification
            use_llm: Whether to use LLM for this agent
        """
        self.name = name
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.use_llm = use_llm
        self.llm_client: Optional[OpenAIClient] = None
        
        if use_llm:
            try:
                self.llm_client = OpenAIClient()
                self.logger.info(f"Agent {name} initialized with LLM support")
            except Exception as e:
                self.logger.warning(f"Could not initialize LLM: {e}")
                self.use_llm = False
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            Output data dictionary
        """
        pass
    
    def log_step(self, message: str) -> None:
        """Log a processing step."""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_warning(self, message: str) -> None:
        """Log a warning."""
        self.logger.warning(f"[{self.name}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log an error."""
        self.logger.error(f"[{self.name}] {message}")
