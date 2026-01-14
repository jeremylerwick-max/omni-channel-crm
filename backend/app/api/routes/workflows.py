from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.models import Workflow, WorkflowEnrollment

router = APIRouter()

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: dict = {}
    definition: dict = {}

class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    trigger_type: Optional[str]
    enrolled_count: int
    completed_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

DEFAULT_ACCOUNT_ID = "00000000-0000-0000-0000-000000000001"

@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List workflows."""
    query = select(Workflow).where(Workflow.account_id == DEFAULT_ACCOUNT_ID)
    if status:
        query = query.where(Workflow.status == status)
    query = query.order_by(Workflow.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(data: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    """Create a new workflow."""
    workflow = Workflow(account_id=DEFAULT_ACCOUNT_ID, **data.model_dump())
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return workflow

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get workflow by ID."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.get("/{workflow_id}/definition")
async def get_workflow_definition(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get workflow definition (YAML/JSON config)."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"definition": workflow.definition, "canvas_data": workflow.canvas_data}

@router.patch("/{workflow_id}/status")
async def update_workflow_status(
    workflow_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Activate/pause/archive a workflow."""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.status = status
    workflow.updated_at = datetime.utcnow()
    return {"id": str(workflow_id), "status": status}

@router.post("/{workflow_id}/enroll/{contact_id}")
async def enroll_contact(
    workflow_id: UUID,
    contact_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Enroll a contact in a workflow."""
    enrollment = WorkflowEnrollment(
        workflow_id=workflow_id,
        contact_id=contact_id,
        status="active",
        current_step_index=0
    )
    db.add(enrollment)
    await db.flush()
    
    # Update workflow stats
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if workflow:
        workflow.enrolled_count += 1
    
    return {"enrolled": True, "enrollment_id": str(enrollment.id)}
