import pytest
import pandas as pd
from backend.app.services.ranking import compute_bayesian_weighted_ratings, transform_rating_to_preference

def test_bayesian_weighted_rating_and_preference_weights():
    # Preference mapping test
    assert transform_rating_to_preference(5.0) == 2.0
    assert transform_rating_to_preference(4.0) == 1.0
    assert transform_rating_to_preference(3.0) == 0.0
    assert transform_rating_to_preference(1.0) == -2.0
    assert transform_rating_to_preference(0.5) == -2.5

    # Bayesian rating test: 1 rating of 5.0 vs 200 ratings of 4.5 with C = 3.5016
    ratings_df = pd.DataFrame([
        {"movieId": 1, "rating": 5.0}, # 1 rating 5.0
        {"movieId": 2, "rating": 4.5}, # 200 ratings 4.5
    ] + [{"movieId": 2, "rating": 4.5} for _ in range(199)])
    movies_df = pd.DataFrame([
        {"movieId": 1, "title": "Obscure 5 Star", "genres": "Drama"},
        {"movieId": 2, "title": "Popular 4.5 Star", "genres": "Action"},
    ])

    meta = compute_bayesian_weighted_ratings(ratings_df, movies_df, m=50.0, global_mean=3.5016)
    # Movie 2 should have higher weighted rating than Movie 1 because of m=50 prior shrinkage to C=3.5016
    assert meta[2]["weighted_rating"] > meta[1]["weighted_rating"]
