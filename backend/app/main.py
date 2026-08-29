import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.settings import BackendSettings
from backend.app.routers import query, auth, conversations, expert, admin
from backend.app.middleware.logging import HTTPLoggingMiddleware
from backend.app.core.exceptions import add_exception_handlers
from backend.app.db.database import init_db

settings = BackendSettings.load()

app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(HTTPLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
add_exception_handlers(app)

# Initialize Database
@app.on_event("startup")
def startup_event():
    init_db()
    
    # Dev seed mechanism
    dev_expert_pwd = os.environ.get("DEV_EXPERT_PASSWORD")
    dev_admin_pwd = os.environ.get("DEV_ADMIN_PASSWORD")
    
    if dev_expert_pwd or dev_admin_pwd:
        import logging
        from backend.app.db.database import SessionLocal
        from backend.app.schemas.auth import Role
        from backend.app.repositories.user_repository import UserRepository
        from backend.app.services.auth_service import AuthService
        from backend.app.schemas.auth import UserCreate
        
        logger = logging.getLogger(__name__)
        db = SessionLocal()
        try:
            repo = UserRepository(db)
            auth_svc = AuthService(repo)
            
            if dev_expert_pwd:
                if not repo.get_by_username("expert"):
                    logger.info("Seeding DEV expert account...")
                    hashed = auth_svc.get_password_hash(dev_expert_pwd)
                    repo.create(UserCreate(username="expert", password=dev_expert_pwd, role=Role.EXPERT), hashed)
                    
            if dev_admin_pwd:
                if not repo.get_by_username("admin"):
                    logger.info("Seeding DEV admin account...")
                    hashed = auth_svc.get_password_hash(dev_admin_pwd)
                    repo.create(UserCreate(username="admin", password=dev_admin_pwd, role=Role.ADMIN), hashed)
                    
            db.commit()
        except Exception as e:
            logger.error(f"Failed to seed dev accounts: {e}")
            db.rollback()
        finally:
            db.close()

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(expert.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": settings.app.version, "components": {}}

@app.get("/api/v1/ready")
async def readiness_check():
    return {"status": "ready"}
