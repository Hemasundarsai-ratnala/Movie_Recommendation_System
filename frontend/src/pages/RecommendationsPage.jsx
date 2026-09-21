import React from 'react';
import RecommendationList from '../components/RecommendationList';
import { ArrowLeft } from 'lucide-react';

export default function RecommendationsPage({ 
  recommendations, 
  isLoading, 
  mode, 
  coldStart,
  diversityLambda,
  onDiversityChange,
  onBackToDiscover
}) {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      <button 
        className="btn-secondary" 
        onClick={onBackToDiscover} 
        style={{ marginBottom: '20px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
      >
        <ArrowLeft size={16} /> Back to Discover / Seed Builder
      </button>

      <RecommendationList
        recommendations={recommendations}
        isLoading={isLoading}
        mode={mode}
        coldStart={coldStart}
        diversityLambda={diversityLambda}
        onDiversityChange={onDiversityChange}
      />
    </div>
  );
}
