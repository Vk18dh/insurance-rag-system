from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class EvaluationCaseResultSchema(BaseModel):
    id: str
    run_id: str
    case_id: str
    query: str
    category: str
    
    generated_answer: Optional[str] = None
    retrieved_sources: Optional[str] = None
    
    retrieval_score: Optional[float] = None
    relevance_score: Optional[float] = None
    faithfulness_score: Optional[float] = None
    hallucination_score: Optional[float] = None
    citation_score: Optional[float] = None
    
    corpus_support: Optional[str] = None

    
    hitl_expected: bool
    hitl_actual: bool
    
    passed: bool
    evaluator_reason: Optional[str] = None
    raw_evaluator_output: Optional[str] = None
    parsed_success: bool
    evaluation_latency: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EvaluationRunSchema(BaseModel):
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    dataset_version: str
    evaluator_model: str
    evaluation_timestamp: datetime
    scoring_schema_version: str
    
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_score: float
    
    model_config = ConfigDict(from_attributes=True)

class EvaluationRunDetailSchema(EvaluationRunSchema):
    results: List[EvaluationCaseResultSchema] = []
    
class StartEvaluationResponse(BaseModel):
    run_id: str
    status: str
