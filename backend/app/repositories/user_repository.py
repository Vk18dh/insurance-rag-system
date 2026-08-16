from sqlalchemy.orm import Session
from typing import Optional
from backend.app.models.user import User
from backend.app.schemas.auth import UserCreate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
        
    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, user_create: UserCreate, hashed_password: str) -> User:
        db_user = User(
            username=user_create.username,
            hashed_password=hashed_password,
            role=user_create.role
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
