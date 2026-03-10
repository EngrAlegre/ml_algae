import React from 'react';
import './Dashboard.css';

function SensorGauge({ label, value, unit, min, max, warningThreshold, dangerThreshold, invert }) {
  const numValue = parseFloat(value) || 0;
  const percentage = Math.min(100, Math.max(0, ((numValue - min) / (max - min)) * 100));

  // Determine color based on thresholds
  let color = 'var(--accent)';
  if (warningThreshold !== undefined && dangerThreshold !== undefined) {
    if (invert) {
      // Lower is worse (e.g., distance - closer = more danger)
      if (numValue <= dangerThreshold) color = 'var(--error)';
      else if (numValue <= warningThreshold) color = 'var(--warning)';
      else color = 'var(--success)';
    } else {
      // Higher is worse
      if (numValue >= dangerThreshold) color = 'var(--error)';
      else if (numValue >= warningThreshold) color = 'var(--warning)';
      else color = 'var(--success)';
    }
  }

  return (
    <div className="gauge-card">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <span className="gauge-value" style={{ color }}>
          {value !== null && value !== undefined ? value : '--'}{unit && <span className="gauge-unit">{unit}</span>}
        </span>
      </div>
      <div className="gauge-bar-container">
        <div
          className="gauge-bar-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
      <div className="gauge-range">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

function Dashboard({ status, connected }) {
  const sensors = status?.sensors || {};
  const gps = status?.gps || {};
  const ml = status?.ml || {};
  const motorState = status?.motor_state || 'N/A';
  const systemStatus = status?.system_status || 'N/A';

  // Determine motor display
  const isMotorActive = motorState && motorState !== 'stopped' && motorState !== 'N/A' && motorState !== 'unavailable';

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>System Overview</h2>
        <small>{connected ? 'Live data' : 'Offline'}</small>
      </div>

      <div className="dashboard-content">
        {/* Sensor Gauges */}
        <div className="dashboard-section">
          <h3 className="section-title">Sensor Readings</h3>
          <div className="gauges-grid">
            <SensorGauge
              label="Distance"
              value={sensors.distance_cm != null ? parseFloat(sensors.distance_cm).toFixed(1) : null}
              unit=" cm"
              min={0}
              max={400}
              warningThreshold={30}
              dangerThreshold={15}
              invert={true}
            />
            <SensorGauge
              label="Weight"
              value={sensors.weight_kg != null ? parseFloat(sensors.weight_kg).toFixed(3) : null}
              unit=" kg"
              min={0}
              max={5}
              warningThreshold={4}
              dangerThreshold={4.5}
              invert={false}
            />
            <SensorGauge
              label="ML Confidence"
              value={ml.confidence != null ? (parseFloat(ml.confidence) * 100).toFixed(1) : null}
              unit="%"
              min={0}
              max={100}
            />
          </div>
        </div>

        {/* System Status Cards */}
        <div className="dashboard-section">
          <h3 className="section-title">System Status</h3>
          <div className="system-cards">
            {/* Motor Status */}
            <div className={`system-card ${isMotorActive ? 'card-active' : 'card-idle'}`}>
              <div className="system-card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
              </div>
              <div className="system-card-info">
                <span className="system-card-label">Motor</span>
                <span className={`system-card-value ${isMotorActive ? 'value-active' : 'value-idle'}`}>
                  {motorState || 'N/A'}
                </span>
              </div>
            </div>

            {/* System Status */}
            <div className={`system-card ${systemStatus === 'running' ? 'card-active' : 'card-idle'}`}>
              <div className="system-card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </div>
              <div className="system-card-info">
                <span className="system-card-label">System</span>
                <span className={`system-card-value ${systemStatus === 'running' ? 'value-active' : 'value-idle'}`}>
                  {systemStatus || 'N/A'}
                </span>
              </div>
            </div>

            {/* Water Level */}
            <div className={`system-card ${sensors.water_level ? 'card-active' : 'card-warning'}`}>
              <div className="system-card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                </svg>
              </div>
              <div className="system-card-info">
                <span className="system-card-label">Water Level</span>
                <span className={`system-card-value ${sensors.water_level ? 'value-active' : 'value-warning'}`}>
                  {sensors.water_level !== undefined ? (sensors.water_level ? 'Detected' : 'No Water') : 'N/A'}
                </span>
              </div>
            </div>

            {/* GPS Status */}
            <div className={`system-card ${gps.latitude ? 'card-active' : 'card-idle'}`}>
              <div className="system-card-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
              </div>
              <div className="system-card-info">
                <span className="system-card-label">GPS</span>
                <span className={`system-card-value ${gps.latitude ? 'value-active' : 'value-idle'}`}>
                  {gps.latitude
                    ? `${gps.latitude.toFixed(4)}, ${gps.longitude.toFixed(4)}`
                    : 'No Fix'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Color Sensor */}
        {sensors.color && sensors.color.r != null && (
          <div className="dashboard-section">
            <h3 className="section-title">Color Sensor</h3>
            <div className="color-display">
              <div
                className="color-preview"
                style={{
                  backgroundColor: `rgb(${sensors.color.r}, ${sensors.color.g || 0}, ${sensors.color.b || 0})`
                }}
              />
              <div className="color-values">
                <div className="color-channel">
                  <span className="channel-label" style={{ color: '#ef4444' }}>R</span>
                  <div className="channel-bar">
                    <div className="channel-fill" style={{ width: `${(sensors.color.r / 255) * 100}%`, background: '#ef4444' }} />
                  </div>
                  <span className="channel-value">{sensors.color.r}</span>
                </div>
                <div className="color-channel">
                  <span className="channel-label" style={{ color: '#22c55e' }}>G</span>
                  <div className="channel-bar">
                    <div className="channel-fill" style={{ width: `${((sensors.color.g || 0) / 255) * 100}%`, background: '#22c55e' }} />
                  </div>
                  <span className="channel-value">{sensors.color.g || 0}</span>
                </div>
                <div className="color-channel">
                  <span className="channel-label" style={{ color: '#3b82f6' }}>B</span>
                  <div className="channel-bar">
                    <div className="channel-fill" style={{ width: `${((sensors.color.b || 0) / 255) * 100}%`, background: '#3b82f6' }} />
                  </div>
                  <span className="channel-value">{sensors.color.b || 0}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
