import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Film, CheckCircle, HelpCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function SearchBar({ onSelectMovie, placeholder = "Search by movie title (e.g. 'the dark knight', 'interstellar', 'se7en')..." }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim().length > 0) {
        setIsLoading(true);
        try {
          const res = await api.searchMovies(query, 10);
          setResults(res);
          setIsOpen(true);
          setSelectedIndex(-1);
        } catch (err) {
          console.error('Search error:', err);
        } finally {
          setIsLoading(false);
        }
      } else {
        setResults([]);
        setIsOpen(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        handleSelect(results[selectedIndex]);
      } else if (results.length > 0) {
        handleSelect(results[0]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (movie) => {
    onSelectMovie(movie);
    setQuery('');
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} style={{ position: 'relative', width: '100%' }}>
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <Search 
          size={20} 
          color="#9ca3af" 
          style={{ position: 'absolute', left: '16px', pointerEvents: 'none' }} 
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim() && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="input-glass"
          style={{ paddingLeft: '48px', paddingRight: '44px' }}
        />
        {query && (
          <button
            onClick={() => { setQuery(''); setResults([]); setIsOpen(false); }}
            style={{
              position: 'absolute',
              right: '14px',
              background: 'none',
              border: 'none',
              color: '#9ca3af',
              cursor: 'pointer'
            }}
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: 0,
          right: 0,
          background: '#121824',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '12px',
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.6)',
          zIndex: 100,
          maxHeight: '380px',
          overflowY: 'auto',
          padding: '8px'
        }}>
          {isLoading ? (
            <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af', fontSize: '0.9rem' }}>
              Searching movie titles...
            </div>
          ) : results.length > 0 ? (
            results.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              const isAuto = item.match_status === 'auto_accept';
              const isDidYouMean = item.match_status === 'did_you_mean';

              return (
                <div
                  key={`${item.movieId}-${idx}`}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    background: isSelected ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Film size={18} color="#a78bfa" />
                    <div>
                      <div style={{ fontWeight: '600', color: '#f3f4f6', fontSize: '0.95rem' }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '2px' }}>
                        {item.genres}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isAuto && (
                      <span className="badge badge-auto" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle size={12} /> Auto ({item.confidence_score}%)
                      </span>
                    )}
                    {isDidYouMean && (
                      <span className="badge badge-did-you-mean" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <HelpCircle size={12} /> Did You Mean ({item.confidence_score}%)
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{ padding: '16px', textAlign: 'center', color: '#f87171', fontSize: '0.9rem' }}>
              No confident movie match found for "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}
