import sys
import time
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.utils.validation import validate_datasets
from backend.app.utils.preprocessing import generate_title_aliases
from backend.app.services.ranking import compute_bayesian_weighted_ratings, transform_rating_to_preference
from backend.app.services.content_model import ContentRecommender
from backend.app.services.collaborative_model import CollaborativeRecommender
from backend.app.services.hybrid_model import HybridRecommender

RELEVANCE_THRESHOLD = settings.RELEVANCE_THRESHOLD  # 4.0

def temporal_split_per_user(ratings_df: pd.DataFrame, train_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Per-user temporal split: sort each user's ratings by timestamp ascending.
    First 80% -> train, last 20% -> test.
    """
    train_rows = []
    test_rows = []

    for user_id, group in ratings_df.groupby("userId"):
        sorted_group = group.sort_values("timestamp")
        n_total = len(sorted_group)
        n_train = max(1, int(math.floor(n_total * train_ratio)))
        
        train_rows.append(sorted_group.iloc[:n_train])
        test_rows.append(sorted_group.iloc[n_train:])

    train_df = pd.concat(train_rows, ignore_index=True)
    test_df = pd.concat(test_rows, ignore_index=True)
    return train_df, test_df

def compute_dcg(recs: List[int], relevant_set: Set[int], k: int) -> float:
    dcg = 0.0
    for i, mid in enumerate(recs[:k]):
        if mid in relevant_set:
            dcg += 1.0 / math.log2(i + 2)
    return dcg

def compute_idcg(num_relevant: int, k: int) -> float:
    idcg = 0.0
    for i in range(min(num_relevant, k)):
        idcg += 1.0 / math.log2(i + 2)
    return idcg

def evaluate_model(
    model_name: str,
    hybrid_engine: HybridRecommender,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    all_movie_ids: List[int],
    w_c: float,
    w_cb: float,
    w_p: float,
    diversity_lambda: float = settings.DIVERSITY_LAMBDA,
    k_vals: List[int] = [5, 10],
) -> Dict[str, Any]:
    
    user_test_relevant: Dict[int, Set[int]] = {}
    for user_id, group in test_df.groupby("userId"):
        rel_mids = set(group[group["rating"] >= RELEVANCE_THRESHOLD]["movieId"])
        if rel_mids:
            user_test_relevant[user_id] = rel_mids

    user_train_seen: Dict[int, Set[int]] = {}
    user_train_seeds: Dict[int, List[Tuple[int, float]]] = {}
    for user_id, group in train_df.groupby("userId"):
        user_train_seen[user_id] = set(group["movieId"].astype(int))
        # Take recent informative items from train as seed profile (recency is primary key)
        high_rated = group[group["rating"] >= 3.0]
        seed_pool = high_rated if len(high_rated) >= 3 else group
        top_seeds = seed_pool.sort_values("timestamp", ascending=False).head(10)
        seeds = [(int(r["movieId"]), float(r["rating"])) for _, r in top_seeds.iterrows()]
        user_train_seeds[user_id] = seeds

    metrics = {f"P@{k}": [] for k in k_vals}
    metrics.update({f"R@{k}": [] for k in k_vals})
    metrics.update({f"NDCG@{k}": [] for k in k_vals})
    hit_rate_10 = []

    all_recommended_movies: Set[int] = set()

    for user_id, rel_set in user_test_relevant.items():
        seeds = user_train_seeds.get(user_id, [])
        train_seen = user_train_seen.get(user_id, set())

        if not seeds and "Most-Popular" not in model_name:
            continue

        n_req = max(k_vals) + 20

        if "Most-Popular" in model_name:
            recs_raw, _ = hybrid_engine._cold_start_recommendations(None, top_n=n_req)
        else:
            recs_raw, _, _ = hybrid_engine.generate_recommendations(
                seed_ratings=seeds,
                top_n=n_req,
                w_content=w_c,
                w_collab=w_cb,
                w_pop=w_p,
                diversity_lambda=diversity_lambda,
            )

        # Standard offline-eval: exclude all already-consumed train items
        rec_mids = [r["movieId"] for r in recs_raw if r["movieId"] not in train_seen]
        all_recommended_movies.update(rec_mids[:max(k_vals)])

        for k in k_vals:
            top_k_recs = rec_mids[:k]
            hits = len(set(top_k_recs) & rel_set)

            precision = hits / float(k)
            recall = hits / float(len(rel_set))

            dcg = compute_dcg(top_k_recs, rel_set, k)
            idcg = compute_idcg(len(rel_set), k)
            ndcg = dcg / idcg if idcg > 0 else 0.0

            metrics[f"P@{k}"].append(precision)
            metrics[f"R@{k}"].append(recall)
            metrics[f"NDCG@{k}"].append(ndcg)

        # Hit Rate @ 10
        hit = 1.0 if len(set(rec_mids[:10]) & rel_set) > 0 else 0.0
        hit_rate_10.append(hit)

    results = {
        "Model": model_name,
        "P@5": round(float(np.mean(metrics["P@5"])), 4),
        "P@10": round(float(np.mean(metrics["P@10"])), 4),
        "R@5": round(float(np.mean(metrics["R@5"])), 4),
        "R@10": round(float(np.mean(metrics["R@10"])), 4),
        "NDCG@5": round(float(np.mean(metrics["NDCG@5"])), 4),
        "NDCG@10": round(float(np.mean(metrics["NDCG@10"])), 4),
        "HitRate@10": round(float(np.mean(hit_rate_10)), 4),
        "Coverage": round((len(all_recommended_movies) / len(all_movie_ids)) * 100.0, 2),
    }

    return results

def main():
    print("=" * 70)
    print("          OFFLINE EVALUATION HARNESS (TEMPORAL 80/20 SPLIT)")
    print("=" * 70)

    movies_df = pd.read_csv(settings.MOVIES_CSV)
    ratings_df = pd.read_csv(settings.RATINGS_CSV)
    all_mids = movies_df["movieId"].tolist()

    print("Splitting ratings per-user temporally (80% train / 20% test)...")
    train_df, test_df = temporal_split_per_user(ratings_df, train_ratio=0.8)
    print(f"Train split: {len(train_df):,} ratings | Test split: {len(test_df):,} ratings")

    print("\n[ZERO DATA LEAKAGE ENFORCEMENT]")
    train_global_mean = float(train_df["rating"].mean())
    print(f"Global mean rating C (TRAIN ONLY): {train_global_mean:.4f}")

    # Compute Bayesian weighted ratings on TRAIN ONLY
    train_movie_meta = compute_bayesian_weighted_ratings(
        ratings_df=train_df,
        movies_df=movies_df,
        m=settings.POPULARITY_PRIOR_M,
        global_mean=train_global_mean,
    )

    # Fit Content model (uses movies.csv metadata, leak-free)
    content_model = ContentRecommender(top_k=settings.TOP_K_NEIGHBOURS)
    content_model.fit(movies_df)

    # Fit Collaborative model on TRAIN ONLY
    print("Fitting Collaborative model on TRAIN RATINGS ONLY...")
    collab_model = CollaborativeRecommender(
        min_common_ratings=settings.MIN_COMMON_RATINGS,
        shrinkage_lambda=settings.SHRINKAGE_LAMBDA,
        top_k=settings.TOP_K_NEIGHBOURS,
    )
    collab_model.fit(train_df, all_mids)

    hybrid_engine = HybridRecommender(
        content_model=content_model,
        collab_model=collab_model,
        movie_metadata=train_movie_meta,
    )

    models_to_eval = [
        ("B1 Most-Popular (Non-personalized)", 0.0, 0.0, 1.0, 1.0),
        ("B2 Content-only", 1.0, 0.0, 0.0, settings.DIVERSITY_LAMBDA),
        ("B3 Collaborative-only", 0.0, 1.0, 0.0, settings.DIVERSITY_LAMBDA),
        (f"B4 Hybrid (production, lambda={settings.DIVERSITY_LAMBDA})", 0.45, 0.45, 0.10, settings.DIVERSITY_LAMBDA),
        ("B4 Hybrid (diagnostic relevance, lambda=1.0)", 0.45, 0.45, 0.10, 1.0),
    ]

    eval_results = []
    print("\nRunning offline evaluation protocol across 610 users...")
    for name, wc, wcb, wp, div_lambda in models_to_eval:
        res = evaluate_model(
            model_name=name,
            hybrid_engine=hybrid_engine,
            train_df=train_df,
            test_df=test_df,
            all_movie_ids=all_mids,
            w_c=wc,
            w_cb=wcb,
            w_p=wp,
            diversity_lambda=div_lambda,
        )
        eval_results.append(res)
        print(f"Finished {name}: P@10={res['P@10']}, R@10={res['R@10']}, NDCG@10={res['NDCG@10']}, Coverage={res['Coverage']}%")

    results_df = pd.DataFrame(eval_results)

    print("\n" + "=" * 70)
    print("                 OFFLINE EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(results_df.to_string(index=False))
    print("=" * 70)

if __name__ == "__main__":
    main()
