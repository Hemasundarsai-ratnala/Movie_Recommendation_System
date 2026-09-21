import React from 'react';
import InsightsDashboard from '../components/InsightsDashboard';
import { BarChart2 } from 'lucide-react';

export default function InsightsPage({ insights, isLoading }) {
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#9ca3af' }}>
        Loading dataset analytics & insights...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: '800', color: '#f3f4f6', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <BarChart2 size={28} color="#a78bfa" /> Dataset Insights & Statistics
        </h1>
        <p style={{ color: '#9ca3af', fontSize: '1rem' }}>
          Verified metrics measured directly from movies.csv (9,742 rows) and ratings.csv (100,836 rows).
        </p>
      </div>

      <InsightsDashboard insights={insights} />
    </div>
  );
}
