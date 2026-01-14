"""
Workflow Engine Data Models

Pydantic models for workflow orchestration and task management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskType(str, Enum):
    """Task execution types."""
    PYTHON = "python"
    SHELL = "shell"
    HTTP = "http"
    DOCKER = "docker"
    LAMBDA = "lambda"


class ScheduleType(str, Enum):
    """Schedule types for workflow execution."""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


class TaskDefinition(BaseModel):
    """Task definition in a workflow."""
    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    type: TaskType = Field(default=TaskType.PYTHON, description="Task type")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this task depends on")
    function: Optional[Any] = Field(None, description="Python function to execute")
    command: Optional[str] = Field(None, description="Shell command to execute")
    args: List[Any] = Field(default_factory=list, description="Function arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Function keyword arguments")
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")
    retry_count: int = Field(default=0, description="Number of retries on failure")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")
    on_failure: Optional[str] = Field(None, description="Task to run on failure")
    on_success: Optional[str] = Field(None, description="Task to run on success")


class TaskResult(BaseModel):
    """Result of a task execution."""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Task status")
    result: Optional[Any] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    execution_time_seconds: Optional[float] = Field(None, description="Execution time")
    retry_count: int = Field(default=0, description="Number of retries attempted")


class WorkflowDefinition(BaseModel):
    """Workflow definition with tasks and dependencies."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    tasks: List[TaskDefinition] = Field(..., description="List of tasks in the workflow")
    max_parallel_tasks: int = Field(default=5, description="Maximum parallel tasks")
    timeout: Optional[int] = Field(None, description="Overall workflow timeout")
    on_failure: Optional[str] = Field(None, description="Action on workflow failure")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a workflow."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    tasks: List[Dict[str, Any]] = Field(..., description="Task definitions")
    max_parallel_tasks: Optional[int] = Field(None, description="Maximum parallel tasks")


class CreateWorkflowResponse(BaseModel):
    """Response model for workflow creation."""
    workflow_id: str = Field(..., description="Created workflow ID")
    task_count: int = Field(..., description="Number of tasks")
    has_cycles: bool = Field(..., description="Whether workflow contains cycles")
    created_at: datetime = Field(default_factory=datetime.now)


class ExecuteWorkflowRequest(BaseModel):
    """Request model for executing a workflow."""
    workflow_id: str = Field(..., description="Workflow identifier")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Workflow inputs")
    dry_run: bool = Field(default=False, description="Run in dry-run mode")
    async_execution: bool = Field(default=False, description="Execute asynchronously")


class ExecuteWorkflowResponse(BaseModel):
    """Response model for workflow execution."""
    workflow_id: str = Field(..., description="Workflow identifier")
    status: WorkflowStatus = Field(..., description="Workflow status")
    completed_tasks: int = Field(..., description="Number of completed tasks")
    failed_tasks: int = Field(..., description="Number of failed tasks")
    skipped_tasks: int = Field(default=0, description="Number of skipped tasks")
    results: Dict[str, Any] = Field(..., description="Task results")
    started_at: Optional[datetime] = Field(None, description="Workflow start time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    execution_time_seconds: Optional[float] = Field(None, description="Total execution time")


class GetWorkflowStatusRequest(BaseModel):
    """Request model for getting workflow status."""
    workflow_id: str = Field(..., description="Workflow identifier")
    include_task_details: bool = Field(default=False, description="Include task details")


class GetWorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str = Field(..., description="Workflow identifier")
    status: WorkflowStatus = Field(..., description="Current status")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    task_count: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    failed_tasks: int = Field(default=0, description="Number of failed tasks")
    task_details: Optional[List[TaskResult]] = Field(None, description="Detailed task information")


class ScheduleWorkflowRequest(BaseModel):
    """Request model for scheduling a workflow."""
    workflow_id: str = Field(..., description="Workflow identifier")
    schedule: str = Field(..., description="Schedule expression")
    schedule_type: ScheduleType = Field(default=ScheduleType.CRON, description="Schedule type")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Default workflow inputs")
    enabled: bool = Field(default=True, description="Whether schedule is enabled")


class ScheduleWorkflowResponse(BaseModel):
    """Response model for workflow scheduling."""
    workflow_id: str = Field(..., description="Workflow identifier")
    schedule: str = Field(..., description="Schedule expression")
    schedule_type: ScheduleType = Field(..., description="Schedule type")
    scheduled: bool = Field(..., description="Whether scheduling was successful")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run time")


class CancelWorkflowRequest(BaseModel):
    """Request model for cancelling a workflow."""
    workflow_id: str = Field(..., description="Workflow identifier")
    force: bool = Field(default=False, description="Force cancellation")


class CancelWorkflowResponse(BaseModel):
    """Response model for workflow cancellation."""
    workflow_id: str = Field(..., description="Workflow identifier")
    cancelled: bool = Field(..., description="Whether cancellation was successful")
    tasks_cancelled: int = Field(..., description="Number of tasks cancelled")
    cancelled_at: datetime = Field(default_factory=datetime.now)


class WorkflowMetrics(BaseModel):
    """Metrics for workflow execution."""
    total_workflows: int = Field(..., description="Total workflows created")
    running_workflows: int = Field(..., description="Currently running workflows")
    completed_workflows: int = Field(..., description="Successfully completed workflows")
    failed_workflows: int = Field(..., description="Failed workflows")
    total_tasks_executed: int = Field(..., description="Total tasks executed")
    average_execution_time_seconds: float = Field(..., description="Average execution time")
    success_rate: float = Field(..., description="Success rate percentage")


class DAGNode(BaseModel):
    """DAG node representation."""
    task_id: str = Field(..., description="Task identifier")
    dependencies: List[str] = Field(default_factory=list, description="Dependent task IDs")
    dependents: List[str] = Field(default_factory=list, description="Tasks that depend on this")
    level: int = Field(..., description="Depth level in DAG")


class DAGInfo(BaseModel):
    """DAG information."""
    workflow_id: str = Field(..., description="Workflow identifier")
    node_count: int = Field(..., description="Number of nodes")
    edge_count: int = Field(..., description="Number of edges")
    max_depth: int = Field(..., description="Maximum depth")
    is_valid: bool = Field(..., description="Whether DAG is valid (no cycles)")
    nodes: List[DAGNode] = Field(..., description="DAG nodes")
    critical_path: List[str] = Field(..., description="Critical path through DAG")


class WorkflowEngineConfig(BaseModel):
    """Workflow Engine configuration."""
    max_parallel_tasks: int = Field(default=5, description="Maximum parallel tasks", gt=0)
    task_timeout: int = Field(default=300, description="Default task timeout in seconds")
    retry_failed_tasks: bool = Field(default=True, description="Retry failed tasks")
    default_retry_count: int = Field(default=3, description="Default retry count")
    default_retry_delay: int = Field(default=5, description="Default retry delay in seconds")
    enable_workflow_persistence: bool = Field(default=True, description="Persist workflows")
    workflow_storage_path: Optional[str] = Field(None, description="Workflow storage directory")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
