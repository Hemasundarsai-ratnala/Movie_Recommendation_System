import sys
import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def _get_env_str(key: str, default: str) -> str:
    val = os.getenv(key)
    return val.strip() if val is not None and val.strip() != "" else default

def _get_env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is not None and val.strip() != "":
        try:
            return int(val.strip())
        except ValueError:
            return default
    return default

def _get_env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is not None and val.strip() != "":
        try:
            return float(val.strip())
        except ValueError:
            return default
    return default

DATA_DIR = Path(_get_env_str("DATA_DIR", str(BASE_DIR / "data")))
MODEL_DIR = Path(_get_env_str("MODEL_DIR", str(BASE_DIR / "backend" / "app" / "models")))

class Settings(BaseModel):
    PROJECT_NAME: str = "Hybrid Movie Recommendation System"
    VERSION: str = "1.0.0"
    
    # Paths
    DATA_DIR: Path = DATA_DIR
    MOVIES_CSV: Path = DATA_DIR / "movies.csv"
    RATINGS_CSV: Path = DATA_DIR / "ratings.csv"
    MODEL_DIR: Path = MODEL_DIR
    
    # Server & Security
    BACKEND_HOST: str = _get_env_str("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = _get_env_int("PORT", _get_env_int("BACKEND_PORT", 8000))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in _get_env_str(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175",
        ).split(",")
        if origin.strip()
    ]
    
    # Model parameters
    MIN_COMMON_RATINGS: int = _get_env_int("MIN_COMMON_RATINGS", 20)
    SHRINKAGE_LAMBDA: float = _get_env_float("SHRINKAGE_LAMBDA", 25.0)
    TOP_K_NEIGHBOURS: int = _get_env_int("TOP_K_NEIGHBOURS", 200)
    
    FUZZY_HIGH_THRESHOLD: float = _get_env_float("FUZZY_HIGH_THRESHOLD", 85.0)
    FUZZY_MEDIUM_THRESHOLD: float = _get_env_float("FUZZY_MEDIUM_THRESHOLD", 60.0)
    
    CONTENT_WEIGHT: float = _get_env_float("CONTENT_WEIGHT", 0.45)
    COLLABORATIVE_WEIGHT: float = _get_env_float("COLLABORATIVE_WEIGHT", 0.45)
    POPULARITY_WEIGHT: float = _get_env_float("POPULARITY_WEIGHT", 0.10)
    
    POPULARITY_PRIOR_M: float = _get_env_float("POPULARITY_PRIOR_M", 50.0)
    NEUTRAL_BASELINE: float = _get_env_float("NEUTRAL_BASELINE", 3.0)
    DIVERSITY_LAMBDA: float = _get_env_float("DIVERSITY_LAMBDA", 0.7)
    TOP_N_DEFAULT: int = _get_env_int("TOP_N_DEFAULT", 10)
    RELEVANCE_THRESHOLD: float = _get_env_float("RELEVANCE_THRESHOLD", 4.0)

settings = Settings()
