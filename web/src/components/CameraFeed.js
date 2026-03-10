import React from 'react';
import './CameraFeed.css';

function CameraFeed({ cameraData, connected }) {
  const formatTimestamp = (ts) => {
    if (!ts) return 'N/A';
    try {
      if (ts.toDate) return ts.toDate().toLocaleTimeString();
      if (typeof ts.seconds === 'number') return new Date(ts.seconds * 1000).toLocaleTimeString();
      return new Date(ts).toLocaleTimeString();
    } catch {
      return 'N/A';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'var(--success)';
    if (confidence >= 0.5) return 'var(--warning)';
    return 'var(--error)';
  };

  const hasImage = cameraData && cameraData.image;
  const mlResult = cameraData?.ml;

  return (
    <div className="panel camera-panel">
      <div className="panel-header">
        <h2>Camera Feed</h2>
        <small>
          {connected ? (
            <>
              <span style={{ color: 'var(--success)', marginRight: '6px' }}>●</span>
              Live
            </>
          ) : (
            'Offline'
          )}
        </small>
      </div>

      <div className="camera-content">
        <div className="camera-viewport">
          {hasImage ? (
            <img
              src={`data:image/jpeg;base64,${cameraData.image}`}
              alt="Robot Camera Feed"
              className="camera-image"
            />
          ) : (
            <div className="camera-placeholder">
              <div className="camera-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
              </div>
              <p>No camera feed available</p>
              <p className="camera-hint">
                {connected
                  ? 'Waiting for camera frame...'
                  : 'Robot is offline'}
              </p>
            </div>
          )}

          {/* ML Detection overlay */}
          {hasImage && mlResult && (
            <div className={`camera-overlay ${mlResult.is_algae ? 'algae-detected' : ''}`}>
              <div className="detection-badge">
                <span className="detection-label">{mlResult.result || 'Unknown'}</span>
                <span
                  className="detection-confidence"
                  style={{ color: getConfidenceColor(mlResult.confidence) }}
                >
                  {(mlResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Camera info bar */}
        <div className="camera-info-bar">
          <div className="camera-info-item">
            <span className="camera-info-label">Resolution</span>
            <span className="camera-info-value">
              {hasImage ? `${cameraData.width || 320}x${cameraData.height || 240}` : '--'}
            </span>
          </div>
          <div className="camera-info-item">
            <span className="camera-info-label">Last Frame</span>
            <span className="camera-info-value">
              {hasImage ? formatTimestamp(cameraData.timestamp) : '--'}
            </span>
          </div>
          <div className="camera-info-item">
            <span className="camera-info-label">Detection</span>
            <span className={`camera-info-value ${mlResult?.is_algae ? 'text-algae' : ''}`}>
              {mlResult ? mlResult.result : '--'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CameraFeed;
