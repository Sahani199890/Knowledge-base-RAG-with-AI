import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import init_db
from app.api.routes import router
from app.services.document_queue import document_store_queue
from app.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    init_db()
    # Start the asynchronous document store queue worker
    await document_store_queue.start()
    yield
    # Gracefully stop the worker
    await document_store_queue.stop()
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Minimal AI Knowledge Inbox with LangChain & Unstructured RAG Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing and container environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing and structured logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} responded {response.status_code} in {duration_ms}ms",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        }
    )
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs."}
    )

# Mount routes at root and /api for maximum client compatibility
app.include_router(router, tags=["Knowledge Inbox"])
app.include_router(router, prefix="/api", tags=["API V1"])

@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
