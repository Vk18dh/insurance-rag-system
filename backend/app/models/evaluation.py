from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.db.database import Base
import uuid

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    dataset_version = Column(String(100), nullable=False)
    evaluator_model = Column(String(100), nullable=False)
    evaluation_timestamp = Column(DateTime, default=datetime.utcnow)
    scoring_schema_version = Column(String(50), default="1.0")
    
    total_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    overall_score = Column(Float, default=0.0)

    results = relationship("EvaluationCaseResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationCaseResult(Base):
    __tablename__ = "evaluation_case_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("evaluation_runs.id"), nullable=False)
    case_id = Column(String(100), nullable=False)
    query = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    
    generated_answer = Column(Text, nullable=True)
    retrieved_sources = Column(Text, nullable=True) # Stored as JSON string
    
    retrieval_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    faithfulness_score = Column(Float, nullable=True)
    hallucination_score = Column(Float, nullable=True)
    citation_score = Column(Float, nullable=True)
    
    corpus_support = Column(String(50), nullable=True)

    
    hitl_expected = Column(Boolean, default=False)
    hitl_actual = Column(Boolean, default=False)
    
    passed = Column(Boolean, default=False)
    evaluator_reason = Column(Text, nullable=True)
    raw_evaluator_output = Column(Text, nullable=True)
    parsed_success = Column(Boolean, default=False)
    evaluation_latency = Column(Float, nullable=True) # Latency in ms
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("EvaluationRun", back_populates="results")
