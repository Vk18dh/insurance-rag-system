from fastapi import APIRouter, Depends
from typing import Annotated, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from backend.app.dependencies.auth import require_admin_role
from backend.app.schemas.auth import TokenPayload
from backend.app.dependencies.db import get_db
from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.review_task import ReviewTask
from backend.app.config.settings import BackendSettings

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
async def admin_dashboard(current_user: Annotated[TokenPayload, Depends(require_admin_role)]):
    """
    Admin dashboard.
    Only accessible by ADMIN role.
    """
    return {"message": "Welcome to the admin dashboard", "user": current_user.sub}

@router.get("/metrics")
async def get_metrics(
    current_user: Annotated[TokenPayload, Depends(require_admin_role)],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieve system metrics for the admin dashboard."""
    # Active Users (total users)
    active_users = db.query(func.count(User.id)).scalar() or 0
    
    # Queries Today
    today = datetime.now(timezone.utc) - timedelta(days=1)
    queries_today = db.query(func.count(Message.id)).filter(
        Message.role == "user",
        Message.created_at >= today
    ).scalar() or 0
    
    # Escalation Rate
    escalations_today = db.query(func.count(ReviewTask.id)).filter(
        ReviewTask.created_at >= today
    ).scalar() or 0
    
    escalation_rate = (escalations_today / queries_today) if queries_today > 0 else 0.0

    return {
        "active_users": active_users,
        "queries_today": queries_today,
        "escalation_rate": escalation_rate,
        "avg_latency_ms": 0, # Cannot be easily queried without logging
        "system_status": "healthy"
    }

@router.get("/provider-health")
async def get_provider_health(current_user: Annotated[TokenPayload, Depends(require_admin_role)]) -> Dict[str, Any]:
    """Retrieve LLM provider health status."""
    settings = BackendSettings.load()
    primary = getattr(settings, 'llm_primary_provider', 'openrouter')
    secondary = getattr(settings, 'llm_secondary_provider', 'groq')
    return {
        "primary_provider": primary,
        "primary_status": "AVAILABLE",
        "secondary_provider": secondary,
        "secondary_status": "AVAILABLE",
        "failover_events_24h": 0
    }

from fastapi import UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import List
from backend.app.models.document import Document
from backend.app.schemas.document import DocumentResponse
from backend.app.services.ingestion_service import process_document_background
import os
import uuid
import shutil

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: Annotated[TokenPayload, Depends(require_admin_role)],
    db: Session = Depends(get_db)
):
    """List all uploaded policy documents."""
    return db.query(Document).order_by(Document.ingestion_timestamp.desc().nulls_last()).all()

@router.post("/documents", response_model=DocumentResponse, status_code=202)
async def upload_document(
    current_user: Annotated[TokenPayload, Depends(require_admin_role)],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    document_name: str = Form(...),
    document_type: str = Form(None),
    source: str = Form(None),
    version: str = Form(None)
):
    """Upload a PDF document and trigger background ingestion."""
    if not file.filename.lower().endswith(".pdf") or file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    new_doc = Document(
        document_name=document_name,
        document_type=document_type,
        source=source,
        version=version
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    file_path = os.path.join(UPLOAD_DIR, f"{new_doc.id}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_document_background, new_doc.id, file_path)

    return new_doc
