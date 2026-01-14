import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Workflow(Base):
    """Automation workflows."""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")  # draft, active, paused, archived
    
    # Workflow definition (YAML/JSON parsed)
    definition = Column(JSONB, nullable=False, default={})
    version = Column(Integer, default=1)
    
    # Visual builder data
    canvas_data = Column(JSONB, default={})  # React Flow node positions
    
    # Trigger config
    trigger_type = Column(String(50))  # manual, tag_added, contact_created, sms_received, etc.
    trigger_config = Column(JSONB, default={})
    
    # Stats
    enrolled_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="workflows")
    enrollments = relationship("WorkflowEnrollment", back_populates="workflow")
    
    __table_args__ = (
        Index("ix_workflows_account_status", "account_id", "status"),
    )

class WorkflowEnrollment(Base):
    """Contact enrollment in a workflow."""
    __tablename__ = "workflow_enrollments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False)
    
    status = Column(String(20), default="active")  # active, completed, paused, failed
    current_step = Column(String(100))
    current_step_index = Column(Integer, default=0)
    
    # State machine data
    state = Column(JSONB, default={})
    
    # Timing
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    next_action_at = Column(DateTime)  # When the next step should execute
    
    # Relationships
    workflow = relationship("Workflow", back_populates="enrollments")
    
    __table_args__ = (
        Index("ix_enrollments_next_action", "next_action_at"),
        Index("ix_enrollments_workflow_status", "workflow_id", "status"),
    )

class Campaign(Base):
    """Marketing campaigns (grouping of workflow executions)."""
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")  # draft, scheduled, running, completed, paused
    
    # Target segment
    segment_filters = Column(JSONB, default={})
    target_count = Column(Integer, default=0)
    
    # Schedule
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Stats
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="campaigns")
