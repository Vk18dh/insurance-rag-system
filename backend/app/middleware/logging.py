import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.config.settings import BackendSettings

logger = logging.getLogger("FastAPI.HTTP")
logger.setLevel(logging.INFO)

# Basic console handler
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request incoming
        logger.info(f"Incoming Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        formatted_process_time = '{0:.2f}'.format(process_time)
        
        # Log response outgoing
        logger.info(
            f"Completed Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Duration: {formatted_process_time}ms"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
