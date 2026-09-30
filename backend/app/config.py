import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "FoodSafe-Indic FSSAI Compliance Checker"
    API_V1_STR: str = "/api"
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    REGULATIONS_DIR: Path = BASE_DIR / "data" / "fssai_regulations"
    CHROMA_DB_DIR: Path = BASE_DIR / "data" / "chroma_db"
    TEST_SAMPLES_DIR: Path = BASE_DIR / "data" / "test_samples"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/foodsafe.db"
    
    # AI / LLM Configuration
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SARVAM_BASE_URL: str = "https://api.sarvam.ai"
    SARVAM_LLM_MODEL: str = "sarvam-2b"
    SARVAM_STT_MODEL: str = "saarika:v2"
    
    # Remote Kaggle / Ngrok / Colab LLM Server URL
    REMOTE_LLM_URL: str = os.getenv("REMOTE_LLM_URL", "")
    KAGGLE_NGROK_URL: str = os.getenv("KAGGLE_NGROK_URL", "")
    
    # Offline fallback settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    LOCAL_WHISPER_MODEL: str = "tiny"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure runtime directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REGULATIONS_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
settings.TEST_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
