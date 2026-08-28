import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

from contextlib import asynccontextmanager
from database.connection import db_manager, redis_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("prepsense.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize durable database tables and Redis connection on startup."""
    try:
        await db_manager.init_tables()
        await redis_manager.get_client()
        logger.info("PrepSense API: Database tables and Redis connections initialized.")
    except Exception as e:
        logger.error(f"PrepSense API: Startup initialization error: {e}")
    yield
    try:
        await db_manager.close()
        await redis_manager.close()
        logger.info("PrepSense API: Database and Redis connections closed.")
    except Exception as e:
        logger.error(f"PrepSense API: Shutdown cleanup error: {e}")


app = FastAPI(
    title="PrepSense Assessment API",
    description="Adaptive Technical & Behavioral Assessment Engine API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local Next.js development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming HTTP requests with latency metrics."""
    t0 = time.perf_counter()
    response = await call_next(request)
    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({latency_ms}ms)")
    return response


# Include Routers
app.include_router(router)

from .voice_ws import ws_router
app.include_router(ws_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": "PrepSense Assessment API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "status": "online"
    }

