import pytest
from backend.app.utils.preprocessing import (
    extract_year_and_clean,
    normalize_string_basic,
    unfold_article,
    generate_title_aliases,
)

def test_extract_year_and_clean():
    clean, year = extract_year_and_clean("Matrix, The (1999)")
    assert clean == "Matrix, The"
    assert year == 1999

    clean_no_yr, year_none = extract_year_and_clean("Babylon 5")
    assert clean_no_yr == "Babylon 5"
    assert year_none is None

def test_unfold_article():
    res1 = unfold_article("Matrix, The")
    assert "the matrix" in [r.lower() for r in res1] or "Matrix, The" in res1
    assert "matrix" in [r.lower() for r in res1] or "Matrix" in res1

    res2 = unfold_article("Misérables, Les")
    assert "les misérables" in [r.lower() for r in res2] or "les miserables" in [r.lower() for r in res2]

def test_generate_title_aliases_query_targets():
    # 1. Dark Knight, The (2008)
    _, _, aliases_dk = generate_title_aliases("Dark Knight, The (2008)")
    assert "the dark knight" in aliases_dk
    assert "dark knight" in aliases_dk
    assert "darkknight" in aliases_dk

    # 2. Seven (a.k.a. Se7en) (1995)
    _, _, aliases_seven = generate_title_aliases("Seven (a.k.a. Se7en) (1995)")
    assert "seven" in aliases_seven
    assert "se7en" in aliases_seven

    # 3. Matrix, The (1999)
    _, _, aliases_matrix = generate_title_aliases("Matrix, The (1999)")
    assert "the matrix" in aliases_matrix
    assert "matrix" in aliases_matrix

    # 4. Misérables, Les (1995)
    _, _, aliases_les = generate_title_aliases("Misérables, Les (1995)")
    assert "les miserables" in aliases_les
    assert "miserables" in aliases_les
