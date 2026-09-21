import numpy as np
import pandas as pd
from typing import Dict, Tuple, Set
from scipy.sparse import csr_matrix
from backend.app.config import settings

class CollaborativeRecommender:
    def __init__(
        self,
        min_common_ratings: int = settings.MIN_COMMON_RATINGS,
        shrinkage_lambda: float = settings.SHRINKAGE_LAMBDA,
        top_k: int = settings.TOP_K_NEIGHBOURS,
    ):
        self.min_common_ratings = min_common_ratings
        self.shrinkage_lambda = shrinkage_lambda
        self.top_k = top_k

        self.neighbor_indices: Dict[int, np.ndarray] = {}
        self.neighbor_scores: Dict[int, np.ndarray] = {}
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        self.rated_movie_ids: Set[int] = set()

    def fit(self, ratings_df: pd.DataFrame, all_movie_ids: list[int]):
        """
        Fits centered-cosine item similarity matrix with shrinkage weighting
        from ratings training dataframe.
        """
        self.rated_movie_ids = set(ratings_df["movieId"].unique())
        all_movie_ids_sorted = sorted(list(set(all_movie_ids)))

        self.movie_id_to_idx = {mid: i for i, mid in enumerate(all_movie_ids_sorted)}
        self.idx_to_movie_id = {i: mid for i, mid in enumerate(all_movie_ids_sorted)}

        user_ids = sorted(ratings_df["userId"].unique())
        user_id_to_idx = {uid: i for i, uid in enumerate(user_ids)}

        n_users = len(user_ids)
        n_items = len(all_movie_ids_sorted)

        # Build sparse matrix of raw ratings
        rows = [user_id_to_idx[u] for u in ratings_df["userId"]]
        cols = [self.movie_id_to_idx[m] for m in ratings_df["movieId"]]
        data = ratings_df["rating"].values.astype(np.float32)

        raw_matrix = csr_matrix((data, (rows, cols)), shape=(n_users, n_items))

        # Compute user means over observed entries only
        user_sums = raw_matrix.sum(axis=1).A1
        user_counts = (raw_matrix > 0).sum(axis=1).A1
        user_means = np.zeros(n_users, dtype=np.float32)
        nonzero_mask = user_counts > 0
        user_means[nonzero_mask] = user_sums[nonzero_mask] / user_counts[nonzero_mask]

        # Build mean-centered ratings matrix
        # Subtract user mean from non-zero entries
        centered_data = data - user_means[rows]
        centered_matrix = csr_matrix((centered_data, (rows, cols)), shape=(n_users, n_items))

        # Build binary indicator matrix for co-ratings
        binary_data = np.ones(len(data), dtype=np.float32)
        binary_matrix = csr_matrix((binary_data, (rows, cols)), shape=(n_users, n_items))

        # Co-rating counts matrix (n_items x n_items)
        co_matrix = (binary_matrix.T @ binary_matrix).tocsr()

        # Dot product of centered ratings vectors (n_items x n_items)
        dot_matrix = (centered_matrix.T @ centered_matrix).tocsr()

        # Item vector norms
        item_norms = np.sqrt((centered_matrix.power(2)).sum(axis=0)).A1
        # Avoid division by zero
        item_norms[item_norms == 0] = 1e-9

        self.neighbor_indices = {}
        self.neighbor_scores = {}

        # Compute top-k neighbors per item
        for j in range(n_items):
            mid = self.idx_to_movie_id[j]

            # Extract row j from dot product and co-ratings
            start_ptr = dot_matrix.indptr[j]
            end_ptr = dot_matrix.indptr[j + 1]

            if start_ptr == end_ptr:
                continue

            neighbor_cols = dot_matrix.indices[start_ptr:end_ptr]
            dots = dot_matrix.data[start_ptr:end_ptr]

            # Filter self
            mask = neighbor_cols != j
            neighbor_cols = neighbor_cols[mask]
            dots = dots[mask]

            if len(neighbor_cols) == 0:
                continue

            # Get co-rating counts for these neighbors
            # Lookup co_matrix for (j, neighbor_cols)
            co_start = co_matrix.indptr[j]
            co_end = co_matrix.indptr[j + 1]
            co_indices = co_matrix.indices[co_start:co_end]
            co_data = co_matrix.data[co_start:co_end]
            co_dict = dict(zip(co_indices, co_data))

            co_counts = np.array([co_dict.get(col, 0) for col in neighbor_cols], dtype=np.float32)

            # Apply floor: min_common_ratings
            valid_floor = co_counts >= self.min_common_ratings
            if not np.any(valid_floor):
                continue

            neighbor_cols = neighbor_cols[valid_floor]
            dots = dots[valid_floor]
            co_counts = co_counts[valid_floor]

            # Raw Pearson / centered cosine similarity
            denoms = item_norms[j] * item_norms[neighbor_cols]
            sims_raw = dots / denoms

            # Shrinkage weighting
            shrinkage = co_counts / (co_counts + self.shrinkage_lambda)
            sims_adj = sims_raw * shrinkage

            # Keep top-k positive similarity neighbors
            pos_mask = sims_adj > 1e-5
            if not np.any(pos_mask):
                continue

            neighbor_cols = neighbor_cols[pos_mask]
            sims_adj = sims_adj[pos_mask]

            if len(sims_adj) <= self.top_k:
                top_order = np.argsort(sims_adj)[::-1]
            else:
                top_order = np.argpartition(sims_adj, -self.top_k)[-self.top_k:]
                top_order = top_order[np.argsort(sims_adj[top_order])[::-1]]

            top_cols = neighbor_cols[top_order]
            top_sims = sims_adj[top_order].astype(np.float32)

            top_mids = np.array([self.idx_to_movie_id[idx] for idx in top_cols], dtype=np.int32)

            self.neighbor_indices[mid] = top_mids
            self.neighbor_scores[mid] = top_sims

    def get_neighbors(self, movie_id: int) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (neighbor_movie_ids, similarity_scores) for a movie_id."""
        if movie_id not in self.neighbor_indices:
            return np.array([], dtype=np.int32), np.array([], dtype=np.float32)
        return self.neighbor_indices[movie_id], self.neighbor_scores[movie_id]
