from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from backend.app.schemas import MovieSummary
from backend.app.services.recommender import engine

router = APIRouter(prefix="/movies", tags=["Movies"])

@router.get("/search")
def search_movies(
    q: str = Query(..., min_length=1, description="Movie title search query"),
    limit: int = Query(default=10, ge=1, le=50),
) -> List[Dict[str, Any]]:
    """Autocomplete movie search endpoint using alias fuzzy index."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded. System is initializing.")
    return engine.fuzzy_matcher.search_autocomplete(q, limit=limit)

@router.get("/{movie_id}", response_model=MovieSummary)
def get_movie_by_id(movie_id: int):
    """Retrieve detailed metadata for a single movie by integer movieId."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded.")
    if movie_id not in engine.movie_metadata:
        raise HTTPException(status_code=404, detail=f"Movie ID {movie_id} not found.")

    meta = engine.movie_metadata[movie_id]
    return MovieSummary(
        movieId=meta["movieId"],
        title=meta["title"],
        genres=meta["genres"],
        year=meta.get("year"),
        average_rating=meta["average_rating"],
        rating_count=meta["rating_count"],
        weighted_rating=meta["weighted_rating"],
    )
