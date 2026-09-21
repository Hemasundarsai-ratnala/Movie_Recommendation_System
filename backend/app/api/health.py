from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas import HealthResponse
from backend.app.services.recommender import engine

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy" if engine.is_loaded else "degraded",
        version=settings.VERSION,
        model_artifacts_loaded=engine.is_loaded,
        manifest=engine.manifest,
    )
