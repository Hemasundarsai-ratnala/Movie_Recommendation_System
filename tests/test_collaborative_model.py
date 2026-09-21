import pytest
import pandas as pd
from backend.app.services.collaborative_model import CollaborativeRecommender

def test_collaborative_model_shrinkage_and_floor():
    ratings = []
    # 25 users rate movie 10 and 20 highly (5.0, 5.0) and movie 99 low (1.0)
    for u in range(1, 26):
        ratings.append({"userId": u, "movieId": 10, "rating": 5.0})
        ratings.append({"userId": u, "movieId": 20, "rating": 5.0})
        ratings.append({"userId": u, "movieId": 99, "rating": 1.0})

    # Users 1 to 5 also rate movie 30 (only 5 co-raters -> below 20 floor)
    for u in range(1, 6):
        ratings.append({"userId": u, "movieId": 30, "rating": 5.0})

    ratings_df = pd.DataFrame(ratings)
    model = CollaborativeRecommender(min_common_ratings=20, shrinkage_lambda=25.0, top_k=5)
    model.fit(ratings_df, [10, 20, 30, 99])

    # Movie 10 & 20 clear 20 co-raters floor and have positive correlation
    mids_10, sims_10 = model.get_neighbors(10)
    assert 20 in mids_10
    # Movie 30 should not be recommended due to floor < 20 co-raters
    assert 30 not in mids_10
