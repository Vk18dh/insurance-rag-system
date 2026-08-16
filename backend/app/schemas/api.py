from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    """Standard payload expected by POST /api/v1/query"""
    query: str
    language: str = "en"
    customer_id: Optional[str] = None
    conversation_id: Optional[str] = None

class RetrievedSource(BaseModel):
    """Information regarding a cited document chunk"""
    document: str
    page: int
    content_snippet: str
    confidence: float

class QueryResponse(BaseModel):
    """Standardized frontend response mapping the ResponseBuilder output"""
    query_id: str
    conversation_id: Optional[str] = None
    final_answer: str
    confidence_score: float
    is_safe: bool
    sources: List[RetrievedSource]
    execution_time_ms: float

class ComponentHealth(BaseModel):
    status: str
    details: Optional[str] = None

class HealthResponse(BaseModel):
    """Standard payload expected by GET /api/v1/health"""
    status: str
    version: str
    components: Dict[str, ComponentHealth]

class StandardResponse(BaseModel):
    """Generic payload for basic confirmations (e.g. POST /reindex)"""
    message: str
    status_code: int = 200
