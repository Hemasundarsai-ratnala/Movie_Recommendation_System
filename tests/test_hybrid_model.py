import pytest
import pandas as pd
from backend.app.services.content_model import ContentRecommender
from backend.app.services.collaborative_model import CollaborativeRecommender
from backend.app.services.hybrid_model import HybridRecommender

def test_hybrid_multi_movie_accumulation_and_exclusion():
    movies_df = pd.DataFrame([
        {"movieId": 1, "title": "Movie A", "genres": "Action"},
        {"movieId": 2, "title": "Movie B", "genres": "Action"},
        {"movieId": 3, "title": "Movie C", "genres": "Comedy"},
    ])
    meta = {
        1: {"movieId": 1, "title": "Movie A", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
        2: {"movieId": 2, "title": "Movie B", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
        3: {"movieId": 3, "title": "Movie C", "genres": "Comedy", "average_rating": 3.5, "rating_count": 20, "weighted_rating": 3.5},
    }
    cm = ContentRecommender(top_k=5)
    cm.fit(movies_df)

    cbm = CollaborativeRecommender(min_common_ratings=1, shrinkage_lambda=1.0, top_k=5)
    
    hybrid = HybridRecommender(cm, cbm, meta)

    # Input movie 1 should be excluded from output
    recs, mode, is_cs = hybrid.generate_recommendations([(1, 5.0)], top_n=2)
    rec_mids = [r["movieId"] for r in recs]
    assert 1 not in rec_mids

class MockModel:
    def __init__(self, mapping):
        self.mapping = mapping
    def get_neighbors(self, mid):
        return self.mapping.get(mid, ([], []))

def test_collaborative_evidence_is_not_penalized_relative_to_missing_evidence():
    """
    A candidate with strong collaborative similarity must not be outranked by an
    otherwise-equal candidate with zero collaborative similarity, when the
    collaborative weight is non-zero. Regression test for the renormalization bug.
    """
    cm = MockModel({1: ([101, 102], [0.8, 0.8])})
    cbm = MockModel({1: ([101], [0.9])})
    meta = {
        1: {"movieId": 1, "title": "Seed", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
        101: {"movieId": 101, "title": "With Collab", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
        102: {"movieId": 102, "title": "No Collab", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
    }
    hybrid = HybridRecommender(cm, cbm, meta)
    recs, _, _ = hybrid.generate_recommendations(
        [(1, 5.0)],
        top_n=2,
        w_content=0.45,
        w_collab=0.45,
        w_pop=0.10,
        diversity_lambda=1.0,
    )
    score_by_mid = {r["movieId"]: r["hybrid_score"] for r in recs}
    assert score_by_mid[101] > score_by_mid[102]
    assert recs[0]["movieId"] == 101

def test_collaborative_only_ignores_content_and_popularity():
    """
    With w_content=0, w_collab=1.0, w_pop=0, a candidate with zero collaborative
    evidence must score 0.0, not 0.5*content + 0.5*popularity.
    """
    cm = MockModel({1: ([101, 102], [0.8, 0.8])})
    cbm = MockModel({1: ([101], [0.9])})
    meta = {
        1: {"movieId": 1, "title": "Seed", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
        101: {"movieId": 101, "title": "With Collab", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
        102: {"movieId": 102, "title": "No Collab", "genres": "Action", "average_rating": 4.0, "rating_count": 50, "weighted_rating": 4.0},
    }
    hybrid = HybridRecommender(cm, cbm, meta)
    recs, _, _ = hybrid.generate_recommendations(
        [(1, 5.0)],
        top_n=2,
        w_content=0.0,
        w_collab=1.0,
        w_pop=0.0,
        diversity_lambda=1.0,
    )
    score_by_mid = {r["movieId"]: r["hybrid_score"] for r in recs}
    assert score_by_mid[102] == 0.0
    assert score_by_mid[101] > 0.0

