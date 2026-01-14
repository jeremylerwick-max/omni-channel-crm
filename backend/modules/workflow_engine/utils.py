"""
Workflow Engine Utilities

Helper functions for workflow orchestration and DAG management.
"""

import networkx as nx
from typing import List, Dict, Any, Tuple, Set, Optional
from datetime import datetime, timedelta
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


def validate_dag(graph: nx.DiGraph) -> Tuple[bool, Optional[str]]:
    """
    Validate that a graph is a valid DAG (Directed Acyclic Graph).

    Args:
        graph: NetworkX directed graph

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(graph, nx.DiGraph):
        return False, "Graph must be a directed graph"

    if not nx.is_directed_acyclic_graph(graph):
        # Find a cycle
        try:
            cycle = nx.find_cycle(graph)
            cycle_str = " -> ".join([str(edge[0]) for edge in cycle])
            return False, f"Graph contains cycle: {cycle_str}"
        except nx.NetworkXNoCycle:
            pass

    if graph.number_of_nodes() == 0:
        return False, "Graph is empty"

    return True, None


def get_topological_order(graph: nx.DiGraph) -> List[str]:
    """
    Get topological order of tasks in DAG.

    Args:
        graph: NetworkX DAG

    Returns:
        List of task IDs in topological order
    """
    try:
        return list(nx.topological_sort(graph))
    except nx.NetworkXError as e:
        logger.error(f"Error getting topological order: {e}")
        return []


def get_task_levels(graph: nx.DiGraph) -> Dict[str, int]:
    """
    Calculate depth level of each task in DAG.

    Args:
        graph: NetworkX DAG

    Returns:
        Dictionary mapping task ID to level
    """
    levels = {}

    for node in nx.topological_sort(graph):
        # Level is max of all predecessor levels + 1
        predecessors = list(graph.predecessors(node))
        if not predecessors:
            levels[node] = 0
        else:
            levels[node] = max(levels[pred] for pred in predecessors) + 1

    return levels


def get_parallel_task_groups(graph: nx.DiGraph) -> List[List[str]]:
    """
    Group tasks that can be executed in parallel.

    Args:
        graph: NetworkX DAG

    Returns:
        List of task groups, where each group can run in parallel
    """
    levels = get_task_levels(graph)

    # Group tasks by level
    max_level = max(levels.values()) if levels else 0
    groups = [[] for _ in range(max_level + 1)]

    for task_id, level in levels.items():
        groups[level].append(task_id)

    return groups


def get_critical_path(graph: nx.DiGraph, task_durations: Optional[Dict[str, float]] = None) -> List[str]:
    """
    Find the critical path through the DAG.

    Args:
        graph: NetworkX DAG
        task_durations: Optional dictionary of task durations

    Returns:
        List of task IDs in critical path
    """
    if task_durations is None:
        task_durations = {node: 1 for node in graph.nodes()}

    # Calculate earliest start times
    earliest_start = {}
    for node in nx.topological_sort(graph):
        predecessors = list(graph.predecessors(node))
        if not predecessors:
            earliest_start[node] = 0
        else:
            earliest_start[node] = max(
                earliest_start[pred] + task_durations[pred]
                for pred in predecessors
            )

    # Find the node with maximum earliest start + duration
    end_nodes = [node for node in graph.nodes() if graph.out_degree(node) == 0]
    if not end_nodes:
        return []

    critical_end = max(end_nodes, key=lambda n: earliest_start[n] + task_durations[n])

    # Backtrack to find critical path
    critical_path = [critical_end]
    current = critical_end

    while True:
        predecessors = list(graph.predecessors(current))
        if not predecessors:
            break

        # Find predecessor on critical path
        critical_pred = max(
            predecessors,
            key=lambda n: earliest_start[n] + task_durations[n]
        )
        critical_path.insert(0, critical_pred)
        current = critical_pred

    return critical_path


def detect_bottlenecks(graph: nx.DiGraph) -> List[str]:
    """
    Detect potential bottlenecks in the workflow.

    Args:
        graph: NetworkX DAG

    Returns:
        List of task IDs that are potential bottlenecks
    """
    bottlenecks = []

    for node in graph.nodes():
        # A bottleneck is a node with high in-degree or out-degree
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)

        if in_degree > 3 or out_degree > 3:
            bottlenecks.append(node)

    return bottlenecks


def estimate_workflow_duration(graph: nx.DiGraph, task_durations: Dict[str, float]) -> float:
    """
    Estimate total workflow duration assuming parallel execution.

    Args:
        graph: NetworkX DAG
        task_durations: Dictionary of task durations

    Returns:
        Estimated duration in same units as task_durations
    """
    if not graph.nodes():
        return 0.0

    # Get parallel task groups
    groups = get_parallel_task_groups(graph)

    # Total duration is sum of max duration in each group
    total_duration = 0.0
    for group in groups:
        group_duration = max(task_durations.get(task_id, 0) for task_id in group)
        total_duration += group_duration

    return total_duration


def generate_workflow_hash(workflow_definition: Dict[str, Any]) -> str:
    """
    Generate hash of workflow definition for versioning.

    Args:
        workflow_definition: Workflow definition dictionary

    Returns:
        Hash string
    """
    # Create deterministic JSON string
    workflow_json = json.dumps(workflow_definition, sort_keys=True)
    return hashlib.sha256(workflow_json.encode()).hexdigest()


def parse_cron_schedule(cron_expression: str) -> Dict[str, Any]:
    """
    Parse cron expression into components.

    Args:
        cron_expression: Cron expression string

    Returns:
        Dictionary with cron components
    """
    parts = cron_expression.split()

    if len(parts) != 5:
        raise ValueError("Invalid cron expression. Expected 5 fields.")

    return {
        'minute': parts[0],
        'hour': parts[1],
        'day_of_month': parts[2],
        'month': parts[3],
        'day_of_week': parts[4]
    }


def calculate_next_run(schedule: str, schedule_type: str = "cron",
                       current_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    Calculate next run time based on schedule.

    Args:
        schedule: Schedule expression
        schedule_type: Type of schedule (cron, interval)
        current_time: Current time (defaults to now)

    Returns:
        Next run datetime or None
    """
    if current_time is None:
        current_time = datetime.now()

    try:
        if schedule_type == "cron":
            # Simple cron parsing (would need croniter for full support)
            from croniter import croniter
            cron = croniter(schedule, current_time)
            return cron.get_next(datetime)
        elif schedule_type == "interval":
            # Interval in seconds
            interval_seconds = int(schedule)
            return current_time + timedelta(seconds=interval_seconds)
        else:
            return None
    except ImportError:
        logger.warning("croniter not installed, cron scheduling not fully supported")
        return None
    except Exception as e:
        logger.error(f"Error calculating next run: {e}")
        return None


