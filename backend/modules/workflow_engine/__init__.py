"""Workflow Engine Module

Task orchestration with DAGs, scheduling, and dependencies.
"""

__version__ = "1.0.0"

from .executor import WorkflowEngineExecutor, execute
from .client import WorkflowEngineClient
from .data_models import (
    WorkflowEngineConfig,
    TaskDefinition, TaskResult,
    WorkflowDefinition,
    CreateWorkflowRequest, CreateWorkflowResponse,
    ExecuteWorkflowRequest, ExecuteWorkflowResponse,
    GetWorkflowStatusRequest, GetWorkflowStatusResponse,
    ScheduleWorkflowRequest, ScheduleWorkflowResponse,
    CancelWorkflowRequest, CancelWorkflowResponse,
    TaskStatus, WorkflowStatus, TaskType, ScheduleType
)

__all__ = [
    'WorkflowEngineExecutor',
    'WorkflowEngineClient',
    'execute',
    'WorkflowEngineConfig',
    'TaskStatus',
    'WorkflowStatus',
    'TaskType',
    'ScheduleType'
]
