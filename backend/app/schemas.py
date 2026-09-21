from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator

class MovieSummary(BaseModel):
    movieId: int
    title: str
    genres: str
    year: Optional[int] = None
    average_rating: float = 0.0
    rating_count: int = 0
    weighted_rating: float = 0.0

class SearchAlternative(BaseModel):
    movieId: int
    title: str
    score: float

class MatchedMovie(BaseModel):
    query: str
    movieId: Optional[int] = None
    title: Optional[str] = None
    confidence_score: float = 0.0
    match_status: str = "no_match"  # "auto_accept", "did_you_mean", "no_match"
    alternatives: List[SearchAlternative] = []

class SeedMovieInput(BaseModel):
    query_or_id: str = Field(..., description="Movie title search string or integer movieId as string")
    rating: float = Field(..., ge=0.5, le=5.0, description="User rating from 0.5 to 5.0 in 0.5 steps")

    @field_validator("rating")

    def validate_rating_step(cls, v: float) -> float:
        if round(v * 2) / 2 != v:
            raise ValueError("Rating must be in 0.5 increments (e.g., 0.5, 1.0, 1.5, ..., 5.0)")
        return v

class SingleRecommendRequest(BaseModel):
    query_or_id: str = Field(..., min_length=1, description="Movie title or movieId")
    rating: float = Field(default=5.0, ge=0.5, le=5.0)
    top_n: int = Field(default=10, ge=1, le=50)
    content_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    collaborative_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    popularity_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    diversity_lambda: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)

class HybridRecommendRequest(BaseModel):
    seeds: List[SeedMovieInput] = Field(..., min_length=1, max_length=20)
    top_n: int = Field(default=10, ge=1, le=50)
    content_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    collaborative_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    popularity_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    diversity_lambda: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)

class PersonalizedRecommendRequest(BaseModel):
    seeds: List[SeedMovieInput] = Field(default=[])
    stated_genres: List[str] = Field(default=[])
    top_n: int = Field(default=10, ge=1, le=50)
    content_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    collaborative_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    popularity_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    diversity_lambda: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)

class RecommendationItem(BaseModel):
    movieId: int
    title: str
    genres: str
    year: Optional[int] = None
    average_rating: float
    rating_count: int
    weighted_rating: float
    content_score: float = 0.0
    collaborative_score: float = 0.0
    popularity_score: float = 0.0
    hybrid_score: float = 0.0
    explanation: str = ""

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    matched_movies: List[MatchedMovie]
    mode: str  # "cold_start_popularity", "cold_start_genre", "single_seed_hybrid", "multi_seed_hybrid"
    cold_start: bool = False
    total_returned: int

class GenreCount(BaseModel):
    genre: str
    count: int

class InsightsResponse(BaseModel):
    total_movies: int
    total_ratings: int
    global_mean_rating: float
    unique_users: int
    unique_rated_movies: int
    sparsity_percentage: float
    genre_distribution: List[GenreCount]
    top_weighted_movies: List[MovieSummary]
    most_rated_movies: List[MovieSummary]
    rating_distribution: Dict[str, int]

class HealthResponse(BaseModel):
    status: str
    version: str
    model_artifacts_loaded: bool
    manifest: Optional[dict] = None
