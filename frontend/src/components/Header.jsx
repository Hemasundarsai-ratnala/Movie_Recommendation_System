import React from 'react';
import { Film, Sparkles, Compass, BarChart2, Activity } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, isEngineLoaded }) {
  return (
    <header style={{
      background: 'rgba(10, 13, 20, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '14px 24px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {/* Logo */}
        <div 
          onClick={() => setActiveTab('home')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div style={{
            background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            padding: '10px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)'
          }}>
            <Film size={22} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: '700', lineHeight: 1.2 }}>
              CineMatch <span className="gradient-text">Hybrid</span>
            </h1>
            <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>TF-IDF · CF · RapidFuzz</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {[
            { id: 'home', label: 'Home', icon: Sparkles },
            { id: 'discover', label: 'Discover & Personalize', icon: Compass },
            { id: 'recommendations', label: 'Recommendations', icon: Film },
            { id: 'insights', label: 'Dataset Insights', icon: BarChart2 },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                  color: isActive ? '#a78bfa' : '#9ca3af',
                  fontWeight: isActive ? '600' : '400',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Engine Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
          <Activity size={14} color={isEngineLoaded ? '#34d399' : '#fbbf24'} />
          <span style={{ color: isEngineLoaded ? '#34d399' : '#fbbf24', fontWeight: '500' }}>
            {isEngineLoaded ? 'Engine Online' : 'Initializing...'}
          </span>
        </div>
      </div>
    </header>
  );
}
