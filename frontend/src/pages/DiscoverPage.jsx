import React, { useState } from 'react';
import { Compass, Sparkles, Sliders, Plus, Play, RefreshCw, Bookmark, Zap } from 'lucide-react';
import SearchBar from '../components/SearchBar';
import StarRating from '../components/StarRating';
import SelectedMoviesList from '../components/SelectedMoviesList';

const GENRE_OPTIONS = [
  'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
  'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
  'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance',
  'Sci-Fi', 'Thriller', 'War', 'Western'
];

const PROFILE_PRESETS = [
  {
    id: 'scifi',
    name: 'Sci-Fi & Cyberpunk',
    icon: '🚀',
    genres: ['Sci-Fi', 'Action'],
    seeds: [
      { movieId: 2571, title: 'Matrix, The (1999)', genres: 'Action|Sci-Fi|Thriller', rating: 5.0 },
      { movieId: 109487, title: 'Interstellar (2014)', genres: 'Sci-Fi|IMAX', rating: 5.0 },
      { movieId: 79132, title: 'Inception (2010)', genres: 'Action|Crime|Drama|Mystery|Sci-Fi|Thriller|IMAX', rating: 4.5 },
    ]
  },
  {
    id: 'crime_thriller',
    name: 'Mind-Bending Thrillers',
    icon: '🔍',
    genres: ['Crime', 'Mystery', 'Thriller'],
    seeds: [
      { movieId: 47, title: 'Seven (a.k.a. Se7en) (1995)', genres: 'Mystery|Thriller', rating: 5.0 },
      { movieId: 2959, title: 'Fight Club (1999)', genres: 'Action|Crime|Drama|Thriller', rating: 4.5 },
      { movieId: 593, title: 'Silence of the Lambs, The (1991)', genres: 'Crime|Horror|Thriller', rating: 5.0 },
    ]
  },
  {
    id: 'action_superhero',
    name: 'Action & Superheroes',
    icon: '⚡',
    genres: ['Action', 'Crime'],
    seeds: [
      { movieId: 58559, title: 'Dark Knight, The (2008)', genres: 'Action|Crime|Drama|IMAX', rating: 5.0 },
      { movieId: 2571, title: 'Matrix, The (1999)', genres: 'Action|Sci-Fi|Thriller', rating: 4.5 },
    ]
  },
  {
    id: 'drama_classics',
    name: 'Award-Winning Classics',
    icon: '🏆',
    genres: ['Drama', 'Crime'],
    seeds: [
      { movieId: 318, title: 'Shawshank Redemption, The (1994)', genres: 'Crime|Drama', rating: 5.0 },
      { movieId: 296, title: 'Pulp Fiction (1994)', genres: 'Comedy|Crime|Drama|Thriller', rating: 4.5 },
      { movieId: 356, title: 'Forrest Gump (1994)', genres: 'Comedy|Drama|Romance|War', rating: 4.5 },
    ]
  },
  {
    id: 'animation',
    name: 'Animation & Fantasy',
    icon: '🎨',
    genres: ['Animation', 'Adventure', 'Fantasy'],
    seeds: [
      { movieId: 1, title: 'Toy Story (1995)', genres: 'Adventure|Animation|Children|Comedy|Fantasy', rating: 5.0 },
      { movieId: 5618, title: 'Spirited Away (Sen to Chihiro no kamikakushi) (2001)', genres: 'Adventure|Animation|Fantasy', rating: 5.0 },
    ]
  },
];

const DEFAULT_SEEDS = [
  { movieId: 2571, title: 'Matrix, The (1999)', genres: 'Action|Sci-Fi|Thriller', rating: 5.0 },
  { movieId: 58559, title: 'Dark Knight, The (2008)', genres: 'Action|Crime|Drama|IMAX', rating: 4.5 },
];

const DEFAULT_WEIGHTS = {
  content: 0.45,
  collab: 0.45,
  pop: 0.10,
  diversityLambda: 0.7,
};

