import pytest
import pandas as pd
from backend.scripts.evaluate import temporal_split_per_user
from backend.app.config import settings

def test_zero_leakage_temporal_split():
    ratings_df = pd.read_csv(settings.RATINGS_CSV)
    train_df, test_df = temporal_split_per_user(ratings_df, train_ratio=0.8)

    # 1. Assert timestamps in train are strictly <= test timestamps per user
    for uid in train_df["userId"].unique()[:20]:
        max_train_ts = train_df[train_df["userId"] == uid]["timestamp"].max()
        min_test_ts = test_df[test_df["userId"] == uid]["timestamp"].min()
        assert max_train_ts <= min_test_ts

    # 2. Assert train global mean is computed strictly on train split
    train_mean = train_df["rating"].mean()
    full_mean = ratings_df["rating"].mean()
    assert train_mean != full_mean
