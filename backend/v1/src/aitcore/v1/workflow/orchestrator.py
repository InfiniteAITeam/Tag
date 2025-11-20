"""
Main workflow orchestrator - coordinates and executes workflow steps.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from ..exceptions import StateError
from ..utils.logger import get_logger
from ..services.state_manager import StateManager
from .base_step import BaseStep, StepResult, StepStatus

logger = get_logger(__name__)


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    workflow_id: str
    started_at: datetime
    completed_at: datetime
    steps: List[StepResult] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "success": self.success,
            "error": self.error,
            "steps": [step.to_dict() for step in self.steps],
        }


class WorkflowOrchestrator:
    """Main orchestrator for executing multi-step workflows."""
    
    def __init__(self, workflow_id: str):
        """
        Initialize orchestrator.
        
        Args:
            workflow_id: Unique workflow identifier
        """
        self.workflow_id = workflow_id
        self.logger = logger
        self.state_manager = StateManager()
        self.steps: List[BaseStep] = []
        self.callbacks: Dict[str, List[Callable]] = {
            "on_step_complete": [],
            "on_step_failed": [],
            "on_workflow_complete": [],
        }
    
    def add_step(self, step: BaseStep) -> "WorkflowOrchestrator":
        """
        Add a step to the workflow.
        
        Args:
            step: BaseStep instance to add
        
        Returns:
            Self for chaining
        """
        self.steps.append(step)
        self.logger.info(f"Added step: {step.name}")
        return self
    
    def on_step_complete(self, callback: Callable[[StepResult], None]) -> None:
        """Register callback for step completion."""
        self.callbacks["on_step_complete"].append(callback)
    
    def on_step_failed(self, callback: Callable[[StepResult], None]) -> None:
        """Register callback for step failure."""
        self.callbacks["on_step_failed"].append(callback)
    
    def on_workflow_complete(self, callback: Callable[[WorkflowResult], None]) -> None:
        """Register callback for workflow completion."""
        self.callbacks["on_workflow_complete"].append(callback)
    
    def _execute_callbacks(self, callback_type: str, *args) -> None:
        """Execute registered callbacks."""
        for callback in self.callbacks.get(callback_type, []):
            try:
                callback(*args)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def execute(
        self,
        initial_data: Dict[str, Any],
        stop_on_error: bool = True
    ) -> WorkflowResult:
        """
        Execute all steps in the workflow.
        
        Args:
            initial_data: Initial input data
            stop_on_error: Whether to stop on first error
        
        Returns:
            WorkflowResult with execution details
        """
        started_at = datetime.now()
        steps_results = []
        current_data = initial_data.copy()
        
        self.logger.info(f"Starting workflow: {self.workflow_id}")
        
        for step in self.steps:
            try:
                # Execute step
                result = step.run(current_data)
                steps_results.append(result)
                
                # Handle result
                if result.status == StepStatus.COMPLETED:
                    self.logger.info(f"Step {step.name} completed successfully")
                    self._execute_callbacks("on_step_complete", result)
                    
                    # Pass output to next step
                    current_data = result.output or current_data
                
                elif result.status == StepStatus.FAILED:
                    self.logger.error(f"Step {step.name} failed: {result.error}")
                    self._execute_callbacks("on_step_failed", result)
                    
                    if stop_on_error:
                        raise StateError(f"Workflow stopped at step {step.name}: {result.error}")
            
            except Exception as e:
                self.logger.error(f"Step execution error: {e}")
                steps_results.append(StepResult(
                    step_name=step.name,
                    status=StepStatus.FAILED,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    error=str(e)
                ))
                
                if stop_on_error:
                    result = WorkflowResult(
                        workflow_id=self.workflow_id,
                        started_at=started_at,
                        completed_at=datetime.now(),
                        steps=steps_results,
                        success=False,
                        error=str(e)
                    )
                    self._execute_callbacks("on_workflow_complete", result)
                    return result
        
        # Create final result
        all_successful = all(
            step.status == StepStatus.COMPLETED 
            for step in steps_results
        )
        
        result = WorkflowResult(
            workflow_id=self.workflow_id,
            started_at=started_at,
            completed_at=datetime.now(),
            steps=steps_results,
            success=all_successful
        )
        
        self.logger.info(f"Workflow {self.workflow_id} completed: {'SUCCESS' if all_successful else 'WITH_FAILURES'}")
        self._execute_callbacks("on_workflow_complete", result)
        
        return result
    
    def get_step_output(self, step_name: str, steps_results: List[StepResult]) -> Optional[Dict[str, Any]]:
        """Get output from a specific step."""
        for result in steps_results:
            if result.step_name == step_name:
                return result.output
        return None
