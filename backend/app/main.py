import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .database import init_db
from .routers import audit, chat, incidents, test_cases
from .services.rag_service import rag_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="End-to-End Multilingual NLP System for FSSAI Food Safety and Regulatory Compliance Verification",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite / Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for uploaded packaging photos and sample images
app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/static/test_samples", StaticFiles(directory=str(settings.TEST_SAMPLES_DIR)), name="test_samples")

# Include API Routers
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(incidents.router, prefix=settings.API_V1_STR)
app.include_router(test_cases.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing FoodSafe-Indic backend services...")
    init_db()
    logger.info("Database initialized.")
    # Ensure RAG knowledge base is loaded
    logger.info(f"RAG Corpus status: {len(rag_service.documents)} FSSAI clauses ready.")

@app.get("/")
def root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_STR
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "rag_clauses_loaded": len(rag_service.documents),
        "sarvam_api_configured": bool(settings.SARVAM_API_KEY)
    }
