from fastapi import APIRouter, HTTPException
from backend.app.schemas import InsightsResponse, MovieSummary, GenreCount
from backend.app.services.recommender import engine

router = APIRouter(prefix="/insights", tags=["Insights"])

@router.get("", response_model=InsightsResponse)
def get_insights():
    """Returns dataset insights, statistics, and top movies from precomputed metadata."""
    if not engine.is_loaded:
        raise HTTPException(status_code=503, detail="Model artifacts not loaded.")

    stats = engine.global_stats
    all_movies = list(engine.movie_metadata.values())

    top_weighted = sorted(all_movies, key=lambda x: x["weighted_rating"], reverse=True)[:10]
    most_rated = sorted(all_movies, key=lambda x: x["rating_count"], reverse=True)[:10]

    genre_counts = [
        GenreCount(genre=g, count=c)
        for g, c in sorted(stats.get("genre_counts", {}).items(), key=lambda x: x[1], reverse=True)
    ]

    return InsightsResponse(
        total_movies=stats.get("total_movies", len(all_movies)),
        total_ratings=stats.get("total_ratings", 0),
        global_mean_rating=stats.get("global_mean_rating", 3.5016),
        unique_users=stats.get("unique_users", 610),
        unique_rated_movies=stats.get("unique_rated_movies", 9724),
        sparsity_percentage=stats.get("sparsity_percentage", 98.3),
        genre_distribution=genre_counts,
        top_weighted_movies=[
            MovieSummary(
                movieId=m["movieId"],
                title=m["title"],
                genres=m["genres"],
                year=m.get("year"),
                average_rating=m["average_rating"],
                rating_count=m["rating_count"],
                weighted_rating=m["weighted_rating"],
            )
            for m in top_weighted
        ],
        most_rated_movies=[
            MovieSummary(
                movieId=m["movieId"],
                title=m["title"],
                genres=m["genres"],
                year=m.get("year"),
                average_rating=m["average_rating"],
                rating_count=m["rating_count"],
                weighted_rating=m["weighted_rating"],
            )
            for m in most_rated
        ],
        rating_distribution=stats.get("rating_distribution", {}),
    )
