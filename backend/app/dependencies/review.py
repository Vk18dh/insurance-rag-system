from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated

from backend.app.dependencies.db import get_db
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.services.review_service import ReviewService

def get_review_service(db: Annotated[Session, Depends(get_db)]) -> ReviewService:
    repo = ReviewRepository(db)
    return ReviewService(review_repository=repo)
