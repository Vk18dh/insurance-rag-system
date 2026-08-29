from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.dependencies.db import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.schemas.auth import TokenPayload
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.services.conversation_service import ConversationService
from backend.app.services.review_service import ReviewService
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.schemas.review_task import ReviewTaskResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])

def get_conversation_service(db: Annotated[Session, Depends(get_db)]) -> ConversationService:
    repo = ConversationRepository(db)
    return ConversationService(conversation_repository=repo)

def get_review_service(db: Annotated[Session, Depends(get_db)]) -> ReviewService:
    repo = ReviewRepository(db)
    return ReviewService(review_repository=repo)

class ConversationResponse(BaseModel):
    id: str
    title: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str

class ConversationCreateRequest(BaseModel):
    title: str = "New Conversation"

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    conv = conversation_service.create_conversation(user_id=current_user.sub, title=request.title)
    conversation_service.commit()
    return ConversationResponse(id=conv.id, title=conv.title)

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    convs = conversation_service.get_user_conversations(user_id=current_user.sub)
    return [ConversationResponse(id=c.id, title=c.title) for c in convs]

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    conv = conversation_service.get_conversation_by_id(conversation_id, current_user.sub)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(id=conv.id, title=conv.title)

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    messages = conversation_service.get_messages(conversation_id, current_user.sub)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [MessageResponse(id=m.id, role=m.role, content=m.content) for m in messages]

@router.get("/{conversation_id}/reviews", response_model=List[ReviewTaskResponse])
async def get_conversation_reviews(
    conversation_id: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    conversation_service: ConversationService = Depends(get_conversation_service),
    review_service: ReviewService = Depends(get_review_service)
):
    # Verify ownership
    conv = conversation_service.get_conversation_by_id(conversation_id, current_user.sub)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    tasks = review_service.list_tasks_by_conversation(conversation_id)
    return tasks

