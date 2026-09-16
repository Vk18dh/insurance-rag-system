from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Annotated, List
from sqlalchemy.orm import Session
from backend.app.dependencies.db import get_db
from backend.app.dependencies.auth import require_admin_role
from backend.app.schemas.auth import TokenPayload
from backend.app.schemas.evaluation import EvaluationRunSchema, EvaluationRunDetailSchema, StartEvaluationResponse
from backend.app.models.evaluation import EvaluationRun, EvaluationCaseResult
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/admin/evaluations", tags=["admin", "evaluation"])

@router.post("", response_model=StartEvaluationResponse)
def start_evaluation(
    background_tasks: BackgroundTasks,
    current_admin: Annotated[TokenPayload, Depends(require_admin_role)],
    db: Session = Depends(get_db)
):
    """
    Start a new evaluation run against the dataset in the background.
    """
    try:
        from phase2.config.settings import get_settings
        settings = get_settings()
        
        new_run = EvaluationRun(
            dataset_version="1.0", # Will be updated when dataset is loaded
            evaluator_model="qwen2.5:3b", # Local Ollama judge
            status="QUEUED"
        )
        db.add(new_run)
        db.commit()
        db.refresh(new_run)
        
        evaluation_service = EvaluationService(db)
        background_tasks.add_task(evaluation_service.run_evaluation_background, new_run.id)
        
        return StartEvaluationResponse(run_id=new_run.id, status="QUEUED")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[EvaluationRunSchema])
def get_evaluation_runs(
    current_admin: Annotated[TokenPayload, Depends(require_admin_role)],
    db: Session = Depends(get_db)
):
    """
    List all evaluation runs.
    """
    runs = db.query(EvaluationRun).order_by(EvaluationRun.started_at.desc()).all()
    return runs

@router.get("/{run_id}", response_model=EvaluationRunDetailSchema)
def get_evaluation_run(
    run_id: str,
    current_admin: Annotated[TokenPayload, Depends(require_admin_role)],
    db: Session = Depends(get_db)
):
    """
    Get details of a specific evaluation run including case results.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run
