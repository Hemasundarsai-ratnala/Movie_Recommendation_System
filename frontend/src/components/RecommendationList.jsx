import React from 'react';
import MovieCard from './MovieCard';
import { Sliders, Sparkles, AlertCircle } from 'lucide-react';

export default function RecommendationList({ 
  recommendations = [], 
  isLoading = false, 
  mode, 
  coldStart = false,
  diversityLambda = 0.7,
  onDiversityChange,
}) {
  if (isLoading) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px', width: '100%' }}>
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="glass-panel skeleton" style={{ height: '320px' }} />
        ))}
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', width: '100%' }}>
        <AlertCircle size={40} color="#9ca3af" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ fontSize: '1.2rem', color: '#f3f4f6', marginBottom: '6px' }}>No Recommendations Yet</h3>
        <p style={{ color: '#9ca3af', fontSize: '0.9rem' }}>
          Select or search seed movies on the Discover page to generate personalized hybrid recommendations.
        </p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%' }}>
      {/* Controls Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={20} color="#a78bfa" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', color: '#f3f4f6' }}>
            Recommended Movies ({recommendations.length})
          </h2>
          {mode && (
            <span className="badge badge-auto" style={{ textTransform: 'none', letterSpacing: 0 }}>
              Mode: {mode.replace(/_/g, ' ')}
            </span>
          )}
        </div>

        {/* Diversity MMR Slider */}
        {onDiversityChange && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'rgba(18, 24, 36, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            padding: '8px 16px',
            borderRadius: '10px'
          }}>
            <Sliders size={16} color="#a78bfa" />
            <span style={{ fontSize: '0.85rem', color: '#d1d5db', fontWeight: '500' }}>
              Relevance vs Diversity (MMR):
            </span>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={diversityLambda}
              onChange={(e) => onDiversityChange(parseFloat(e.target.value))}
              style={{ accentColor: '#8b5cf6', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '0.85rem', color: '#a78bfa', fontWeight: '700', minWidth: '40px' }}>
              λ = {diversityLambda.toFixed(2)}
            </span>
          </div>
        )}
      </div>

      {/* Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '20px'
      }}>
        {recommendations.map((movie, idx) => (
          <MovieCard key={movie.movieId} movie={movie} rank={idx + 1} />
        ))}
      </div>
    </div>
  );
}
