import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from 'recharts';
import './DetectionChart.css';

function DetectionChart({ logs }) {
  // Process logs into chart data
  const chartData = useMemo(() => {
    if (!logs || logs.length === 0) return [];

    // Take last 20 logs and reverse to chronological order
    const recentLogs = [...logs].slice(0, 20).reverse();

    return recentLogs.map((log, index) => {
      const confidence = log.ml?.confidence
        ? parseFloat(log.ml.confidence) * 100
        : 0;
      const isAlgae = log.ml?.result?.toLowerCase() === 'algae';
      
      // Format timestamp for x-axis
      let timeLabel = '';
      try {
        const ts = log.timestamp;
        if (ts?.toDate) {
          timeLabel = ts.toDate().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (typeof ts?.seconds === 'number') {
          timeLabel = new Date(ts.seconds * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
      } catch {
        timeLabel = `#${index + 1}`;
      }

      return {
        time: timeLabel,
        confidence: confidence.toFixed(1),
        isAlgae,
        distance: log.sensors?.distance_cm ? parseFloat(log.sensors.distance_cm).toFixed(1) : null,
        weight: log.sensors?.weight_kg ? parseFloat(log.sensors.weight_kg).toFixed(3) : null,
      };
    });
  }, [logs]);

  // Calculate detection summary
  const summary = useMemo(() => {
    if (!logs || logs.length === 0) return { algae: 0, noAlgae: 0, total: 0 };
    const total = Math.min(logs.length, 20);
    const algae = logs.slice(0, 20).filter(l => l.ml?.result?.toLowerCase() === 'algae').length;
    return { algae, noAlgae: total - algae, total };
  }, [logs]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="chart-tooltip">
          <p className="tooltip-time">{label}</p>
          <p className="tooltip-result">
            <span className={data.isAlgae ? 'text-algae' : 'text-muted'}>
              {data.isAlgae ? 'Algae' : 'No Algae'}
            </span>
          </p>
          <p className="tooltip-confidence">
            Confidence: <strong>{data.confidence}%</strong>
          </p>
          {data.distance && (
            <p className="tooltip-detail">Distance: {data.distance} cm</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Detection History</h2>
        <small>Last {summary.total} readings</small>
      </div>

      <div className="chart-content">
        {/* Detection summary bar */}
        <div className="detection-summary">
          <div className="summary-item">
            <div className="summary-dot algae-dot" />
            <span className="summary-label">Algae</span>
            <span className="summary-count">{summary.algae}</span>
          </div>
          <div className="summary-item">
            <div className="summary-dot no-algae-dot" />
            <span className="summary-label">No Algae</span>
            <span className="summary-count">{summary.noAlgae}</span>
          </div>
          <div className="summary-bar">
            <div
              className="summary-bar-fill"
              style={{
                width: summary.total > 0
                  ? `${(summary.algae / summary.total) * 100}%`
                  : '0%'
              }}
            />
          </div>
        </div>

        {/* Confidence chart */}
        {chartData.length > 0 ? (
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'var(--muted)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--border)' }}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fill: 'var(--muted)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--border)' }}
                  tickLine={false}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="confidence" radius={[4, 4, 0, 0]} maxBarSize={24}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.isAlgae ? 'var(--algae)' : 'var(--accent)'}
                      fillOpacity={0.8}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Distance line chart */}
            <div className="chart-section-label">Distance (cm)</div>
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: 'var(--muted)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--border)' }}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fill: 'var(--muted)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--border)' }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: '#1e293b',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    color: 'var(--text)',
                    fontSize: '0.85rem',
                  }}
                  formatter={(value) => [`${value} cm`, 'Distance']}
                />
                <Area
                  type="monotone"
                  dataKey="distance"
                  stroke="var(--accent)"
                  fill="var(--accent)"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="chart-empty">
            <p>No detection data available</p>
            <p className="chart-empty-hint">Charts will appear when the robot starts collecting data</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DetectionChart;
