import joblib
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from backend.app.config import settings
from backend.app.schemas import (
    SingleRecommendRequest,
    HybridRecommendRequest,
    PersonalizedRecommendRequest,
    RecommendationResponse,
    RecommendationItem,
    MatchedMovie,
)
from backend.app.services.fuzzy_matcher import FuzzyTitleMatcher
from backend.app.services.content_model import ContentRecommender
from backend.app.services.collaborative_model import CollaborativeRecommender
from backend.app.services.hybrid_model import HybridRecommender
from backend.app.services.explain import generate_explanation

logger = logging.getLogger("recommender")

class RecommendationEngine:
    def __init__(self, model_dir: Path = settings.MODEL_DIR):
        self.model_dir = model_dir
        self.is_loaded = False
        self.manifest: Optional[dict] = None

        self.fuzzy_matcher = FuzzyTitleMatcher()
        self.content_model: Optional[ContentRecommender] = None
        self.collab_model: Optional[CollaborativeRecommender] = None
        self.hybrid_model: Optional[HybridRecommender] = None

        self.movie_metadata: Dict[int, Dict[str, Any]] = {}
        self.global_stats: Dict[str, Any] = {}

    def load_artifacts(self) -> bool:
        """Loads serialized model artifacts from model_dir."""
        manifest_path = self.model_dir / "training_manifest.json"
        if not manifest_path.exists():
            logger.warning(f"Training manifest not found at {manifest_path}. Please run train.py.")
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                self.manifest = json.load(f)

            self.movie_metadata = joblib.load(self.model_dir / "movie_metadata.joblib")
            title_aliases = joblib.load(self.model_dir / "title_alias_index.joblib")
            self.content_model = joblib.load(self.model_dir / "content_topk.joblib")
            self.collab_model = joblib.load(self.model_dir / "collaborative_topk.joblib")

            if (self.model_dir / "global_stats.joblib").exists():
                self.global_stats = joblib.load(self.model_dir / "global_stats.joblib")

            # Build fuzzy index
            self.fuzzy_matcher.build_index(self.movie_metadata, title_aliases)

            # Build hybrid wrapper
            self.hybrid_model = HybridRecommender(
                content_model=self.content_model,
                collab_model=self.collab_model,
                movie_metadata=self.movie_metadata,
            )

            self.is_loaded = True
            logger.info(f"Engine successfully loaded artifacts built at {self.manifest.get('build_timestamp')}")
            return True

        except Exception as e:
            logger.error(f"Failed to load artifacts from {self.model_dir}: {e}", exc_info=True)
            self.is_loaded = False
            return False

    def recommend_single(self, request: SingleRecommendRequest) -> RecommendationResponse:
        """Single movie seed recommendation."""
        matched = self.fuzzy_matcher.match_query(request.query_or_id)
        matched_list = [matched]

        if matched.match_status == "no_match" or matched.movieId is None:
            # Fallback to cold start popularity
            recs_raw, mode, is_cs = self.hybrid_model._cold_start_recommendations(None, request.top_n)
            return self._build_response(recs_raw, matched_list, mode, is_cs)

        seed_ratings = [(matched.movieId, request.rating)]

        recs_raw, mode, is_cs = self.hybrid_model.generate_recommendations(
            seed_ratings=seed_ratings,
            top_n=request.top_n,
            w_content=request.content_weight,
            w_collab=request.collaborative_weight,
            w_pop=request.popularity_weight,
            diversity_lambda=request.diversity_lambda,
        )

        return self._build_response(recs_raw, matched_list, mode, is_cs)

    def recommend_hybrid(self, request: HybridRecommendRequest) -> RecommendationResponse:
        """Multi-movie hybrid seed recommendation."""
        matched_list = []
        seed_ratings = []

        for seed in request.seeds:
            matched = self.fuzzy_matcher.match_query(seed.query_or_id)
            matched_list.append(matched)
            if matched.match_status != "no_match" and matched.movieId is not None:
                seed_ratings.append((matched.movieId, seed.rating))

        recs_raw, mode, is_cs = self.hybrid_model.generate_recommendations(
            seed_ratings=seed_ratings,
            top_n=request.top_n,
            w_content=request.content_weight,
            w_collab=request.collaborative_weight,
            w_pop=request.popularity_weight,
            diversity_lambda=request.diversity_lambda,
        )

        return self._build_response(recs_raw, matched_list, mode, is_cs)

    def recommend_personalized(self, request: PersonalizedRecommendRequest) -> RecommendationResponse:
        """Personalized recommendation with seeds and stated genre preferences."""
        matched_list = []
        seed_ratings = []

        for seed in request.seeds:
            matched = self.fuzzy_matcher.match_query(seed.query_or_id)
            matched_list.append(matched)
            if matched.match_status != "no_match" and matched.movieId is not None:
                seed_ratings.append((matched.movieId, seed.rating))

        recs_raw, mode, is_cs = self.hybrid_model.generate_recommendations(
            seed_ratings=seed_ratings,
            stated_genres=request.stated_genres,
            top_n=request.top_n,
            w_content=request.content_weight,
            w_collab=request.collaborative_weight,
            w_pop=request.popularity_weight,
            diversity_lambda=request.diversity_lambda,
        )

        return self._build_response(recs_raw, matched_list, mode, is_cs)

    def _build_response(
        self,
        recs_raw: List[Dict[str, Any]],
        matched_list: List[MatchedMovie],
        mode: str,
        is_cold_start: bool,
    ) -> RecommendationResponse:
        items = []
        for r in recs_raw:
            exp = generate_explanation(r, is_cold_start=is_cold_start)
            items.append(RecommendationItem(
                movieId=r["movieId"],
                title=r["title"],
                genres=r["genres"],
                year=r.get("year"),
                average_rating=r["average_rating"],
                rating_count=r["rating_count"],
                weighted_rating=r["weighted_rating"],
                content_score=r["content_score"],
                collaborative_score=r["collaborative_score"],
                popularity_score=r["popularity_score"],
                hybrid_score=r["hybrid_score"],
                explanation=exp,
            ))

        return RecommendationResponse(
            recommendations=items,
            matched_movies=matched_list,
            mode=mode,
            cold_start=is_cold_start,
            total_returned=len(items),
        )

engine = RecommendationEngine()
