import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, Text
from backend.app.db.database import Base

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_name = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    source = Column(String, nullable=True)
    version = Column(String, nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    ingestion_timestamp = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