export default function DiscoverPage({
  onGenerateHybrid,
  seeds: propsSeeds,
  setSeeds: propsSetSeeds,
  selectedGenres: propsSelectedGenres,
  setSelectedGenres: propsSetSelectedGenres,
  weights: propsWeights,
  setWeights: propsSetWeights,
}) {
  // Local fallbacks if not hoisted
  const [localSeeds, setLocalSeeds] = useState(DEFAULT_SEEDS);
  const [localGenres, setLocalGenres] = useState([]);
  const [localWeights, setLocalWeights] = useState(DEFAULT_WEIGHTS);

  const seeds = propsSeeds !== undefined ? propsSeeds : localSeeds;
  const setSeeds = propsSetSeeds !== undefined ? propsSetSeeds : setLocalSeeds;
  const selectedGenres = propsSelectedGenres !== undefined ? propsSelectedGenres : localGenres;
  const setSelectedGenres = propsSetSelectedGenres !== undefined ? propsSetSelectedGenres : setLocalGenres;
  const weights = propsWeights !== undefined ? propsWeights : localWeights;
  const setWeights = propsSetWeights !== undefined ? propsSetWeights : setLocalWeights;

  const [newSeedRating, setNewSeedRating] = useState(5.0);
  const [tempMovie, setTempMovie] = useState(null);

  const handleSelectMovieFromSearch = (movie) => {
    setTempMovie(movie);
  };

  const handleAddTempMovie = () => {
    if (!tempMovie) return;
    const exists = seeds.some(s => s.movieId === tempMovie.movieId);
    if (!exists) {
      setSeeds([...seeds, {
        movieId: tempMovie.movieId,
        title: tempMovie.title,
        genres: tempMovie.genres,
        rating: newSeedRating
      }]);
    }
    setTempMovie(null);
    setNewSeedRating(5.0);
  };

  const handleApplyPreset = (preset) => {
    setSeeds(preset.seeds);
    setSelectedGenres(preset.genres);
  };

  const handleUpdateRating = (index, rating) => {
    const updated = [...seeds];
    updated[index].rating = rating;
    setSeeds(updated);
  };

  const handleRemoveSeed = (index) => {
    setSeeds(seeds.filter((_, i) => i !== index));
  };

  const handleToggleGenre = (g) => {
    if (selectedGenres.includes(g)) {
      setSelectedGenres(selectedGenres.filter(x => x !== g));
    } else {
      setSelectedGenres([...selectedGenres, g]);
    }
  };

  const handleGenerate = () => {
    onGenerateHybrid(seeds, selectedGenres, weights);
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div style={{ textAlign: 'center', marginBottom: '10px' }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: '800', color: '#f3f4f6', marginBottom: '8px' }}>
          Personalized <span className="gradient-text">Hybrid Profile</span>
        </h1>
        <p style={{ color: '#9ca3af', fontSize: '1rem' }}>
          Add your favorite movies with star ratings or pick stated genres to compute hybrid candidate fusion.
        </p>
      </div>

      {/* Quick Profile Presets */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={18} color="#fbbf24" /> Quick-Seed Profile Presets
        </h3>
        <p style={{ fontSize: '0.85rem', color: '#9ca3af', marginBottom: '14px' }}>
          Instantly populate your profile with verified MovieLens seeds & curated genres:
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {PROFILE_PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleApplyPreset(preset)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(255, 255, 255, 0.04)',
                color: '#f3f4f6',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: '500',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)';
                e.currentTarget.style.borderColor = '#8b5cf6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
              }}
            >
              <span>{preset.icon}</span>
              <span>{preset.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Add Movie Section */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus size={18} color="#a78bfa" /> Add Movie to Profile
        </h3>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '300px' }}>
            <SearchBar onSelectMovie={handleSelectMovieFromSearch} />
          </div>

          {tempMovie && (
            <div style={{
              background: 'rgba(139, 92, 246, 0.15)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '10px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              width: '100%',
              marginTop: '10px'
            }}>
              <div>
                <div style={{ fontWeight: '700', color: '#f3f4f6' }}>{tempMovie.title}</div>
                <div style={{ fontSize: '0.8rem', color: '#a78bfa' }}>{tempMovie.genres}</div>
              </div>

              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '2px' }}>Your Rating:</div>
                  <StarRating rating={newSeedRating} onChange={setNewSeedRating} size={18} />
                </div>
                <button className="btn-primary" onClick={handleAddTempMovie}>
                  Add Seed
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Selected Seeds Manager */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <SelectedMoviesList
          seeds={seeds}
          onUpdateRating={handleUpdateRating}
          onRemoveSeed={handleRemoveSeed}
          onClearAll={() => setSeeds([])}
        />
      </div>

      {/* Stated Genres Selector */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '14px' }}>
          Stated Genre Preferences (Optional)
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {GENRE_OPTIONS.map((g) => {
            const isSel = selectedGenres.includes(g);
            return (
              <button
                key={g}
                onClick={() => handleToggleGenre(g)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: isSel ? '1px solid #8b5cf6' : '1px solid rgba(255, 255, 255, 0.1)',
                  background: isSel ? 'rgba(139, 92, 246, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                  color: isSel ? '#a78bfa' : '#9ca3af',
                  fontWeight: isSel ? '600' : '400',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  transition: 'all 0.15s ease'
                }}
              >
                {g}
              </button>
            );
          })}
        </div>
      </div>

      {/* Model Fusion Tuning Controls */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={18} color="#38bdf8" /> Hybrid Score Channel Weights
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#d1d5db', marginBottom: '6px' }}>
              <span>Content Weight (W_content)</span>
              <span style={{ color: '#a78bfa', fontWeight: '700' }}>{weights.content.toFixed(2)}</span>
            </div>
            <input
              type="range" min="0" max="1" step="0.05"
              value={weights.content}
              onChange={(e) => setWeights({ ...weights, content: parseFloat(e.target.value) })}
              style={{ width: '100%', accentColor: '#8b5cf6' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#d1d5db', marginBottom: '6px' }}>
              <span>Collaborative Weight (W_collab)</span>
              <span style={{ color: '#38bdf8', fontWeight: '700' }}>{weights.collab.toFixed(2)}</span>
            </div>
            <input
              type="range" min="0" max="1" step="0.05"
              value={weights.collab}
              onChange={(e) => setWeights({ ...weights, collab: parseFloat(e.target.value) })}
              style={{ width: '100%', accentColor: '#38bdf8' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#d1d5db', marginBottom: '6px' }}>
              <span>Popularity Weight (W_pop)</span>
              <span style={{ color: '#fbbf24', fontWeight: '700' }}>{weights.pop.toFixed(2)}</span>
            </div>
            <input
              type="range" min="0" max="1" step="0.05"
              value={weights.pop}
              onChange={(e) => setWeights({ ...weights, pop: parseFloat(e.target.value) })}
              style={{ width: '100%', accentColor: '#fbbf24' }}
            />
          </div>
        </div>
      </div>

      {/* Generate CTA Button */}
      <div style={{ textAlign: 'center', marginTop: '10px' }}>
        <button className="btn-primary" style={{ padding: '16px 36px', fontSize: '1.1rem' }} onClick={handleGenerate}>
          <Play size={20} /> Generate Hybrid Recommendations
        </button>
      </div>
    </div>
  );
}
