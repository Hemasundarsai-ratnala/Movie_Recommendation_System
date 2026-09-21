import pytest
from backend.app.services.fuzzy_matcher import FuzzyTitleMatcher
from backend.app.utils.preprocessing import generate_title_aliases

@pytest.fixture
def sample_fuzzy_matcher():
    matcher = FuzzyTitleMatcher()
    movies_meta = {
        838: {"title": "Emma (1996)", "genres": "Comedy|Drama|Romance", "year": 1996, "average_rating": 3.8, "rating_count": 30, "weighted_rating": 3.7},
        26958: {"title": "Emma (1996)", "genres": "Romance", "year": 1996, "average_rating": 3.0, "rating_count": 2, "weighted_rating": 3.5},
        155: {"title": "Dark Knight, The (2008)", "genres": "Action|Crime|Drama", "year": 2008, "average_rating": 4.2, "rating_count": 200, "weighted_rating": 4.1},
        47: {"title": "Seven (a.k.a. Se7en) (1995)", "genres": "Mystery|Thriller", "year": 1995, "average_rating": 4.2, "rating_count": 200, "weighted_rating": 4.1},
        2571: {"title": "Matrix, The (1999)", "genres": "Action|Sci-Fi", "year": 1999, "average_rating": 4.2, "rating_count": 278, "weighted_rating": 4.1},
    }
    title_aliases = {
        838: generate_title_aliases("Emma (1996)")[2],
        26958: generate_title_aliases("Emma (1996)")[2],
        155: generate_title_aliases("Dark Knight, The (2008)")[2],
        47: generate_title_aliases("Seven (a.k.a. Se7en) (1995)")[2],
        2571: generate_title_aliases("Matrix, The (1999)")[2],
    }
    matcher.build_index(movies_meta, title_aliases)
    return matcher

def test_fuzzy_targets_resolution(sample_fuzzy_matcher):
    # Dark Knight queries
    m1 = sample_fuzzy_matcher.match_query("dark knight")
    assert m1.movieId == 155
    assert m1.match_status == "auto_accept"

    m2 = sample_fuzzy_matcher.match_query("the dark knight")
    assert m2.movieId == 155

    m3 = sample_fuzzy_matcher.match_query("darkknight")
    assert m3.movieId == 155

    # Se7en query
    m4 = sample_fuzzy_matcher.match_query("se7en")
    assert m4.movieId == 47

    # Matrix query
    m5 = sample_fuzzy_matcher.match_query("the matrix")
    assert m5.movieId == 2571

def test_fuzzy_confidence_bands(sample_fuzzy_matcher):
    # Low confidence query
    m_low = sample_fuzzy_matcher.match_query("xyzqwerty123")
    assert m_low.match_status == "no_match"
    assert m_low.movieId is None

def test_ambiguous_alias_does_not_report_full_confidence():
    """
    When an alias maps to multiple movies (e.g. 'hamlet' resolving to multiple adaptations),
    it must not report 100.0 confidence and should provide alternatives.
    """
    matcher = FuzzyTitleMatcher()
    movies_meta = {
        659: {"title": "Hamlet (1996)", "genres": "Drama", "year": 1996, "average_rating": 4.0, "rating_count": 50, "weighted_rating": 3.9},
        2820: {"title": "Hamlet (1964)", "genres": "Drama", "year": 1964, "average_rating": 3.8, "rating_count": 10, "weighted_rating": 3.6},
        3598: {"title": "Hamlet (2000)", "genres": "Crime|Drama|Romance|Thriller", "year": 2000, "average_rating": 3.2, "rating_count": 20, "weighted_rating": 3.4},
        1941: {"title": "Hamlet (1948)", "genres": "Drama", "year": 1948, "average_rating": 4.1, "rating_count": 15, "weighted_rating": 3.7},
    }
    title_aliases = {
        mid: generate_title_aliases(meta["title"])[2]
        for mid, meta in movies_meta.items()
    }
    matcher.build_index(movies_meta, title_aliases)
    result = matcher.match_query("hamlet")
    assert result.confidence_score < 100.0
    assert len(result.alternatives) >= 1
    assert result.movieId == 659

