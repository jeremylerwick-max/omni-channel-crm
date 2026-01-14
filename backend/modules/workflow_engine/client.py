"""
Workflow Engine Client

High-level client for workflow orchestration operations.
"""

from typing import Optional, Dict, Any, List, Callable
import logging
import time
from datetime import datetime

from .executor import WorkflowEngineExecutor
from .data_models import (
    CreateWorkflowRequest, CreateWorkflowResponse,
    ExecuteWorkflowRequest, ExecuteWorkflowResponse,
    GetWorkflowStatusRequest, GetWorkflowStatusResponse,
    ScheduleWorkflowRequest, ScheduleWorkflowResponse,
    CancelWorkflowRequest, CancelWorkflowResponse,
    WorkflowEngineConfig, TaskDefinition, WorkflowStatus
)
from .utils import (
    validate_dag, get_topological_order, get_parallel_task_groups,
    get_critical_path, detect_bottlenecks, estimate_workflow_duration,
    visualize_dag, optimize_workflow
)

logger = logging.getLogger(__name__)


class WorkflowEngineClient:
    """
    High-level client for Workflow Engine operations.

    This client provides a user-friendly interface for workflow orchestration
    including DAG management, task execution, and scheduling.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Workflow Engine client.

        Args:
            config: Configuration dictionary
        """
        self.config = WorkflowEngineConfig(**(config or {}))
        self.executor = WorkflowEngineExecutor(self.config.dict())

    def create_workflow(self, workflow_id: str, tasks: List[Dict[str, Any]],
                       max_parallel_tasks: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new workflow with tasks and dependencies.

        Args:
            workflow_id: Unique workflow identifier
            tasks: List of task definitions
            max_parallel_tasks: Maximum parallel tasks

        Returns:
            Dictionary with workflow creation result
        """
        request = CreateWorkflowRequest(
            workflow_id=workflow_id,
            tasks=tasks,
            max_parallel_tasks=max_parallel_tasks or self.config.max_parallel_tasks
        )

        result = self.executor.create_workflow(request.dict())
        logger.info(f"Workflow created: {workflow_id} with {result['task_count']} tasks")

        return result

    def create_simple_workflow(self, workflow_id: str,
                              task_functions: List[Callable],
                              sequential: bool = True) -> Dict[str, Any]:
        """
        Create a simple workflow from a list of functions.

        Args:
            workflow_id: Unique workflow identifier
            task_functions: List of callable functions
            sequential: Whether tasks run sequentially (True) or in parallel (False)

        Returns:
            Dictionary with workflow creation result
        """
        tasks = []

        for i, func in enumerate(task_functions):
            task_id = f"task_{i}"
            task = {
                'id': task_id,
                'type': 'python',
                'function': func,
                'dependencies': [f"task_{i-1}"] if sequential and i > 0 else []
            }
            tasks.append(task)

        return self.create_workflow(workflow_id, tasks)

    def execute_workflow(self, workflow_id: str,
                        inputs: Optional[Dict[str, Any]] = None,
                        dry_run: bool = False,
                        async_execution: bool = False) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow identifier
            inputs: Workflow input parameters
            dry_run: Run in dry-run mode (validate without executing)
            async_execution: Execute asynchronously

        Returns:
            Dictionary with execution result
        """
        request = ExecuteWorkflowRequest(
            workflow_id=workflow_id,
            inputs=inputs or {},
            dry_run=dry_run,
            async_execution=async_execution
        )

        start_time = time.time()
        result = self.executor.execute_workflow(request.dict())
        execution_time = time.time() - start_time

        result['execution_time_seconds'] = execution_time

        status = result.get('status')
        if status == 'completed':
            logger.info(f"Workflow {workflow_id} completed successfully in {execution_time:.2f}s")
        elif status == 'failed':
            logger.error(f"Workflow {workflow_id} failed after {execution_time:.2f}s")

        return result

    def get_workflow_status(self, workflow_id: str,
                          include_task_details: bool = False) -> Dict[str, Any]:
        """
        Get workflow execution status.

        Args:
            workflow_id: Workflow identifier
            include_task_details: Include detailed task information

        Returns:
            Dictionary with workflow status
        """
        request = GetWorkflowStatusRequest(
            workflow_id=workflow_id,
            include_task_details=include_task_details
        )

        return self.executor.get_workflow_status(request.dict())

    def schedule_workflow(self, workflow_id: str, schedule: str,
                         schedule_type: str = "cron",
                         inputs: Optional[Dict[str, Any]] = None,
                         enabled: bool = True) -> Dict[str, Any]:
        """
        Schedule workflow for recurring execution.

        Args:
            workflow_id: Workflow identifier
            schedule: Schedule expression (cron or interval)
            schedule_type: Schedule type (cron, interval, once)
            inputs: Default workflow inputs
            enabled: Whether schedule is enabled

        Returns:
            Dictionary with scheduling result
        """
        request = ScheduleWorkflowRequest(
            workflow_id=workflow_id,
            schedule=schedule,
            schedule_type=schedule_type,
            inputs=inputs or {},
            enabled=enabled
        )

        result = self.executor.schedule_workflow(request.dict())
        logger.info(f"Workflow {workflow_id} scheduled: {schedule}")

        return result

    def cancel_workflow(self, workflow_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Cancel a running workflow.

        Args:
            workflow_id: Workflow identifier
            force: Force cancellation

        Returns:
            Dictionary with cancellation result
        """
        request = CancelWorkflowRequest(workflow_id=workflow_id, force=force)
        result = self.executor.cancel_workflow(request.dict())

        logger.info(f"Workflow {workflow_id} cancelled")
        return result

    def get_workflow_dag(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get DAG representation of workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with DAG information
        """
        if workflow_id not in self.executor.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.executor.workflows[workflow_id]
        dag = workflow['dag']

        # Get DAG metrics
        task_levels = get_parallel_task_groups(dag)
        critical_path = get_critical_path(dag)
        bottlenecks = detect_bottlenecks(dag)

        return {
            'workflow_id': workflow_id,
            'node_count': dag.number_of_nodes(),
            'edge_count': dag.number_of_edges(),
            'max_parallelism': max(len(group) for group in task_levels) if task_levels else 0,
            'critical_path': critical_path,
            'critical_path_length': len(critical_path),
            'bottlenecks': bottlenecks,
            'parallel_groups': len(task_levels),
            'visualization': visualize_dag(dag)
        }

    def optimize_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Analyze workflow and get optimization suggestions.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with optimization analysis
        """
        if workflow_id not in self.executor.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.executor.workflows[workflow_id]
        dag = workflow['dag']

        return optimize_workflow(dag)

    def list_workflows(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all workflows with optional status filter.

        Args:
            status_filter: Filter by workflow status

        Returns:
            List of workflow summaries
        """
        workflows = []

        for workflow_id, workflow in self.executor.workflows.items():
            workflow_status = workflow.get('status')

            if status_filter and workflow_status != status_filter:
                continue

            workflows.append({
                'workflow_id': workflow_id,
                'status': workflow_status,
                'created_at': workflow.get('created_at'),
                'task_count': workflow['dag'].number_of_nodes(),
                'started_at': workflow.get('started_at'),
                'completed_at': workflow.get('completed_at')
            })

        return workflows

    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with deletion result
        """
        if workflow_id not in self.executor.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Can only delete workflows that are not running
        workflow = self.executor.workflows[workflow_id]
        if workflow.get('status') == 'running':
            raise ValueError(f"Cannot delete running workflow: {workflow_id}")

        del self.executor.workflows[workflow_id]

        logger.info(f"Workflow deleted: {workflow_id}")
        return {
            'workflow_id': workflow_id,
            'deleted': True
        }

    def pause_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Pause a running workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with pause result
        """
        if workflow_id not in self.executor.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.executor.workflows[workflow_id]
        workflow['status'] = 'paused'
        workflow['paused_at'] = datetime.now().isoformat()

        logger.info(f"Workflow paused: {workflow_id}")
        return {
            'workflow_id': workflow_id,
            'paused': True,
            'status': 'paused'
        }

    def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Resume a paused workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with resume result
        """
        if workflow_id not in self.executor.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.executor.workflows[workflow_id]

        if workflow.get('status') != 'paused':
            raise ValueError(f"Workflow is not paused: {workflow_id}")

        workflow['status'] = 'running'
        workflow['resumed_at'] = datetime.now().isoformat()

        logger.info(f"Workflow resumed: {workflow_id}")
        return {
            'workflow_id': workflow_id,
            'resumed': True,
            'status': 'running'
        }

    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for all workflows.

        Returns:
            Dictionary with workflow metrics
        """
        total_workflows = len(self.executor.workflows)
        running = sum(1 for w in self.executor.workflows.values() if w.get('status') == 'running')
        completed = sum(1 for w in self.executor.workflows.values() if w.get('status') == 'completed')
        failed = sum(1 for w in self.executor.workflows.values() if w.get('status') == 'failed')

        # Calculate average execution time
        execution_times = []
        for workflow in self.executor.workflows.values():
            if workflow.get('started_at') and workflow.get('completed_at'):
                started = datetime.fromisoformat(workflow['started_at'])
                completed_time = datetime.fromisoformat(workflow['completed_at'])
                execution_times.append((completed_time - started).total_seconds())

        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            'total_workflows': total_workflows,
            'running_workflows': running,
            'completed_workflows': completed,
            'failed_workflows': failed,
            'average_execution_time_seconds': avg_execution_time,
            'success_rate': (completed / total_workflows * 100) if total_workflows > 0 else 0
        }

    def clone_workflow(self, source_workflow_id: str, new_workflow_id: str) -> Dict[str, Any]:
        """
        Clone an existing workflow.

        Args:
            source_workflow_id: Source workflow ID
            new_workflow_id: New workflow ID

        Returns:
            Dictionary with cloning result
        """
        if source_workflow_id not in self.executor.workflows:
            raise ValueError(f"Source workflow not found: {source_workflow_id}")

        if new_workflow_id in self.executor.workflows:
            raise ValueError(f"Workflow already exists: {new_workflow_id}")

        source_workflow = self.executor.workflows[source_workflow_id]
        source_dag = source_workflow['dag']

        # Extract tasks from source DAG
        tasks = []
        for node in source_dag.nodes():
            task_data = source_dag.nodes[node]
            dependencies = list(source_dag.predecessors(node))

            tasks.append({
                'id': node,
                'dependencies': dependencies,
                **task_data
            })

        # Create new workflow
        return self.create_workflow(new_workflow_id, tasks)

    def validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Validate a workflow definition.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with validation result
        """
        if workflow_id not in self.executor.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.executor.workflows[workflow_id]
        dag = workflow['dag']

        # Validate DAG
        is_valid, error = validate_dag(dag)

        return {
            'workflow_id': workflow_id,
            'is_valid': is_valid,
            'error': error,
            'has_cycles': not is_valid,
            'node_count': dag.number_of_nodes(),
            'edge_count': dag.number_of_edges()
        }
