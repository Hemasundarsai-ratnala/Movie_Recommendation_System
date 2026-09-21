import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
MODEL_DIR = Path(os.getenv("MODEL_DIR", str(BASE_DIR / "backend" / "app" / "models")))

class Settings(BaseModel):
    PROJECT_NAME: str = "Hybrid Movie Recommendation System"
    VERSION: str = "1.0.0"
    
    # Paths
    DATA_DIR: Path = DATA_DIR
    MOVIES_CSV: Path = DATA_DIR / "movies.csv"
    RATINGS_CSV: Path = DATA_DIR / "ratings.csv"
    MODEL_DIR: Path = MODEL_DIR
    
    # Server & Security
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175").split(",")
    ]
    
    # Model parameters
    MIN_COMMON_RATINGS: int = int(os.getenv("MIN_COMMON_RATINGS", "20"))
    SHRINKAGE_LAMBDA: float = float(os.getenv("SHRINKAGE_LAMBDA", "25.0"))
    TOP_K_NEIGHBOURS: int = int(os.getenv("TOP_K_NEIGHBOURS", "200"))
    
    FUZZY_HIGH_THRESHOLD: float = float(os.getenv("FUZZY_HIGH_THRESHOLD", "85.0"))
    FUZZY_MEDIUM_THRESHOLD: float = float(os.getenv("FUZZY_MEDIUM_THRESHOLD", "60.0"))
    
    CONTENT_WEIGHT: float = float(os.getenv("CONTENT_WEIGHT", "0.45"))
    COLLABORATIVE_WEIGHT: float = float(os.getenv("COLLABORATIVE_WEIGHT", "0.45"))
    POPULARITY_WEIGHT: float = float(os.getenv("POPULARITY_WEIGHT", "0.10"))
    
    POPULARITY_PRIOR_M: float = float(os.getenv("POPULARITY_PRIOR_M", "50.0"))
    NEUTRAL_BASELINE: float = float(os.getenv("NEUTRAL_BASELINE", "3.0"))
    DIVERSITY_LAMBDA: float = float(os.getenv("DIVERSITY_LAMBDA", "0.7"))
    TOP_N_DEFAULT: int = int(os.getenv("TOP_N_DEFAULT", "10"))
    RELEVANCE_THRESHOLD: float = float(os.getenv("RELEVANCE_THRESHOLD", "4.0"))

settings = Settings()
