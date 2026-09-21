import React from 'react';
import { Star, Sparkles, Film, Award, Users, Info } from 'lucide-react';
import StarRating from './StarRating';

export default function MovieCard({ movie, rank, onSelect }) {
  const contentScore = Math.round((movie.content_score || 0) * 100);
  const collabScore = Math.round((movie.collaborative_score || 0) * 100);
  const popScore = Math.round((movie.popularity_score || 0) * 100);
  const hybridScore = Math.round((movie.hybrid_score || 0) * 100);

  const genreList = movie.genres ? movie.genres.split('|') : [];

  return (
    <div 
      className="glass-panel"
      style={{
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top Rank Badge */}
      {rank && (
        <div style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.3))',
          border: '1px solid rgba(139, 92, 246, 0.4)',
          borderRadius: '8px',
          padding: '4px 10px',
          fontSize: '0.85rem',
          fontWeight: '700',
          color: '#a78bfa'
        }}>
          #{rank}
        </div>
      )}

      <div>
        {/* Title & Year */}
        <h3 style={{
          fontSize: '1.15rem',
          fontWeight: '700',
          color: '#f3f4f6',
          paddingRight: rank ? '40px' : '0',
          lineHeight: 1.3,
          marginBottom: '6px'
        }}>
          {movie.title}
        </h3>

        {/* Genre Tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
          {genreList.map((g, idx) => (
            <span 
              key={idx}
              style={{
                fontSize: '0.72rem',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: '#d1d5db',
                padding: '2px 8px',
                borderRadius: '4px',
                fontWeight: '500'
              }}
            >
              {g}
            </span>
          ))}
        </div>

        {/* Ratings Row */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 12px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '8px',
          marginBottom: '14px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <StarRating rating={movie.average_rating} readonly size={14} />
            <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
              ({movie.rating_count} ratings)
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', color: '#f59e0b', fontWeight: '600' }}>
            <Award size={14} /> WR {movie.weighted_rating?.toFixed(2)}
          </div>
        </div>

        {/* Score Breakdown Pills */}
        <div style={{ marginBottom: '14px' }}>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '6px', fontWeight: '600' }}>
            Signal Contributions:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
            <div style={{
              background: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid rgba(139, 92, 246, 0.2)',
              borderRadius: '6px',
              padding: '6px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.65rem', color: '#c4b5fd', textTransform: 'uppercase' }}>Content</div>
              <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#a78bfa' }}>{contentScore}%</div>
            </div>

            <div style={{
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.2)',
              borderRadius: '6px',
              padding: '6px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.65rem', color: '#67e8f9', textTransform: 'uppercase' }}>Collab</div>
              <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#38bdf8' }}>{collabScore}%</div>
            </div>

            <div style={{
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              borderRadius: '6px',
              padding: '6px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.65rem', color: '#fde68a', textTransform: 'uppercase' }}>Popularity</div>
              <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#fbbf24' }}>{popScore}%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Explanation Banner */}
      {movie.explanation && (
        <div style={{
          background: 'rgba(99, 102, 241, 0.08)',
          borderLeft: '3px solid #6366f1',
          padding: '10px 12px',
          borderRadius: '0 6px 6px 0',
          fontSize: '0.8rem',
          color: '#e0e7ff',
          lineHeight: 1.4,
          display: 'flex',
          gap: '8px',
          alignItems: 'flex-start'
        }}>
          <Sparkles size={16} color="#818cf8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>{movie.explanation}</span>
        </div>
      )}
    </div>
  );
}
