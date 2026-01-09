import React from 'react';
import './StatusPanel.css';

function StatusPanel({ status, connected }) {
  if (!status || !connected) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>Live Status</h2>
          <small>Robot disconnected</small>
        </div>
        <div className="status-grid">
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            color: 'var(--muted)'
          }}>
            <p style={{ fontSize: '1.2rem', marginBottom: '10px' }}>
              ⚠️ Robot is not connected
            </p>
            <p style={{ fontSize: '0.9rem' }}>
              {status ? 'Last data received was from a previous session.' : 'No data available.'}
            </p>
            <p style={{ fontSize: '0.85rem', marginTop: '20px', opacity: 0.7 }}>
              Waiting for robot to come online...
            </p>
          </div>
        </div>
      </div>
    );
  }

  const formatTimestamp = (ts) => {
    if (!ts) return 'N/A';
    try {
      if (ts.toDate) {
        return ts.toDate().toLocaleString();
      }
      return new Date(ts).toLocaleString();
    } catch {
      return String(ts);
    }
  };

  const formatConfidence = (conf) => {
    if (conf == null) return 'N/A';
    return `${(parseFloat(conf) * 100).toFixed(1)}%`;
  };

  const mlResult = status.ml?.result || 'N/A';
  const isAlgae = mlResult.toLowerCase().includes('algae');

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Live Status</h2>
        <small>
          <span style={{ color: 'var(--success)', marginRight: '6px' }}>●</span>
          Real-time data from robot
        </small>
      </div>
      <div className="status-grid">
        <div className="status-card">
          <h3>System</h3>
          <p><strong>Status:</strong> <span className={`badge badge-${status.system_status?.toLowerCase() || 'default'}`}>{status.system_status || 'N/A'}</span></p>
          <p><strong>Motor:</strong> <span className={`badge badge-${status.motor_state?.includes('stopped') ? 'stopped' : 'running'}`}>{status.motor_state || 'N/A'}</span></p>
          <p><strong>Timestamp:</strong> {formatTimestamp(status.timestamp)}</p>
        </div>

        <div className="status-card">
          <h3>ML Detection</h3>
          <p><strong>Result:</strong> <span className={`badge ${isAlgae ? 'badge-algae' : 'badge-default'}`}>{mlResult}</span></p>
          <p><strong>Confidence:</strong> {formatConfidence(status.ml?.confidence)}</p>
        </div>

        <div className="status-card">
          <h3>GPS</h3>
          <p><strong>Lat:</strong> {status.gps?.latitude?.toFixed(6) || 'N/A'}</p>
          <p><strong>Lon:</strong> {status.gps?.longitude?.toFixed(6) || 'N/A'}</p>
          <p><strong>Alt:</strong> {status.gps?.altitude?.toFixed(1) || 'N/A'} m</p>
        </div>

        <div className="status-card">
          <h3>Sensors</h3>
          <p><strong>Color:</strong> 
            <span 
              className="color-box"
              style={{
                backgroundColor: status.sensors?.color?.r != null 
                  ? `rgb(${status.sensors.color.r}, ${status.sensors.color.g || 0}, ${status.sensors.color.b || 0})`
                  : 'transparent'
              }}
            />
            {status.sensors?.color?.r != null 
              ? `${status.sensors.color.r}/${status.sensors.color.g}/${status.sensors.color.b}`
              : 'N/A'}
          </p>
          <p><strong>Distance:</strong> {status.sensors?.distance_cm?.toFixed(1) || 'N/A'} cm</p>
          <p><strong>Weight:</strong> {status.sensors?.weight_kg?.toFixed(3) || 'N/A'} kg</p>
          <p><strong>Water Level:</strong> <span className={`badge ${status.sensors?.water_level ? 'badge-success' : 'badge-warning'}`}>{status.sensors?.water_level ? 'Yes' : 'No'}</span></p>
        </div>
      </div>
    </div>
  );
}

export default StatusPanel;

