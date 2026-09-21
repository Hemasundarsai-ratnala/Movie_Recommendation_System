import React from 'react';
import { Trash2, Film, Star } from 'lucide-react';
import StarRating from './StarRating';

export default function SelectedMoviesList({ seeds = [], onUpdateRating, onRemoveSeed, onClearAll }) {
  if (!seeds || seeds.length === 0) {
    return (
      <div style={{
        padding: '24px',
        textAlign: 'center',
        border: '1px dashed rgba(255, 255, 255, 0.12)',
        borderRadius: '12px',
        color: '#9ca3af',
        fontSize: '0.9rem'
      }}>
        No seed movies added yet. Search and select movies above to build your preference profile.
      </div>
    );
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '0.9rem', color: '#d1d5db', fontWeight: '600' }}>
          Selected Seed Movies ({seeds.length})
        </span>
        <button
          onClick={onClearAll}
          style={{
            background: 'none',
            border: 'none',
            color: '#f87171',
            fontSize: '0.8rem',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          Clear All
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {seeds.map((seed, idx) => (
          <div
            key={`${seed.movieId || seed.title}-${idx}`}
            style={{
              background: 'rgba(15, 23, 42, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '10px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Film size={18} color="#a78bfa" />
              <div>
                <div style={{ fontWeight: '600', color: '#f3f4f6', fontSize: '0.95rem' }}>
                  {seed.title}
                </div>
                {seed.genres && (
                  <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{seed.genres}</div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>Your Rating</div>
                <StarRating
                  rating={seed.rating}
                  onChange={(val) => onUpdateRating(idx, val)}
                  size={16}
                />
              </div>

              <button
                onClick={() => onRemoveSeed(idx)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#9ca3af',
                  cursor: 'pointer',
                  padding: '4px',
                  transition: 'color 0.2s'
                }}
                title="Remove movie"
              >
                <Trash2 size={16} color="#f87171" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
