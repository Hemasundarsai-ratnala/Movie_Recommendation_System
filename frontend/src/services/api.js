const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  getHealth: () => fetchJson('/api/health'),
  
  searchMovies: (query, limit = 10) => 
    fetchJson(`/api/movies/search?q=${encodeURIComponent(query)}&limit=${limit}`),
    
  getMovieById: (movieId) => fetchJson(`/api/movies/${movieId}`),
  
  getInsights: () => fetchJson('/api/insights'),
  
  recommendSingle: (queryOrId, rating = 5.0, topN = 10, weights = {}) =>
    fetchJson('/api/recommend/single', {
      method: 'POST',
      body: JSON.stringify({
        query_or_id: String(queryOrId),
        rating: parseFloat(rating),
        top_n: parseInt(topN),
        content_weight: weights.content,
        collaborative_weight: weights.collab,
        popularity_weight: weights.pop,
        diversity_lambda: weights.diversityLambda,
      }),
    }),
    
  recommendHybrid: (seeds, topN = 10, weights = {}) =>
    fetchJson('/api/recommend/hybrid', {
      method: 'POST',
      body: JSON.stringify({
        seeds: seeds.map(s => ({
          query_or_id: String(s.movieId || s.query),
          rating: parseFloat(s.rating),
        })),
        top_n: parseInt(topN),
        content_weight: weights.content,
        collaborative_weight: weights.collab,
        popularity_weight: weights.pop,
        diversity_lambda: weights.diversityLambda,
      }),
    }),
    
  recommendPersonalized: (seeds, statedGenres = [], topN = 10, weights = {}) =>
    fetchJson('/api/recommend/personalized', {
      method: 'POST',
      body: JSON.stringify({
        seeds: seeds.map(s => ({
          query_or_id: String(s.movieId || s.query),
          rating: parseFloat(s.rating),
        })),
        stated_genres: statedGenres,
        top_n: parseInt(topN),
        content_weight: weights.content,
        collaborative_weight: weights.collab,
        popularity_weight: weights.pop,
        diversity_lambda: weights.diversityLambda,
      }),
    }),
};
