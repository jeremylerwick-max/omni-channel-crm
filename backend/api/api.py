"""FastAPI Application - REST API for orchestrator.

Provides HTTP endpoints for task management, module queries, health checks,
and system monitoring.

Production-ready with error handling, validation, and OpenAPI docs.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from orchestrator.state import TaskState, TaskStatus, StepStatus
from orchestrator.registry import get_registry, init_registry
from orchestrator.secrets_manager import get_secrets_client
from orchestrator.sandbox import get_sandbox_manager, init_sandbox_manager
from orchestrator.budget import get_budget_tracker, init_budget_tracker
from orchestrator.scheduler import get_scheduler, init_scheduler, TaskPriority
from orchestrator.graph import get_orchestrator, init_orchestrator
from orchestrator.tracking import init_tracking, track_run, get_tracker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logger.info("🚀 Initializing orchestrator services...")
    
    # Initialize registry with manifests directory
    import os
    manifests_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manifests')
    init_registry(manifests_dir)
    
    # Load all manifests
    registry = get_registry()
    manifests = registry.load_all()
    logger.info(f"✅ Registry initialized with {len(manifests)} modules")
    
    # Initialize scheduler
    init_scheduler()
    logger.info("✅ Scheduler initialized")
    
    # Initialize budget tracker
    init_budget_tracker()
    logger.info("✅ Budget tracker initialized")
    
    # Initialize sandbox manager
    init_sandbox_manager()
    logger.info("✅ Sandbox manager initialized")
    
    # Initialize orchestrator graph with PostgreSQL checkpointer
    import os
    postgres_uri = os.getenv(
        'POSTGRES_URI',
        'postgresql://postgres:postgres@localhost:5432/orchestrator'
    )
    init_orchestrator(postgres_uri)
    logger.info("✅ Orchestrator graph initialized")

    # Initialize agent run tracking
    init_tracking()
    logger.info("✅ Agent run tracking initialized")

    logger.info("🎉 All services ready!")

    yield
    
    logger.info("👋 Shutting down orchestrator services...")


# Initialize FastAPI app
app = FastAPI(
    title="Agent Orchestrator API",
    description="Modular AI agent orchestration platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware to allow UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class TaskCreateRequest(BaseModel):
    """Request to create a new task."""
    owner: str = Field(..., description="Task owner identifier")
    requested_modules: List[str] = Field(..., description="List of module names to execute")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    priority: str = Field(default="medium", description="Task priority (low, medium, high, critical)")
    budget: Optional[Dict[str, Any]] = Field(default=None, description="Budget constraints")


class TaskResponse(BaseModel):
    """Response with task information."""
    task_id: str
    status: str
    owner: str
    steps: List[Dict]
    created_at: str
    updated_at: Optional[str] = None


class ModuleListResponse(BaseModel):
    """Response with list of available modules."""
    modules: List[Dict[str, Any]]
    count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    services: Dict[str, str]


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""
    pending_count: int
    active_count: int
    completed_count: int
    failed_count: int
    owner_counts: Dict[str, str]
    module_counts: Dict[str, str]


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Orchestrator API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of all services."""
    services = {}

    # Check registry
    try:
        registry = get_registry()
        manifests = registry.load_all()
        services["registry"] = f"ok ({len(manifests)} modules)"
    except Exception as e:
        services["registry"] = f"error: {str(e)}"

    # Check scheduler
    try:
        scheduler = get_scheduler()
        stats = scheduler.get_queue_stats()
        services["scheduler"] = f"ok ({stats.get('pending_count', 0)} pending)"
    except Exception as e:
        services["scheduler"] = f"error: {str(e)}"

    # Check sandbox manager
    try:
        sandbox_manager = get_sandbox_manager()
        sandboxes = sandbox_manager.list_sandboxes()
        services["sandboxes"] = f"ok ({len(sandboxes)} active)"
    except Exception as e:
        services["sandboxes"] = f"error: {str(e)}"

    # Check budget tracker
    try:
        tracker = get_budget_tracker()
        budgets = tracker.list_budgets()
        services["budget_tracker"] = f"ok ({len(budgets)} tracked)"
    except Exception as e:
        services["budget_tracker"] = f"error: {str(e)}"

    # Determine overall status
    has_errors = any("error" in status for status in services.values())
    overall_status = "degraded" if has_errors else "healthy"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        services=services
    )


