"""GamED.AI — FastAPI Application Entry Point (V4 Pipeline)"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

# Configure logging
from app.utils.logging_config import setup_logging, get_logger

log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(
    level=log_level,
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
    structured=os.getenv("STRUCTURED_LOGGING", "false").lower() == "true",
)

logger = get_logger("gamed_ai.main")

# Suppress Pydantic V1 deprecation warnings
import warnings
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*pydantic.v1.*", category=UserWarning)

# Import routes
from app.routes import generate

# Create FastAPI app
app = FastAPI(
    title="GamED.AI API",
    description="V4 Pipeline — Educational Game Generation",
    version="2.0.0",
)

# Rate limiter
from app.routes.generate import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger.info("GamED.AI API Starting (V4 Pipeline)")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    from app.db.database import init_db
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)


# CORS middleware
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID", "Accept", "Origin"],
    max_age=3600,
)

# Register routes
app.include_router(generate.router, prefix="/api", tags=["generate"])


@app.get("/")
async def root():
    return {"name": "GamED.AI", "version": "2.0.0", "pipeline": "V4"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