def visualize_dag(graph: nx.DiGraph, output_format: str = "text") -> str:
    """
    Create a text visualization of the DAG.

    Args:
        graph: NetworkX DAG
        output_format: Output format (text, dot)

    Returns:
        Visualization string
    """
    if output_format == "text":
        lines = []
        levels = get_task_levels(graph)

        # Group by level
        max_level = max(levels.values()) if levels else 0
        for level in range(max_level + 1):
            tasks_at_level = [task for task, l in levels.items() if l == level]
            lines.append(f"Level {level}: {', '.join(tasks_at_level)}")

        return "\n".join(lines)

    elif output_format == "dot":
        # Generate DOT format for Graphviz
        lines = ["digraph workflow {"]
        for node in graph.nodes():
            lines.append(f'  "{node}";')
        for source, target in graph.edges():
            lines.append(f'  "{source}" -> "{target}";')
        lines.append("}")
        return "\n".join(lines)

    else:
        raise ValueError(f"Unsupported format: {output_format}")


def validate_task_dependencies(tasks: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate that task dependencies are valid.

    Args:
        tasks: List of task definitions

    Returns:
        Tuple of (is_valid, error_message)
    """
    task_ids = {task['id'] for task in tasks}

    for task in tasks:
        task_id = task['id']
        dependencies = task.get('dependencies', [])

        # Check for self-dependency
        if task_id in dependencies:
            return False, f"Task {task_id} depends on itself"

        # Check for non-existent dependencies
        for dep in dependencies:
            if dep not in task_ids:
                return False, f"Task {task_id} depends on non-existent task {dep}"

    return True, None


def merge_workflow_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge results from multiple workflow executions.

    Args:
        results: List of workflow execution results

    Returns:
        Merged results dictionary
    """
    merged = {
        'total_executions': len(results),
        'successful': sum(1 for r in results if r.get('status') == 'completed'),
        'failed': sum(1 for r in results if r.get('status') == 'failed'),
        'average_duration': 0.0,
        'total_tasks_executed': 0
    }

    if results:
        total_duration = sum(r.get('execution_time_seconds', 0) for r in results)
        merged['average_duration'] = total_duration / len(results)
        merged['total_tasks_executed'] = sum(r.get('completed_tasks', 0) for r in results)

    return merged


def optimize_workflow(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Analyze workflow and suggest optimizations.

    Args:
        graph: NetworkX DAG

    Returns:
        Dictionary with optimization suggestions
    """
    suggestions = []

    # Check for sequential tasks that could be parallelized
    groups = get_parallel_task_groups(graph)
    single_task_levels = sum(1 for group in groups if len(group) == 1)
    if single_task_levels > len(groups) / 2:
        suggestions.append({
            'type': 'parallelization',
            'message': 'Many tasks are sequential. Consider removing dependencies to enable parallel execution.'
        })

    # Check for bottlenecks
    bottlenecks = detect_bottlenecks(graph)
    if bottlenecks:
        suggestions.append({
            'type': 'bottleneck',
            'message': f'Tasks with high fan-in/fan-out detected: {", ".join(bottlenecks)}'
        })

    # Check for isolated nodes
    isolated = list(nx.isolates(graph))
    if isolated:
        suggestions.append({
            'type': 'isolated_tasks',
            'message': f'Isolated tasks detected: {", ".join(isolated)}'
        })

    return {
        'total_tasks': graph.number_of_nodes(),
        'max_parallelism': max(len(group) for group in groups) if groups else 0,
        'critical_path_length': len(get_critical_path(graph)),
        'suggestions': suggestions
    }
