"""
Base workflow step class - abstract foundation for all workflow steps.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from ..exceptions import StateError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StepStatus(str, Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    step_name: str
    status: StepStatus
    started_at: datetime
    completed_at: datetime
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    logs: list[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "output": self.output,
            "error": self.error,
            "logs": self.logs,
        }


class BaseStep(ABC):
    """Abstract base class for all workflow steps."""
    
    def __init__(self, name: str):
        """
        Initialize step.
        
        Args:
            name: Step name for identification and logging
        """
        self.name = name
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            True if valid, raises exception if invalid
        """
        pass
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the step.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            Output data dictionary
        
        Raises:
            Exception: If step execution fails
        """
        pass
    
    def run(self, input_data: Dict[str, Any]) -> StepResult:
        """
        Run the step with error handling and logging.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            StepResult with execution details
        """
        started_at = datetime.now()
        logs = []
        
        try:
            # Log step start
            log_msg = f"Starting step: {self.name}"
            self.logger.info(log_msg)
            logs.append(log_msg)
            
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input data for step {self.name}")
            
            # Execute step
            output = self.execute(input_data)
            
            # Log success
            log_msg = f"Completed step: {self.name}"
            self.logger.info(log_msg)
            logs.append(log_msg)
            
            return StepResult(
                step_name=self.name,
                status=StepStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(),
                output=output,
                logs=logs
            )
        
        except Exception as e:
            error_msg = f"Step {self.name} failed: {e}"
            self.logger.error(error_msg)
            logs.append(error_msg)
            
            return StepResult(
                step_name=self.name,
                status=StepStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(),
                error=str(e),
                logs=logs
            )
