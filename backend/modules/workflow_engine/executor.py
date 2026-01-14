"""Workflow Engine Executor"""

import sys
import json
import networkx as nx
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowEngineExecutor:
    """Workflow orchestration executor."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.max_parallel_tasks = config.get('max_parallel_tasks', 5)
        self.task_timeout = config.get('task_timeout', 300)
        self.retry_failed_tasks = config.get('retry_failed_tasks', True)
        self.workflows = {}

    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action."""
        logger.info(f"Executing action: {action}")

        actions = {
            'create_workflow': self.create_workflow,
            'execute_workflow': self.execute_workflow,
            'get_workflow_status': self.get_workflow_status,
            'schedule_workflow': self.schedule_workflow,
            'cancel_workflow': self.cancel_workflow
        }

        if action not in actions:
            return {'success': False, 'error': f'Unknown action: {action}'}

        try:
            result = actions[action](parameters)
            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return {'success': False, 'error': str(e)}

    def create_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow DAG."""
        workflow_id = params['workflow_id']
        tasks = params['tasks']

        # Build DAG
        dag = nx.DiGraph()

        for task in tasks:
            task_id = task['id']
            dependencies = task.get('dependencies', [])

            # Add task node
            dag.add_node(task_id, **task)

            # Add dependency edges
            for dep in dependencies:
                dag.add_edge(dep, task_id)

        # Validate DAG (no cycles)
        if not nx.is_directed_acyclic_graph(dag):
            raise ValueError("Workflow contains cycles")

        self.workflows[workflow_id] = {
            'dag': dag,
            'status': 'created',
            'created_at': datetime.now().isoformat()
        }

        return {
            'workflow_id': workflow_id,
            'task_count': len(tasks),
            'has_cycles': False
        }

    def execute_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow."""
        workflow_id = params['workflow_id']
        inputs = params.get('inputs', {})

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]
        dag = workflow['dag']

        workflow['status'] = 'running'
        workflow['started_at'] = datetime.now().isoformat()

        results = {}
        failed_tasks = []

        # Execute tasks in topological order
        for task_id in nx.topological_sort(dag):
            task_data = dag.nodes[task_id]

            try:
                result = self._execute_task(task_id, task_data, results, inputs)
                results[task_id] = result
                logger.info(f"Task {task_id} completed successfully")
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                failed_tasks.append({
                    'task_id': task_id,
                    'error': str(e)
                })

                if not self.retry_failed_tasks:
                    break

        workflow['status'] = 'completed' if not failed_tasks else 'failed'
        workflow['completed_at'] = datetime.now().isoformat()
        workflow['results'] = results
        workflow['failed_tasks'] = failed_tasks

        return {
            'workflow_id': workflow_id,
            'status': workflow['status'],
            'completed_tasks': len(results),
            'failed_tasks': len(failed_tasks),
            'results': results
        }

    def _execute_task(self, task_id: str, task_data: Dict[str, Any],
                     previous_results: Dict[str, Any],
                     workflow_inputs: Dict[str, Any]) -> Any:
        """Execute a single task."""
        task_type = task_data.get('type', 'python')

        if task_type == 'python':
            # Execute Python callable
            func = task_data.get('function')
            args = task_data.get('args', [])
            kwargs = task_data.get('kwargs', {})

            # Inject previous results and workflow inputs
            kwargs['_previous_results'] = previous_results
            kwargs['_workflow_inputs'] = workflow_inputs

            return func(*args, **kwargs)

        elif task_type == 'shell':
            # Execute shell command
            import subprocess
            cmd = task_data.get('command')
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}

        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    def get_workflow_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow status."""
        workflow_id = params['workflow_id']

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]

        return {
            'workflow_id': workflow_id,
            'status': workflow['status'],
            'created_at': workflow.get('created_at'),
            'started_at': workflow.get('started_at'),
            'completed_at': workflow.get('completed_at'),
            'task_count': workflow['dag'].number_of_nodes(),
            'failed_tasks': len(workflow.get('failed_tasks', []))
        }

    def schedule_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule workflow execution."""
        workflow_id = params['workflow_id']
        schedule = params['schedule']  # e.g., "every day at 10:00"

        # Store schedule
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        self.workflows[workflow_id]['schedule'] = schedule

        return {
            'workflow_id': workflow_id,
            'schedule': schedule,
            'scheduled': True
        }

    def cancel_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel running workflow."""
        workflow_id = params['workflow_id']

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]
        workflow['status'] = 'cancelled'
        workflow['cancelled_at'] = datetime.now().isoformat()

        return {
            'workflow_id': workflow_id,
            'cancelled': True
        }


def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """Main execution entry point."""
    action = params.get('action')
    action_params = params.get('parameters', {})
    config = params.get('config', {})

    executor = WorkflowEngineExecutor(config)
    return executor.execute(action, action_params)


if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    result = execute(input_data)
    print(json.dumps(result))
