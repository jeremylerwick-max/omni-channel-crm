from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_db
from app.models import Contact, ContactStatus

router = APIRouter()

# ============ SCHEMAS ============

class ContactCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: List[str] = []
    custom_fields: dict = {}
    source: Optional[str] = None
    sms_consent: bool = False
    email_consent: bool = False

class ContactUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[dict] = None
    status: Optional[ContactStatus] = None
    do_not_disturb: bool = False

class ContactResponse(BaseModel):
    id: UUID
    email: Optional[str]
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    status: ContactStatus
    tags: List[str]
    custom_fields: dict
    do_not_disturb: bool
    sms_consent: bool
    email_consent: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============ ROUTES ============

# Default account ID for MVP (multi-tenant later)
DEFAULT_ACCOUNT_ID = "00000000-0000-0000-0000-000000000001"

@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[ContactStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """List contacts with filtering and pagination."""
    query = select(Contact).where(Contact.account_id == DEFAULT_ACCOUNT_ID)
    
    if search:
        query = query.where(or_(
            Contact.email.ilike(f"%{search}%"),
            Contact.phone.ilike(f"%{search}%"),
            Contact.first_name.ilike(f"%{search}%"),
            Contact.last_name.ilike(f"%{search}%")
        ))
    
    if tag:
        query = query.where(Contact.tags.contains([tag]))
    
    if status:
        query = query.where(Contact.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Contact.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/count")
async def count_contacts(
    status: Optional[ContactStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get contact count."""
    query = select(func.count(Contact.id)).where(Contact.account_id == DEFAULT_ACCOUNT_ID)
    if status:
        query = query.where(Contact.status == status)
    result = await db.execute(query)
    return {"count": result.scalar()}

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single contact by ID."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.account_id == DEFAULT_ACCOUNT_ID)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.post("/", response_model=ContactResponse)
async def create_contact(data: ContactCreate, db: AsyncSession = Depends(get_db)):
    """Create a new contact."""
    contact = Contact(
        account_id=DEFAULT_ACCOUNT_ID,
        **data.model_dump()
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return contact

@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: UUID, data: ContactUpdate, db: AsyncSession = Depends(get_db)):
    """Update a contact."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.account_id == DEFAULT_ACCOUNT_ID)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    contact.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(contact)
    return contact

@router.delete("/{contact_id}")
async def delete_contact(contact_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a contact."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.account_id == DEFAULT_ACCOUNT_ID)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await db.delete(contact)
    return {"deleted": True, "id": str(contact_id)}

@router.post("/{contact_id}/tags/{tag}")
async def add_tag(contact_id: UUID, tag: str, db: AsyncSession = Depends(get_db)):
    """Add a tag to a contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if tag not in contact.tags:
        contact.tags = contact.tags + [tag]
        contact.updated_at = datetime.utcnow()
    
    return {"tags": contact.tags}

@router.delete("/{contact_id}/tags/{tag}")
async def remove_tag(contact_id: UUID, tag: str, db: AsyncSession = Depends(get_db)):
    """Remove a tag from a contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    if tag in contact.tags:
        contact.tags = [t for t in contact.tags if t != tag]
        contact.updated_at = datetime.utcnow()
    
    return {"tags": contact.tags}
