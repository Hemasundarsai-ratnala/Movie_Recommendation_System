import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import DiscoverPage from './pages/DiscoverPage';
import RecommendationsPage from './pages/RecommendationsPage';
import InsightsPage from './pages/InsightsPage';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [isEngineLoaded, setIsEngineLoaded] = useState(false);
  
  const [recommendations, setRecommendations] = useState([]);
  const [recMode, setRecMode] = useState('');
  const [isColdStart, setIsColdStart] = useState(false);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  
  const [insights, setInsights] = useState(null);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);

  // Active hybrid query state for re-filtering diversity
  const [lastQuery, setLastQuery] = useState(null);
  const [diversityLambda, setDiversityLambda] = useState(0.7);

  // Persistent user seed profile & preference state
  const [seeds, setSeeds] = useState([
    { movieId: 2571, title: 'Matrix, The (1999)', genres: 'Action|Sci-Fi|Thriller', rating: 5.0 },
    { movieId: 58559, title: 'Dark Knight, The (2008)', genres: 'Action|Crime|Drama|IMAX', rating: 4.5 },
  ]);
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [weights, setWeights] = useState({
    content: 0.45,
    collab: 0.45,
    pop: 0.10,
    diversityLambda: 0.7,
  });

  // Check health and load insights at startup
  useEffect(() => {
    async function init() {
      try {
        const health = await api.getHealth();
        setIsEngineLoaded(health.model_artifacts_loaded);
        
        setIsLoadingInsights(true);
        const data = await api.getInsights();
        setInsights(data);
      } catch (err) {
        console.error('Initialization check error:', err);
      } finally {
        setIsLoadingInsights(false);
      }
    }
    init();
  }, []);

  const handleSelectSingleMovie = async (movie) => {
    if (!movie || !movie.movieId) return;
    setIsLoadingRecs(true);
    setActiveTab('recommendations');
    
    try {
      const res = await api.recommendSingle(movie.movieId, 5.0, 10, { diversityLambda });
      setRecommendations(res.recommendations);
      setRecMode(res.mode);
      setIsColdStart(res.cold_start);
      setLastQuery({ type: 'single', movieId: movie.movieId, rating: 5.0 });
    } catch (err) {
      console.error('Single recommendation error:', err);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  const handleGenerateHybrid = async (seeds, statedGenres, weights) => {
    setIsLoadingRecs(true);
    setActiveTab('recommendations');
    
    try {
      const res = await api.recommendPersonalized(seeds, statedGenres, 12, {
        ...weights,
        diversityLambda,
      });
      setRecommendations(res.recommendations);
      setRecMode(res.mode);
      setIsColdStart(res.cold_start);
      setLastQuery({ type: 'hybrid', seeds, statedGenres, weights });
    } catch (err) {
      console.error('Hybrid recommendation error:', err);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  const handleDiversityChange = async (newLambda) => {
    setDiversityLambda(newLambda);
    if (!lastQuery) return;
    
    setIsLoadingRecs(true);
    try {
      if (lastQuery.type === 'single') {
        const res = await api.recommendSingle(lastQuery.movieId, lastQuery.rating, 10, { diversityLambda: newLambda });
        setRecommendations(res.recommendations);
      } else if (lastQuery.type === 'hybrid') {
        const res = await api.recommendPersonalized(lastQuery.seeds, lastQuery.statedGenres, 12, {
          ...lastQuery.weights,
          diversityLambda: newLambda,
        });
        setRecommendations(res.recommendations);
      }
    } catch (err) {
      console.error('Diversity update error:', err);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isEngineLoaded={isEngineLoaded} 
      />

      <main style={{ flex: 1, padding: '30px 24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'home' && (
          <HomePage 
            onSelectSingleMovie={handleSelectSingleMovie}
            onNavigateDiscover={() => setActiveTab('discover')}
          />
        )}

        {activeTab === 'discover' && (
          <DiscoverPage 
            onGenerateHybrid={handleGenerateHybrid}
            seeds={seeds}
            setSeeds={setSeeds}
            selectedGenres={selectedGenres}
            setSelectedGenres={setSelectedGenres}
            weights={weights}
            setWeights={setWeights}
          />
        )}

        {activeTab === 'recommendations' && (
          <RecommendationsPage 
            recommendations={recommendations}
            isLoading={isLoadingRecs}
            mode={recMode}
            coldStart={isColdStart}
            diversityLambda={diversityLambda}
            onDiversityChange={handleDiversityChange}
            onBackToDiscover={() => setActiveTab('discover')}
          />
        )}

        {activeTab === 'insights' && (
          <InsightsPage 
            insights={insights}
            isLoading={isLoadingInsights}
          />
        )}
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '20px',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        color: '#6b7280',
        fontSize: '0.85rem'
      }}>
        Hybrid Movie Recommendation System · MovieLens Dataset (9,742 movies, 100,836 ratings)
      </footer>
    </div>
  );
}
