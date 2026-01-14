import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# ============ ENUMS ============

class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"

class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    WHATSAPP = "whatsapp"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"

class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    ARCHIVED = "archived"

# ============ CORE MODELS ============

class Account(Base):
    """Multi-tenant account (company/agency)."""
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE)
    
    # Settings
    settings = Column(JSONB, default={})
    timezone = Column(String(50), default="America/Denver")
    
    # Billing
    stripe_customer_id = Column(String(100))
    subscription_tier = Column(String(50), default="starter")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="account")
    contacts = relationship("Contact", back_populates="account")
    workflows = relationship("Workflow", back_populates="account")
    campaigns = relationship("Campaign", back_populates="account")

class User(Base):
    """Platform users."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    role = Column(String(50), default="member")  # admin, member, viewer
    
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("Account", back_populates="users")

class Contact(Base):
    """CRM contacts/leads."""
    __tablename__ = "contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Core fields
    email = Column(String(255))
    phone = Column(String(20))
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Status & Compliance
    status = Column(SQLEnum(ContactStatus), default=ContactStatus.ACTIVE)
    sms_consent = Column(Boolean, default=False)
    email_consent = Column(Boolean, default=False)
    do_not_disturb = Column(Boolean, default=False)
    
    # Custom fields
    custom_fields = Column(JSONB, default={})
    tags = Column(ARRAY(String), default=[])
    
    # Source tracking
    source = Column(String(100))
    source_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contacted_at = Column(DateTime)
    
    # Relationships
    account = relationship("Account", back_populates="contacts")
    messages = relationship("Message", back_populates="contact")
    conversations = relationship("Conversation", back_populates="contact")
    
    __table_args__ = (
        Index("ix_contacts_account_phone", "account_id", "phone"),
        Index("ix_contacts_account_email", "account_id", "email"),
        Index("ix_contacts_tags", "tags", postgresql_using="gin"),
    )

class Tag(Base):
    """Reusable tags for contacts."""
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#3B82F6")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("account_id", "name", name="uq_tag_account_name"),
    )
