import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.settings import BackendSettings
from backend.app.routers import query
from backend.app.middleware.logging import HTTPLoggingMiddleware
from backend.app.core.exceptions import add_exception_handlers

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

# Routers
app.include_router(query.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": settings.app.version, "components": {}}

@app.get("/api/v1/ready")
async def readiness_check():
    return {"status": "ready"}
