import React, { useState } from 'react';
import { Star, StarHalf } from 'lucide-react';

export default function StarRating({ rating = 0, onChange, readonly = false, size = 18 }) {
  const [hoverRating, setHoverRating] = useState(null);

  const displayRating = hoverRating !== null ? hoverRating : rating;

  const handleMouseMove = (e, index) => {
    if (readonly) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const isHalf = e.clientX - rect.left < rect.width / 2;
    const value = index + (isHalf ? 0.5 : 1.0);
    setHoverRating(value);
  };

  const handleClick = (e, index) => {
    if (readonly || !onChange) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const isHalf = e.clientX - rect.left < rect.width / 2;
    const value = index + (isHalf ? 0.5 : 1.0);
    onChange(value);
  };

  return (
    <div 
      className="inline-flex items-center gap-1"
      onMouseLeave={() => !readonly && setHoverRating(null)}
      style={{ display: 'inline-flex', gap: '4px', cursor: readonly ? 'default' : 'pointer' }}
    >
      {[0, 1, 2, 3, 4].map((index) => {
        const starValue = index + 1;
        const halfValue = index + 0.5;

        let fillState = 'empty';
        if (displayRating >= starValue) {
          fillState = 'full';
        } else if (displayRating >= halfValue) {
          fillState = 'half';
        }

        return (
          <span
            key={index}
            onMouseMove={(e) => handleMouseMove(e, index)}
            onClick={(e) => handleClick(e, index)}
            style={{ position: 'relative', display: 'inline-block' }}
            title={`${index + 1} Star${index > 0 ? 's' : ''}`}
          >
            {fillState === 'full' && (
              <Star size={size} fill="#f59e0b" color="#f59e0b" />
            )}
            {fillState === 'half' && (
              <StarHalf size={size} fill="#f59e0b" color="#f59e0b" />
            )}
            {fillState === 'empty' && (
              <Star size={size} color="#4b5563" />
            )}
          </span>
        );
      })}
      {rating > 0 && (
        <span style={{ fontSize: '0.85rem', color: '#f59e0b', fontWeight: '600', marginLeft: '4px' }}>
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  );
}
