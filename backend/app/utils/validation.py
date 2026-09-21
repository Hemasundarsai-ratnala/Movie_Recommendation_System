import pandas as pd
import re
from typing import Dict, Any, List
from pathlib import Path

def validate_datasets(movies_path: Path, ratings_path: Path) -> Dict[str, Any]:
    """
    Validates movies.csv and ratings.csv against expected structural constraints
    and reports on genuine dataset edge cases.
    """
    if not movies_path.exists():
        raise FileNotFoundError(f"Movies CSV not found at {movies_path}")
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings CSV not found at {ratings_path}")

    movies_df = pd.read_csv(movies_path)
    ratings_df = pd.read_csv(ratings_path)

    # Required columns
    movies_req_cols = {"movieId", "title", "genres"}
    ratings_req_cols = {"userId", "movieId", "rating", "timestamp"}

    if not movies_req_cols.issubset(movies_df.columns):
        raise ValueError(f"movies.csv missing columns: {movies_req_cols - set(movies_df.columns)}")
    if not ratings_req_cols.issubset(ratings_df.columns):
        raise ValueError(f"ratings.csv missing columns: {ratings_req_cols - set(ratings_df.columns)}")

    # Null checks
    movies_nulls = int(movies_df.isnull().sum().sum())
    ratings_nulls = int(ratings_df.isnull().sum().sum())

    # Duplicate checks
    dup_movie_ids = int(movies_df.duplicated(subset=["movieId"]).sum())
    dup_user_movie_pairs = int(ratings_df.duplicated(subset=["userId", "movieId"]).sum())

    # Orphan check
    movie_id_set = set(movies_df["movieId"])
    rating_movie_ids = set(ratings_df["movieId"])
    orphan_movie_ids = len(rating_movie_ids - movie_id_set)

    # Rating domain check
    valid_ratings = {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0}
    invalid_ratings = int((~ratings_df["rating"].isin(valid_ratings)).sum())

    # Genuine Edge Case 1: Duplicate titles mapping to different movieIds
    title_counts = movies_df["title"].value_counts()
    dup_titles = title_counts[title_counts > 1].index.tolist()
    dup_title_pairs: List[Dict[str, Any]] = []
    for dt in dup_titles:
        mids = movies_df[movies_df["title"] == dt]["movieId"].tolist()
        genres = movies_df[movies_df["title"] == dt]["genres"].tolist()
        dup_title_pairs.append({"title": dt, "movieIds": mids, "genres": genres})

    # Genuine Edge Case 2: Movies with zero ratings
    unrated_movie_ids = movie_id_set - rating_movie_ids
    zero_rating_count = len(unrated_movie_ids)

    # Genuine Edge Case 3: Movies tagged (no genres listed)
    no_genres_count = int((movies_df["genres"] == "(no genres listed)").sum())

    # Genuine Edge Case 4: Titles without trailing year (YYYY)
    year_regex = re.compile(r"\(\d{4}\)$")
    titles_no_year = [
        t for t in movies_df["title"]
        if not year_regex.search(t.strip())
    ]
    no_year_count = len(titles_no_year)

    report = {
        "movies_count": len(movies_df),
        "ratings_count": len(ratings_df),
        "movies_nulls": movies_nulls,
        "ratings_nulls": ratings_nulls,
        "duplicate_movie_ids": dup_movie_ids,
        "duplicate_user_movie_pairs": dup_user_movie_pairs,
        "orphan_movie_ids": orphan_movie_ids,
        "invalid_ratings": invalid_ratings,
        "unique_users": int(ratings_df["userId"].nunique()),
        "unique_rated_movies": int(ratings_df["movieId"].nunique()),
        "global_mean_rating": float(ratings_df["rating"].mean()),
        "edge_case_1_duplicate_title_pairs": dup_title_pairs,
        "edge_case_2_zero_rating_movies_count": zero_rating_count,
        "edge_case_3_no_genres_count": no_genres_count,
        "edge_case_4_titles_no_year_count": no_year_count,
        "edge_case_4_titles_no_year_sample": titles_no_year[:15],
    }

    return report

def format_validation_report(report: Dict[str, Any]) -> str:
    lines = [
        "=" * 60,
        "         DATASET VALIDATION & INTEGRITY REPORT",
        "=" * 60,
        f"movies.csv rows       : {report['movies_count']:,}",
        f"ratings.csv rows      : {report['ratings_count']:,}",
        f"Null values (movies)  : {report['movies_nulls']}",
        f"Null values (ratings) : {report['ratings_nulls']}",
        f"Duplicate movieIds    : {report['duplicate_movie_ids']}",
        f"Duplicate (u, m) pairs: {report['duplicate_user_movie_pairs']}",
        f"Orphan movieIds       : {report['orphan_movie_ids']}",
        f"Invalid ratings       : {report['invalid_ratings']}",
        f"Unique Users          : {report['unique_users']}",
        f"Unique Rated Movies   : {report['unique_rated_movies']}",
        f"Global Mean Rating    : {report['global_mean_rating']:.4f}",
        "-" * 60,
        "GENUINE EDGE CASES REPORTED:",
        f"1. Duplicate Titles   : {len(report['edge_case_1_duplicate_title_pairs'])} pairs",
    ]
    for dt in report['edge_case_1_duplicate_title_pairs']:
        lines.append(f"   - '{dt['title']}': movieIds {dt['movieIds']} | genres: {dt['genres']}")
    lines.extend([
        f"2. Zero-Rating Movies : {report['edge_case_2_zero_rating_movies_count']} movies",
        f"3. No Genres Listed   : {report['edge_case_3_no_genres_count']} movies",
        f"4. Titles without Year: {report['edge_case_4_titles_no_year_count']} movies",
        "   Sample: " + ", ".join(report['edge_case_4_titles_no_year_sample'][:5]),
        "=" * 60,
    ])
    return "\n".join(lines)
