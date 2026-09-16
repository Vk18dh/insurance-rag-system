import sys
import os
sys.path.append(os.getcwd())

from backend.app.db.database import SessionLocal
from backend.app.models.evaluation import EvaluationRun, EvaluationCaseResult

db = SessionLocal()
runs = db.query(EvaluationRun).all()
print(f"Total runs: {len(runs)}")
for run in runs:
    print(f"Run {run.id}: {run.passed_cases} passed, {run.failed_cases} failed")
    
cases = db.query(EvaluationCaseResult).all()
for c in cases:
    print(f"Case {c.case_id}: passed={c.passed}, parsed_success={c.parsed_success}, reason={c.evaluator_reason}, raw={c.raw_evaluator_output}")
    print("---")
