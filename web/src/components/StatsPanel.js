import React from 'react';
import './StatsPanel.css';

function StatsPanel({ stats }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Statistics</h2>
        <small>Based on recent data</small>
      </div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.totalLogs.toLocaleString()}</div>
          <div className="stat-label">Total Logs</div>
        </div>
        <div className="stat-card">
          <div className="stat-value stat-algae">{stats.algaeDetections.toLocaleString()}</div>
          <div className="stat-label">Algae Detections</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.maxWeight}</div>
          <div className="stat-label">Max Weight (kg)</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.collectionEvents.toLocaleString()}</div>
          <div className="stat-label">Collection Events</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.successRate}%</div>
          <div className="stat-label">Success Rate</div>
        </div>
      </div>
    </div>
  );
}

export default StatsPanel;

