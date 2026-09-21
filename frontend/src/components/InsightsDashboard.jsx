import React from 'react';
import { Database, Film, Star, Users, Percent, Award, Layers } from 'lucide-react';
import MovieCard from './MovieCard';

export default function InsightsDashboard({ insights }) {
  if (!insights) return null;

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '30px' }}>
      {/* Overview Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        {[
          { label: 'Total Catalog Movies', value: insights.total_movies?.toLocaleString(), icon: Film, color: '#a78bfa' },
          { label: 'Total User Ratings', value: insights.total_ratings?.toLocaleString(), icon: Database, color: '#38bdf8' },
          { label: 'Global Mean Rating', value: insights.global_mean_rating?.toFixed(4), icon: Star, color: '#fbbf24' },
          { label: 'Unique Users', value: insights.unique_users, icon: Users, color: '#34d399' },
          { label: 'Unique Rated Movies', value: insights.unique_rated_movies?.toLocaleString(), icon: Layers, color: '#f472b6' },
          { label: 'Matrix Sparsity', value: `${insights.sparsity_percentage}%`, icon: Percent, color: '#f87171' },
        ].map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', color: '#9ca3af', fontWeight: '500' }}>{stat.label}</span>
                <Icon size={20} color={stat.color} />
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#f3f4f6' }}>
                {stat.value}
              </div>
            </div>
          );
        })}
      </div>

      {/* Genre Distribution */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '16px' }}>
          Genre Distribution Across Catalog (20 Tokens)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
          {insights.genre_distribution?.map((g) => {
            const pct = Math.round((g.count / insights.total_movies) * 100);
            return (
              <div key={g.genre} style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '10px 14px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ fontWeight: '600', color: '#e5e7eb' }}>{g.genre}</span>
                  <span style={{ color: '#a78bfa', fontWeight: '700' }}>{g.count} ({pct}%)</span>
                </div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #38bdf8)' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Weighted Movies vs Most Rated Movies */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={18} color="#fbbf24" /> Top 10 Bayesian Weighted Rated Movies (m=50)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {insights.top_weighted_movies?.map((m, idx) => (
              <div key={m.movieId} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: '700', color: '#a78bfa', minWidth: '24px' }}>#{idx + 1}</span>
                  <div>
                    <div style={{ fontWeight: '600', color: '#f3f4f6', fontSize: '0.9rem' }}>{m.title}</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{m.genres}</div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#fbbf24', fontWeight: '700', fontSize: '0.9rem' }}>WR {m.weighted_rating?.toFixed(2)}</div>
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{m.rating_count} ratings ({m.average_rating?.toFixed(2)} avg)</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#f3f4f6', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={18} color="#38bdf8" /> Top 10 Most-Rated Movies
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {insights.most_rated_movies?.map((m, idx) => (
              <div key={m.movieId} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: '700', color: '#38bdf8', minWidth: '24px' }}>#{idx + 1}</span>
                  <div>
                    <div style={{ fontWeight: '600', color: '#f3f4f6', fontSize: '0.9rem' }}>{m.title}</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{m.genres}</div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#38bdf8', fontWeight: '700', fontSize: '0.9rem' }}>{m.rating_count} ratings</div>
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{m.average_rating?.toFixed(2)} avg</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
