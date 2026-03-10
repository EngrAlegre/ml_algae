import React from 'react';
import './StatsPanel.css';

function StatsPanel({ stats }) {
  const formatAccuracy = (value) => {
    if (value == null) {
      return 'N/A';
    }
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Statistics</h2>
        <small>
          {stats.labeledLogs > 0
            ? `${stats.labeledLogs} labeled logs support confusion-matrix metrics`
            : 'Add actual labels to unlock TP/TN/FP/FN metrics'}
        </small>
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
          <div className="stat-value">{stats.labeledLogs.toLocaleString()}</div>
          <div className="stat-label">Labeled Logs</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.unlabeledLogs.toLocaleString()}</div>
          <div className="stat-label">Unlabeled Logs</div>
        </div>
        <div className="stat-card">
          <div className="stat-value stat-algae">{stats.confusion.tp.toLocaleString()}</div>
          <div className="stat-label">True Positives</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.confusion.tn.toLocaleString()}</div>
          <div className="stat-label">True Negatives</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.confusion.fp.toLocaleString()}</div>
          <div className="stat-label">False Positives</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.confusion.fn.toLocaleString()}</div>
          <div className="stat-label">False Negatives</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatAccuracy(stats.overallAccuracy)}</div>
          <div className="stat-label">Overall Accuracy</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatAccuracy(stats.muddyMetrics.accuracy)}</div>
          <div className="stat-label">Muddy Accuracy</div>
          <div className="stat-subvalue">{stats.muddyMetrics.totalLabeled} labeled</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatAccuracy(stats.clearMetrics.accuracy)}</div>
          <div className="stat-label">Clear Accuracy</div>
          <div className="stat-subvalue">{stats.clearMetrics.totalLabeled} labeled</div>
        </div>
      </div>
    </div>
  );
}

export default StatsPanel;

