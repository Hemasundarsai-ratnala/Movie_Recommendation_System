import pytest
from backend.app.config import settings
from backend.app.utils.validation import validate_datasets

def test_dataset_facts_part_a():
    report = validate_datasets(settings.MOVIES_CSV, settings.RATINGS_CSV)
    assert report["movies_count"] == 9742
    assert report["ratings_count"] == 100836
    assert report["movies_nulls"] == 0
    assert report["ratings_nulls"] == 0
    assert report["duplicate_movie_ids"] == 0
    assert report["duplicate_user_movie_pairs"] == 0
    assert report["orphan_movie_ids"] == 0
    assert report["invalid_ratings"] == 0
    assert report["unique_users"] == 610
    assert report["unique_rated_movies"] == 9724
    assert abs(report["global_mean_rating"] - 3.5016) < 0.001
    assert len(report["edge_case_1_duplicate_title_pairs"]) == 5
    assert report["edge_case_2_zero_rating_movies_count"] == 18
    assert report["edge_case_3_no_genres_count"] == 34
    assert report["edge_case_4_titles_no_year_count"] == 13
