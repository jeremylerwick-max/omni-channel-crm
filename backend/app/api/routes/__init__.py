from fastapi import APIRouter
from app.api.routes import contacts, messages, conversations, workflows, webhooks

router = APIRouter()

# Include all route modules
router.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
router.include_router(messages.router, prefix="/messages", tags=["Messages"])
router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

@router.get("/")
async def api_root():
    return {"message": "Omni-Channel CRM API", "version": "1.0"}
