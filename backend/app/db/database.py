import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config.settings import BackendSettings

logger = logging.getLogger(__name__)

settings = BackendSettings.load()
DATABASE_URL = settings.database_url

# SQLite requires specific arguments for multithreading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    try:
        from backend.app.models.user import User
        from backend.app.models.conversation import Conversation
        from backend.app.models.message import Message
        from backend.app.models.review_task import ReviewTask
        from backend.app.models.document import Document

        Base.metadata.create_all(bind=engine)
        logger.info("Application database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize application database: {e}")
        raise
