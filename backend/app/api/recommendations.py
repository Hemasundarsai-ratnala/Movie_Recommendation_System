from fastapi import APIRouter, HTTPException
from backend.app.schemas import (
    SingleRecommendRequest,
    HybridRecommendRequest,
    PersonalizedRecommendRequest,
    RecommendationResponse,
)
from backend.app.services.recommender import engine

router = APIRouter(prefix="/recommend", tags=["Recommendations"])

@router.post("/single", response_model=RecommendationResponse)
def get_single_recommendation(request: SingleRecommendRequest):
    """Generates recommendations from a single seed movie title or ID."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded.")
    return engine.recommend_single(request)

@router.post("/hybrid", response_model=RecommendationResponse)
def get_hybrid_recommendation(request: HybridRecommendRequest):
    """Generates hybrid recommendations from multiple rated seed movies."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded.")
    return engine.recommend_hybrid(request)

@router.post("/personalized", response_model=RecommendationResponse)
def get_personalized_recommendation(request: PersonalizedRecommendRequest):
    """Generates personalized recommendations combining seeds and stated genre preferences."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded.")
    return engine.recommend_personalized(request)
