from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from backend.app.models.document import DocumentStatus

class DocumentBase(BaseModel):
    document_name: str
    document_type: Optional[str] = None
    source: Optional[str] = None
    version: Optional[str] = None
    publication_date: Optional[datetime] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    ingestion_timestamp: Optional[datetime] = None
    status: DocumentStatus
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