@app.get("/modules", response_model=ModuleListResponse)
async def list_modules():
    """List all available modules."""
    try:
        registry = get_registry()
        modules = registry.list_modules()

        return ModuleListResponse(
            modules=modules,
            count=len(modules)
        )

    except Exception as e:
        logger.error(f"Failed to list modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list modules: {str(e)}"
        )


@app.get("/modules/{module_name}", response_model=Dict[str, Any])
async def get_module(module_name: str, version: Optional[str] = None):
    """Get details of a specific module."""
    try:
        registry = get_registry()
        manifest = registry.get_manifest(module_name, version)

        if not manifest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module not found: {module_name}"
            )

        return manifest.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get module: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get module: {str(e)}"
        )


@app.get("/modules/{module_name}/health", response_model=Dict[str, Any])
async def check_module_health(module_name: str, version: Optional[str] = None):
    """Check health of a specific module."""
    try:
        registry = get_registry()
        health = registry.check_health(module_name, version)

        return health

    except Exception as e:
        logger.error(f"Failed to check module health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check module health: {str(e)}"
        )


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    """Create and enqueue a new task."""
    try:
        # Generate task ID
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        # Map priority
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        priority = priority_map.get(request.priority.lower(), TaskPriority.MEDIUM)

        # Create initial state with all fields the graph needs
        initial_state = TaskState(
            task_id=task_id,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            owner=request.owner,
            status="PENDING",
            summary=None,
            dag_name="default",
            steps=[],
            current_node=None,
            budget=None,
            tags=[]
        )
        
        # Add extra fields needed by graph (TypedDict allows extra fields with total=False)
        initial_state['requested_modules'] = request.requested_modules
        initial_state['inputs'] = request.inputs
        initial_state['current_step'] = 0
        initial_state['context'] = {}
        initial_state['error'] = None
        initial_state['manifests'] = {}
        initial_state['outputs'] = {}

        # Enqueue task
        scheduler = get_scheduler()
        success = scheduler.enqueue(
            task_id=task_id,
            owner=request.owner,
            module_name=",".join(request.requested_modules),
            priority=priority,
            metadata={"inputs": request.inputs}
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enqueue task"
            )

        # Schedule background execution
        background_tasks.add_task(execute_task_background, task_id, initial_state)

        logger.info(f"Created task {task_id} for owner {request.owner}")

        return TaskResponse(
            task_id=task_id,
            status=initial_state['status'],
            owner=request.owner,
            steps=[],
            created_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get status of a specific task."""
    try:
        # In production, retrieve from database
        # For now, check scheduler
        scheduler = get_scheduler()
        stats = scheduler.get_queue_stats()

        # This is a simplified implementation
        return TaskResponse(
            task_id=task_id,
            status="active",
            owner="unknown",
            steps=[],
            created_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}"
        )


@app.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """Get queue statistics."""
    try:
        scheduler = get_scheduler()
        stats = scheduler.get_queue_stats()

        return QueueStatsResponse(
            pending_count=stats.get('pending_count', 0),
            active_count=stats.get('active_count', 0),
            completed_count=stats.get('completed_count', 0),
            failed_count=stats.get('failed_count', 0),
            owner_counts=stats.get('owner_counts', {}),
            module_counts=stats.get('module_counts', {})
        )

    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )


@app.get("/budget/{task_id}", response_model=Dict[str, Any])
async def get_task_budget(task_id: str):
    """Get budget information for a task."""
    try:
        tracker = get_budget_tracker()
        summary = tracker.get_summary(task_id)

        return summary

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget: {str(e)}"
        )


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    try:
        scheduler = get_scheduler()
        success = scheduler.fail_task(task_id, "Cancelled by user", retry=False)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}"
            )

        return {"status": "cancelled", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@app.post("/maintenance/cleanup")
async def run_cleanup():
    """Run maintenance cleanup tasks."""
    try:
        scheduler = get_scheduler()
        
        # Cleanup stale tasks
        scheduler.cleanup_stale_tasks(max_age_seconds=3600)
        
        # Cleanup old completed tasks
        scheduler.cleanup_old_completed(max_age_hours=24)
        
        # Cleanup old budgets
        tracker = get_budget_tracker()
        tracker.cleanup_expired(max_age_hours=24)

        return {"status": "cleanup completed"}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


# Background task execution
async def execute_task_background(task_id: str, initial_state: TaskState):
    """Execute task in background with automatic run tracking."""
    # Build goal from task state
    goal = f"Task {task_id}"
    if 'requested_modules' in initial_state:
        modules = initial_state['requested_modules']
        goal = f"{goal}: {', '.join(modules)}"
    if initial_state.get('summary'):
        goal = initial_state['summary']

    # Track the run
    with track_run(goal, provider="anthropic", model="claude-3-sonnet") as run:
        try:
            logger.info(f"🚀 Starting background execution for task {task_id}")

            # Store run in state for module access
            if run:
                initial_state['_tracking_run'] = run

            orchestrator = get_orchestrator()

            # Configure LangGraph checkpointer with thread_id
            from langgraph.checkpoint.base import RunnableConfig
            config = RunnableConfig(configurable={"thread_id": task_id})

            logger.info(f"Invoking orchestrator graph for task {task_id}...")
            result = await orchestrator.run(initial_state, config=config)

            logger.info(f"Graph completed for task {task_id}, status: {result.get('status')}")

            scheduler = get_scheduler()
            if result['status'] == "SUCCEEDED":
                scheduler.complete_task(task_id, result.get('outputs'))
                logger.info(f"✅ Task {task_id} completed successfully!")
                if run:
                    run.finalize(stop_reason="success")
            else:
                error_msg = result.get('error') or 'Task failed with unknown error'
                logger.error(f"❌ Task {task_id} failed: {error_msg}")
                scheduler.fail_task(task_id, error_msg, retry=False)
                if run:
                    run.finalize(stop_reason="error")

            logger.info(f"Task {task_id} finished with status: {result['status']}")

        except Exception as e:
            logger.error(f"❌ Background task execution failed for {task_id}: {e}", exc_info=True)
            if run:
                run.finalize(stop_reason="error")
            try:
                scheduler = get_scheduler()
                scheduler.fail_task(task_id, str(e), retry=False)
            except Exception as inner_e:
                logger.error(f"Failed to mark task as failed: {inner_e}")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# ============== SIMPLE EXECUTE ENDPOINT FOR UI ==============

class ExecuteRequest(BaseModel):
    """Simple execute request from UI."""
    module: str = Field(..., description="Module name to execute")
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class ExecuteResponse(BaseModel):
    """Simple execute response for UI."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    task_id: Optional[str] = None


@app.post("/execute", response_model=ExecuteResponse)
async def execute_simple(request: ExecuteRequest, background_tasks: BackgroundTasks):
    """
    Simple execute endpoint for UI compatibility.
    Transforms simple module/action/parameters format into task format.
    """
    try:
        # Generate task ID
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        # Transform the request into task format
        # The UI sends: {module, action, parameters}
        # We need to create: {owner, requested_modules, inputs}
        task_request = TaskCreateRequest(
            owner="ui_user",
            requested_modules=[request.module],
            inputs={
                "action": request.action,
                **request.parameters
            },
            priority="medium"
        )

        # Map priority
        priority = TaskPriority.MEDIUM

        # Create initial state
        initial_state = TaskState(
            task_id=task_id,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            owner=task_request.owner,
            status="PENDING",
            summary=None,
            dag_name="default",
            steps=[],
            current_node=None,
            budget=None,
            tags=[]
        )

        # Add extra fields
        initial_state['requested_modules'] = task_request.requested_modules
        initial_state['inputs'] = task_request.inputs
        initial_state['current_step'] = 0
        initial_state['context'] = {}
        initial_state['error'] = None
        initial_state['manifests'] = {}
        initial_state['outputs'] = {}

        # Enqueue task
        scheduler = get_scheduler()
        success = scheduler.enqueue(
            task_id=task_id,
            owner=task_request.owner,
            module_name=",".join(task_request.requested_modules),
            priority=priority,
            metadata={"inputs": task_request.inputs}
        )

        if not success:
            return ExecuteResponse(
                success=False,
                error="Failed to enqueue task",
                task_id=task_id
            )

        # Schedule background execution
        background_tasks.add_task(execute_task_background, task_id, initial_state)

        logger.info(f"✓ UI Execute: {request.module}.{request.action} -> task {task_id}")

        return ExecuteResponse(
            success=True,
            data={
                "task_id": task_id,
                "module": request.module,
                "action": request.action,
                "status": "executing"
            },
            task_id=task_id
        )

    except Exception as e:
        logger.error(f"Execute failed: {e}", exc_info=True)
        return ExecuteResponse(
            success=False,
            error=str(e)
        )


# ============== BROWSER AUTOMATION ENDPOINT ==============

class BrowserExecuteRequest(BaseModel):
    """Browser automation request."""
    action: str = Field(..., description="navigate|click|type|wait_for|screenshot|auto_paginate")
    url: Optional[str] = Field(None, description="Target URL")
    selector: Optional[str] = Field(None, description="CSS selector or XPath")
    text: Optional[str] = Field(None, description="Text to type")
    description: Optional[str] = Field(None, description="Natural language description for vision")
    data_selector: str = Field(".result-item", description="Selector for pagination")
    max_attempts: int = Field(3, description="Max retry attempts")
    session_id: Optional[str] = Field(None, description="Reuse existing browser session")
    keep_alive: bool = Field(False, description="Keep browser open after action")

class BrowserExecuteResponse(BaseModel):
    """Browser automation response."""
    status: str
    data: Dict[str, Any]
    error: Optional[str] = None

@app.post("/browser/execute", response_model=BrowserExecuteResponse)
async def browser_execute_endpoint(request: BrowserExecuteRequest):
    """Execute browser automation with vision support and session persistence."""
    try:
        from modules.browser_playwright import execute_with_session
        
        result = await execute_with_session(request.dict())
        
        logger.info(
            f"Browser: {request.action} on {request.url} - "
            f"session: {result.get('data', {}).get('metadata', {}).get('session_id', 'none')} - "
            f"cost: ${result.get('data', {}).get('cost_usd', 0)}"
        )
        return BrowserExecuteResponse(**result)
        
    except Exception as e:
        logger.error(f"Browser automation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Browser automation failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============== BROWSER SESSION MANAGEMENT ==============

@app.post("/browser/session/close")
async def close_browser_session(session_id: str):
    """Close a browser session."""
    from modules.browser_playwright import execute_with_session
    result = await execute_with_session({"action": "close_session", "session_id": session_id})
    return result

@app.get("/browser/sessions")
async def list_browser_sessions():
    """List all active browser sessions."""
    from modules.browser_playwright import execute_with_session
    result = await execute_with_session({"action": "list_sessions"})
    return result

@app.post("/browser/sessions/cleanup")
async def cleanup_browser_sessions():
    """Clean up old browser sessions (>30 min)."""
    from modules.browser_playwright import execute_with_session
    result = await execute_with_session({"action": "cleanup_sessions"})
    return result


# Include queue management endpoints
from orchestrator.queue_api import router as queue_router
app.include_router(queue_router)

# Include CRM endpoints
from orchestrator.crm_api import router as crm_router
app.include_router(crm_router)

# Include Twilio webhook endpoints
from orchestrator.twilio_webhooks import router as twilio_router
app.include_router(twilio_router)

# Include Natural Language CRM control endpoints
from orchestrator.nl_api import router as nl_router
app.include_router(nl_router)

