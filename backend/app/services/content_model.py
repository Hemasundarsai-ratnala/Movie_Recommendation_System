import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.app.config import settings
from backend.app.utils.preprocessing import extract_year_and_clean, normalize_string_basic

class ContentRecommender:
    def __init__(self, top_k: int = settings.TOP_K_NEIGHBOURS):
        self.top_k = top_k
        self.vectorizer: TfidfVectorizer = None
        # neighbor_indices: maps movieId -> np.ndarray of neighbor movieIds
        self.neighbor_indices: Dict[int, np.ndarray] = {}
        # neighbor_scores: maps movieId -> np.ndarray of similarity scores (float32)
        self.neighbor_scores: Dict[int, np.ndarray] = {}
        # movie_id_to_idx: maps movieId -> 0-based row index in TF-IDF matrix
        self.movie_id_to_idx: Dict[int, int] = {}
        # idx_to_movie_id: maps row index -> movieId
        self.idx_to_movie_id: Dict[int, int] = {}

    def fit(self, movies_df: pd.DataFrame):
        """
        Fits TF-IDF vectorizer over (title_tokens + genre_tokens + decade)
        and computes block-wise sparse top-k cosine similarity lists per movie.
        """
        documents = []
        movie_ids = movies_df["movieId"].values

        self.movie_id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}
        self.idx_to_movie_id = {i: mid for i, mid in enumerate(movie_ids)}

        for _, row in movies_df.iterrows():
            title = str(row["title"])
            clean_title, year = extract_year_and_clean(title)
            norm_title = normalize_string_basic(clean_title)

            genres = str(row["genres"]).replace("|", " ").replace("(no genres listed)", "no_genres_listed")

            decade_str = ""
            if year:
                decade_str = f"decade_{year // 10 * 10}s"

            doc = f"{norm_title} {genres} {decade_str}".strip()
            documents.append(doc)

        # Build TF-IDF matrix (L2 normalized)
        self.vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b\w+\b",
            stop_words="english",
            norm="l2",
            sublinear_tf=True,
        )
        tfidf_matrix = self.vectorizer.fit_transform(documents)

        # Block-wise sparse matrix multiplication to find top-k neighbors per movie
        n_movies = len(movie_ids)
        batch_size = 500
        self.neighbor_indices = {}
        self.neighbor_scores = {}

        for start_idx in range(0, n_movies, batch_size):
            end_idx = min(start_idx + batch_size, n_movies)
            batch = tfidf_matrix[start_idx:end_idx]
            # Batch similarity: (batch_size, n_movies)
            batch_sims = batch.dot(tfidf_matrix.T).toarray()

            for i in range(end_idx - start_idx):
                global_idx = start_idx + i
                mid = movie_ids[global_idx]
                sim_row = batch_sims[i]

                # Zero out self similarity
                sim_row[global_idx] = 0.0

                # Guard against NaN/zero-norm
                if np.isnan(sim_row).any():
                    sim_row = np.nan_to_num(sim_row, 0.0)

                # Get top-k indices
                if len(sim_row) <= self.top_k:
                    top_indices = np.argsort(sim_row)[::-1]
                else:
                    top_indices = np.argpartition(sim_row, -self.top_k)[-self.top_k:]
                    top_indices = top_indices[np.argsort(sim_row[top_indices])[::-1]]

                # Keep non-zero similarity entries
                valid_mask = sim_row[top_indices] > 1e-5
                top_indices = top_indices[valid_mask]
                top_scores = sim_row[top_indices].astype(np.float32)

                top_mids = np.array([self.idx_to_movie_id[idx] for idx in top_indices], dtype=np.int32)

                self.neighbor_indices[mid] = top_mids
                self.neighbor_scores[mid] = top_scores

    def get_neighbors(self, movie_id: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (neighbor_movie_ids, similarity_scores) for a given movie_id.
        """
        if movie_id not in self.neighbor_indices:
            return np.array([], dtype=np.int32), np.array([], dtype=np.float32)
        return self.neighbor_indices[movie_id], self.neighbor_scores[movie_id]
