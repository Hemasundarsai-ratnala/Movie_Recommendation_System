import React from 'react';
import { Sparkles, Film, ArrowRight, ShieldCheck, Compass, Sliders, Zap } from 'lucide-react';
import SearchBar from '../components/SearchBar';

export default function HomePage({ onSelectSingleMovie, onNavigateDiscover }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '60px', padding: '20px 0' }}>
      {/* Hero Section */}
      <div style={{
        textAlign: 'center',
        maxWidth: '840px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '24px'
      }}>
        <div className="badge badge-auto" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 14px' }}>
          <Sparkles size={14} /> NLP-Powered Fuzzy Matching + Centered Cosine CF
        </div>

        <h1 style={{ fontSize: '3.2rem', fontWeight: '800', lineHeight: 1.15, letterSpacing: '-0.02em' }}>
          Discover Next-Level Movie Recommendations with <span className="gradient-text">Hybrid AI</span>
        </h1>

        <p style={{ fontSize: '1.15rem', color: '#9ca3af', lineHeight: 1.6, maxWidth: '700px' }}>
          Combines TF-IDF content similarity, mean-centered collaborative filtering with shrinkage, RapidFuzz title aliasing, and Bayesian weighted ranking.
        </p>

        {/* Hero Search Box */}
        <div style={{ width: '100%', maxWidth: '640px', marginTop: '10px' }}>
          <SearchBar onSelectMovie={onSelectSingleMovie} />
        </div>

        <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
          <button className="btn-primary" onClick={onNavigateDiscover}>
            <Compass size={18} /> Build Personal Seed Profile <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Feature Highlights Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '24px',
        maxWidth: '1200px',
        margin: '0 auto',
        width: '100%'
      }}>
        {[
          {
            title: 'Alias-Based Fuzzy Matcher',
            desc: 'Handles inverted titles like "Matrix, The", foreign titles, and spelling errors ("se7en", "dark knigt") using RapidFuzz pre-indexed searchable title aliases.',
            icon: Zap,
            color: '#a78bfa'
          },
          {
            title: 'Centered Cosine Collaborative',
            desc: 'Mean-centers user ratings over observed entries and applies shrinkage confidence weighting sim * n / (n + 25) with a 20 co-rater floor.',
            icon: Sliders,
            color: '#38bdf8'
          },
          {
            title: 'Bayesian Weighted Popularity',
            desc: 'Ranks candidates with prior m=50 Bayesian smoothing, guarding against single-rating 5.0 false positives and solving long-tail cold start.',
            icon: ShieldCheck,
            color: '#fbbf24'
          },
        ].map((feat, idx) => {
          const Icon = feat.icon;
          return (
            <div key={idx} className="glass-panel" style={{ padding: '24px' }}>
              <div style={{
                background: 'rgba(255, 255, 255, 0.05)',
                width: '44px',
                height: '44px',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <Icon size={22} color={feat.color} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '8px' }}>
                {feat.title}
              </h3>
              <p style={{ color: '#9ca3af', fontSize: '0.92rem', lineHeight: 1.5 }}>
                {feat.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
