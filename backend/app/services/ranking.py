import numpy as np
import pandas as pd
from typing import Dict, Any
from backend.app.config import settings

def compute_bayesian_weighted_ratings(
    ratings_df: pd.DataFrame,
    movies_df: pd.DataFrame,
    m: float = settings.POPULARITY_PRIOR_M,
    global_mean: float = None,
) -> Dict[int, Dict[str, Any]]:
    """
    Computes Bayesian Weighted Rating WR for all movies from training ratings.
    WR = (v / (v + m)) * R + (m / (v + m)) * C
    Guards zero-rating movies by defaulting v=0, R=C -> WR = C.
    """
    if global_mean is None:
        C = float(ratings_df["rating"].mean())
    else:
        C = global_mean

    # Compute movie level stats
    movie_stats = ratings_df.groupby("movieId")["rating"].agg(
        v="count",
        R="mean"
    ).to_dict(orient="index")

    # Maximum rating count across corpus
    v_max = max((int(s["v"]) for s in movie_stats.values()), default=1)
    v_max = max(v_max, 1)
    log_v_max = np.log1p(v_max)

    movie_metadata: Dict[int, Dict[str, Any]] = {}

    for _, row in movies_df.iterrows():
        mid = int(row["movieId"])
        title = str(row["title"])
        genres = str(row["genres"])

        stats = movie_stats.get(mid, {"v": 0, "R": C})
        v = int(stats["v"])
        R = float(stats["R"])

        wr = (v / (v + m)) * R + (m / (v + m)) * C
        support_factor = np.log1p(v) / log_v_max if log_v_max > 0 else 1.0
        pop_ranking = float(wr) * support_factor

        movie_metadata[mid] = {
            "movieId": mid,
            "title": title,
            "genres": genres,
            "average_rating": round(R, 3),
            "rating_count": v,
            "weighted_rating": round(float(wr), 4),
            "popularity_score_for_ranking": round(float(pop_ranking), 4),
        }

    return movie_metadata

def transform_rating_to_preference(rating: float, neutral_baseline: float = settings.NEUTRAL_BASELINE) -> float:
    """
    Maps rating to centered preference weight: w = rating - neutral_baseline.
    5.0 -> +2.0, 4.0 -> +1.0, 3.0 -> 0.0, 2.0 -> -1.0, 1.0 -> -2.0, 0.5 -> -2.5.
    """
    return rating - neutral_baseline
