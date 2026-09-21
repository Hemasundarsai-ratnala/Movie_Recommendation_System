import pytest
import pandas as pd
import numpy as np
from backend.app.services.content_model import ContentRecommender

def test_content_model_zero_genre_guard():
    movies_df = pd.DataFrame([
        {"movieId": 1, "title": "Toy Story (1995)", "genres": "Adventure|Animation|Children|Comedy|Fantasy"},
        {"movieId": 2, "title": "Jumanji (1995)", "genres": "Adventure|Children|Fantasy"},
        {"movieId": 3, "title": "No Genre Movie (2016)", "genres": "(no genres listed)"},
    ])
    model = ContentRecommender(top_k=2)
    model.fit(movies_df)

    # Ensure zero genre movie doesn't throw NaN
    mids, sims = model.get_neighbors(3)
    assert not np.isnan(sims).any()
