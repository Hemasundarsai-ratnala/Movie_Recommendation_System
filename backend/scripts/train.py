import os
import sys
import time
import json
import hashlib
import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.utils.validation import validate_datasets
from backend.app.utils.preprocessing import generate_title_aliases
from backend.app.services.ranking import compute_bayesian_weighted_ratings
from backend.app.services.content_model import ContentRecommender
from backend.app.services.collaborative_model import CollaborativeRecommender

def file_md5(path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main():
    start_time = time.time()
    print("=" * 60)
    print("      HYBRID RECOMMENDER - OFFLINE MODEL TRAINING")
    print("=" * 60)

    # 1. Validation check
    print(f"Loading datasets from {settings.DATA_DIR}...")
    val_report = validate_datasets(settings.MOVIES_CSV, settings.RATINGS_CSV)
    print(f"Loaded {val_report['movies_count']:,} movies, {val_report['ratings_count']:,} ratings.")

    movies_df = pd.read_csv(settings.MOVIES_CSV)
    ratings_df = pd.read_csv(settings.RATINGS_CSV)

    # 2. Generate searchable title aliases
    print("Generating normalized searchable title aliases...")
    title_aliases = {}
    parsed_years = {}
    clean_titles = {}

    for _, row in movies_df.iterrows():
        mid = int(row["movieId"])
        raw_t = str(row["title"])
        y, ct, aliases = generate_title_aliases(raw_t)
        title_aliases[mid] = aliases
        parsed_years[mid] = y
        clean_titles[mid] = ct

    # 3. Compute Bayesian weighted rating WR and metadata
    print("Computing Bayesian weighted ratings (POPULARITY_PRIOR_M = 50)...")
    movie_meta = compute_bayesian_weighted_ratings(
        ratings_df=ratings_df,
        movies_df=movies_df,
        m=settings.POPULARITY_PRIOR_M,
        global_mean=val_report["global_mean_rating"],
    )

    for mid, meta in movie_meta.items():
        meta["year"] = parsed_years.get(mid)

    # 4. Train Content-Based Model (TF-IDF + block-wise top-k)
    print("Fitting Content-Based Model (TF-IDF + Top-200 Sparse Cosine)...")
    content_model = ContentRecommender(top_k=settings.TOP_K_NEIGHBOURS)
    content_model.fit(movies_df)

    # 5. Train Collaborative Model (Centered Cosine + Shrinkage + Top-200)
    print("Fitting Collaborative Model (Centered Cosine + Shrinkage Lambda=25)...")
    collab_model = CollaborativeRecommender(
        min_common_ratings=settings.MIN_COMMON_RATINGS,
        shrinkage_lambda=settings.SHRINKAGE_LAMBDA,
        top_k=settings.TOP_K_NEIGHBOURS,
    )
    collab_model.fit(ratings_df, movies_df["movieId"].tolist())

    # 6. Global statistics
    print("Computing dataset insights & statistics...")
    genre_counts: dict[str, int] = {}
    for g_str in movies_df["genres"]:
        for g in g_str.split("|"):
            g = g.strip()
            genre_counts[g] = genre_counts.get(g, 0) + 1

    rating_dist = ratings_df["rating"].value_counts().sort_index().to_dict()
    rating_dist_str = {str(k): int(v) for k, v in rating_dist.items()}

    total_cells = val_report["unique_users"] * val_report["unique_rated_movies"]
    sparsity_pct = (1.0 - (val_report["ratings_count"] / total_cells)) * 100.0

    global_stats = {
        "total_movies": val_report["movies_count"],
        "total_ratings": val_report["ratings_count"],
        "global_mean_rating": val_report["global_mean_rating"],
        "unique_users": val_report["unique_users"],
        "unique_rated_movies": val_report["unique_rated_movies"],
        "sparsity_percentage": round(sparsity_pct, 2),
        "genre_counts": genre_counts,
        "rating_distribution": rating_dist_str,
    }

    # 7. Serialize Artifacts
    settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Serializing artifacts to {settings.MODEL_DIR}...")

    joblib.dump(movie_meta, settings.MODEL_DIR / "movie_metadata.joblib", compress=3)
    joblib.dump(title_aliases, settings.MODEL_DIR / "title_alias_index.joblib", compress=3)
    joblib.dump(content_model, settings.MODEL_DIR / "content_topk.joblib", compress=3)
    joblib.dump(collab_model, settings.MODEL_DIR / "collaborative_topk.joblib", compress=3)
    joblib.dump(global_stats, settings.MODEL_DIR / "global_stats.joblib", compress=3)

    manifest = {
        "build_timestamp": datetime.utcnow().isoformat() + "Z",
        "movies_csv_md5": file_md5(settings.MOVIES_CSV),
        "ratings_csv_md5": file_md5(settings.RATINGS_CSV),
        "movies_count": val_report["movies_count"],
        "ratings_count": val_report["ratings_count"],
        "config": {
            "MIN_COMMON_RATINGS": settings.MIN_COMMON_RATINGS,
            "SHRINKAGE_LAMBDA": settings.SHRINKAGE_LAMBDA,
            "TOP_K_NEIGHBOURS": settings.TOP_K_NEIGHBOURS,
            "POPULARITY_PRIOR_M": settings.POPULARITY_PRIOR_M,
            "NEUTRAL_BASELINE": settings.NEUTRAL_BASELINE,
        },
        "training_time_seconds": round(time.time() - start_time, 2),
    }

    with open(settings.MODEL_DIR / "training_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"SUCCESS: Training pipeline completed in {elapsed:.2f} seconds.")
    print(f"Artifacts successfully written to: {settings.MODEL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
