import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.app.schemas.api import StandardResponse

# We safely import Phase2Exception if it's available, otherwise fallback gracefully
try:
    from phase2.exceptions import Phase2Exception
    HAS_PHASE2 = True
except ImportError:
    HAS_PHASE2 = False
    
logger = logging.getLogger("FastAPI.Exceptions")

def add_exception_handlers(app: FastAPI):
    """
    Registers global exception handlers enforcing security protocols where internal
    stack traces are completely sanitized and shielded from the end client.
    """
    
    if HAS_PHASE2:
        @app.exception_handler(Phase2Exception)
        async def phase2_exception_handler(request: Request, exc: "Phase2Exception"):
            logger.error(f"Phase 2 Business Logic Error: {str(exc)}")
            return JSONResponse(
                status_code=400, # or 422 depending on precise exception parsing
                content=StandardResponse(
                    message="The AI engine could not process your request due to an internal rule.",
                    status_code=400
                ).model_dump()
            )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch-all to prevent stack trace leaks securely mapping 500s."""
        logger.error(f"Unhandled Server Error at {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=StandardResponse(
                message="Internal Server Error. Please contact an administrator.",
                status_code=500
            ).model_dump()
        )
