import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from backend.app.config import settings
from backend.app.services.content_model import ContentRecommender
from backend.app.services.collaborative_model import CollaborativeRecommender
from backend.app.services.ranking import transform_rating_to_preference

def min_max_scale(scores_dict: Dict[int, float], candidate_ids: List[int]) -> Dict[int, float]:
    """Applies min-max normalization over candidate pool for a score channel."""
    vals = [scores_dict.get(mid, 0.0) for mid in candidate_ids]
    if not vals:
        return {}
    min_v = float(np.min(vals))
    max_v = float(np.max(vals))

    if max_v - min_v < 1e-6:
        return {mid: 0.0 for mid in candidate_ids}

    scaled = {}
    for mid in candidate_ids:
        raw_val = scores_dict.get(mid, 0.0)
        scaled[mid] = (raw_val - min_v) / (max_v - min_v)
    return scaled

class HybridRecommender:
    def __init__(
        self,
        content_model: ContentRecommender,
        collab_model: CollaborativeRecommender,
        movie_metadata: Dict[int, Dict[str, Any]],
    ):
        self.content_model = content_model
        self.collab_model = collab_model
        self.movie_metadata = movie_metadata

    def generate_recommendations(
        self,
        seed_ratings: List[Tuple[int, float]],
        stated_genres: Optional[List[str]] = None,
        top_n: int = 10,
        w_content: Optional[float] = None,
        w_collab: Optional[float] = None,
        w_pop: Optional[float] = None,
        diversity_lambda: Optional[float] = settings.DIVERSITY_LAMBDA,
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """
        Generates hybrid recommendations with score channel normalization,
        weight renormalization for missing collaborative signal, and MMR re-ranking.
        Returns (recommendations_list, mode_string, is_cold_start).
        """
        if w_content is None:
            w_content = settings.CONTENT_WEIGHT
        if w_collab is None:
            w_collab = settings.COLLABORATIVE_WEIGHT
        if w_pop is None:
            w_pop = settings.POPULARITY_WEIGHT
        if diversity_lambda is None:
            diversity_lambda = settings.DIVERSITY_LAMBDA

        # Normalize weights to sum to 1.0
        total_w = w_content + w_collab + w_pop
        if total_w > 0:
            w_content /= total_w
            w_collab /= total_w
            w_pop /= total_w

        seed_mids = {mid for mid, _ in seed_ratings if mid in self.movie_metadata}

        # -------------------------------------------------------------
        # COLD START HANDLER
        # -------------------------------------------------------------
        if not seed_ratings or len(seed_mids) == 0:
            recs, mode = self._cold_start_recommendations(stated_genres, top_n)
            return recs, mode, True

        # Mode determination
        if len(seed_mids) == 1:
            mode = "single_seed_hybrid"
        else:
            mode = "multi_seed_hybrid"

        # -------------------------------------------------------------
        # MULTI-MOVIE AGGREGATION
        # Accumulate scores into dicts keyed by movieId (NEVER append series)
        # -------------------------------------------------------------
        content_scores_raw: Dict[int, float] = {}
        collab_scores_raw: Dict[int, float] = {}

        top_content_contributor: Dict[int, Tuple[int, float]] = {}  # mid -> (seed_mid, score)
        top_collab_contributor: Dict[int, Tuple[int, float]] = {}

        for seed_mid, user_rating in seed_ratings:
            if seed_mid not in self.movie_metadata:
                continue

            pref_weight = transform_rating_to_preference(user_rating)

            # 1. Content channel neighbours
            c_mids, c_sims = self.content_model.get_neighbors(seed_mid)
            for n_mid, sim in zip(c_mids, c_sims):
                if n_mid in seed_mids:
                    continue
                contrib = pref_weight * float(sim)
                content_scores_raw[n_mid] = content_scores_raw.get(n_mid, 0.0) + contrib

                if contrib > 0 and (n_mid not in top_content_contributor or contrib > top_content_contributor[n_mid][1]):
                    top_content_contributor[n_mid] = (seed_mid, contrib)

            # 2. Collaborative channel neighbours
            cb_mids, cb_sims = self.collab_model.get_neighbors(seed_mid)
            for n_mid, sim in zip(cb_mids, cb_sims):
                if n_mid in seed_mids:
                    continue
                contrib = pref_weight * float(sim)
                collab_scores_raw[n_mid] = collab_scores_raw.get(n_mid, 0.0) + contrib

                if contrib > 0 and (n_mid not in top_collab_contributor or contrib > top_collab_contributor[n_mid][1]):
                    top_collab_contributor[n_mid] = (seed_mid, contrib)

        # Candidate pool: union of all non-seed candidates touched by content/collab or top popular
        candidate_set = (set(content_scores_raw.keys()) | set(collab_scores_raw.keys())) - seed_mids

        if not candidate_set:
            # Fallback to popularity if no candidates generated
            recs, mode = self._cold_start_recommendations(stated_genres, top_n)
            return recs, mode, True

        candidate_ids = list(candidate_set)

        # -------------------------------------------------------------
        # SCORE CHANNEL NORMALIZATION
        # -------------------------------------------------------------
        c_norm = min_max_scale(content_scores_raw, candidate_ids)
        cb_norm = min_max_scale(collab_scores_raw, candidate_ids)

        # Popularity score (Bayesian WR scaled by support factor for ranking)
        pop_raw = {
            mid: self.movie_metadata[mid].get("popularity_score_for_ranking", self.movie_metadata[mid]["weighted_rating"])
            for mid in candidate_ids
            if mid in self.movie_metadata
        }
        pop_norm = min_max_scale(pop_raw, candidate_ids)

        # -------------------------------------------------------------
        # HYBRID FUSION (UNMODIFIED WEIGHTS)
        # -------------------------------------------------------------
        hybrid_scores: Dict[int, float] = {}

        for mid in candidate_ids:
            cn = c_norm.get(mid, 0.0)
            cbn = cb_norm.get(mid, 0.0)
            pn = pop_norm.get(mid, 0.0)

            h_score = w_content * cn + w_collab * cbn + w_pop * pn
            hybrid_scores[mid] = float(h_score)

        # Sort candidate pool by initial hybrid score
        ranked_candidates = sorted(candidate_ids, key=lambda mid: hybrid_scores[mid], reverse=True)

        # -------------------------------------------------------------
        # MMR DIVERSITY RE-RANKING
        # -------------------------------------------------------------
        final_selected_mids = self._mmr_rerank(
            ranked_candidates[: min(200, len(ranked_candidates))],
            hybrid_scores,
            diversity_lambda,
            top_n,
        )

        # Build recommendation result objects
        recommendations = []
        for mid in final_selected_mids:
            meta = self.movie_metadata[mid]
            cn = round(c_norm.get(mid, 0.0), 3)
            cbn = round(cb_norm.get(mid, 0.0), 3)
            pn = round(pop_norm.get(mid, 0.0), 3)
            hs = round(hybrid_scores.get(mid, 0.0), 3)

            top_seed_mid = None
            if mid in top_collab_contributor and top_collab_contributor[mid][1] > 0:
                top_seed_mid = top_collab_contributor[mid][0]
            elif mid in top_content_contributor:
                top_seed_mid = top_content_contributor[mid][0]

            seed_title = self.movie_metadata[top_seed_mid]["title"] if top_seed_mid and top_seed_mid in self.movie_metadata else None

            recommendations.append({
                "movieId": mid,
                "title": meta["title"],
                "genres": meta["genres"],
                "year": meta.get("year"),
                "average_rating": meta["average_rating"],
                "rating_count": meta["rating_count"],
                "weighted_rating": meta["weighted_rating"],
                "content_score": cn,
                "collaborative_score": cbn,
                "popularity_score": pn,
                "hybrid_score": hs,
                "top_contributing_seed_title": seed_title,
            })

        return recommendations, mode, False

    def _mmr_rerank(
        self,
        candidate_pool: List[int],
        hybrid_scores: Dict[int, float],
        lambda_param: float,
        top_n: int,
    ) -> List[int]:
        """Applies Maximal Marginal Relevance (MMR) re-ranking."""
        if not candidate_pool:
            return []
        if lambda_param >= 0.99 or len(candidate_pool) <= top_n:
            return candidate_pool[:top_n]

        # Precompute neighbor similarity dictionaries once for candidate pool
        # to ensure symmetric similarity: sim(u, v) = max(sim_u.get(v, 0), sim_v.get(u, 0))
        sim_lookup: Dict[int, Dict[int, float]] = {}
        for mid in candidate_pool:
            c_mids, c_sims = self.content_model.get_neighbors(mid)
            sim_lookup[mid] = {int(m): float(s) for m, s in zip(c_mids, c_sims)}

        def get_symmetric_similarity(m1: int, m2: int) -> float:
            s1 = sim_lookup.get(m1, {}).get(m2, 0.0)
            if s1 > 0:
                return s1
            return sim_lookup.get(m2, {}).get(m1, 0.0)

        first_mid = candidate_pool[0]
        selected: List[int] = [first_mid]
        unselected = set(candidate_pool[1:])

        # Incrementally track max content similarity to any selected item
        max_sim: Dict[int, float] = {
            mid: get_symmetric_similarity(mid, first_mid) for mid in unselected
        }

        while len(selected) < top_n and unselected:
            best_mid = None
            best_mmr_score = -1e9

            for mid in unselected:
                mmr = lambda_param * hybrid_scores[mid] - (1.0 - lambda_param) * max_sim[mid]
                if mmr > best_mmr_score:
                    best_mmr_score = mmr
                    best_mid = mid

            if best_mid is None:
                break

            selected.append(best_mid)
            unselected.remove(best_mid)

            # Update max similarity to selected set for remaining candidates
            for mid in unselected:
                sim_to_new = get_symmetric_similarity(mid, best_mid)
                if sim_to_new > max_sim[mid]:
                    max_sim[mid] = sim_to_new

        return selected

    def _cold_start_recommendations(
        self, stated_genres: Optional[List[str]], top_n: int
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Cold start fallback using Bayesian Weighted Rating popularity."""
        sorted_movies = sorted(
            self.movie_metadata.values(),
            key=lambda x: x.get("popularity_score_for_ranking", x["weighted_rating"]),
            reverse=True,
        )

        if stated_genres:
            genres_lower = {g.lower() for g in stated_genres}
            filtered = [
                m for m in sorted_movies
                if any(g.strip().lower() in genres_lower for g in m["genres"].split("|"))
            ]
            if filtered:
                sorted_movies = filtered
                mode = "cold_start_genre"
            else:
                mode = "cold_start_popularity"
        else:
            mode = "cold_start_popularity"

        recs = []
        for meta in sorted_movies[:top_n]:
            recs.append({
                "movieId": meta["movieId"],
                "title": meta["title"],
                "genres": meta["genres"],
                "year": meta.get("year"),
                "average_rating": meta["average_rating"],
                "rating_count": meta["rating_count"],
                "weighted_rating": meta["weighted_rating"],
                "content_score": 0.0,
                "collaborative_score": 0.0,
                "popularity_score": 1.0,
                "hybrid_score": round(meta["weighted_rating"] / 5.0, 3),
                "top_contributing_seed_title": None,
            })

        return recs, mode
