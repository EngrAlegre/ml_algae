import React from 'react';
import './LogsTable.css';

function LogsTable({ logs }) {
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

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Recent Logs</h2>
        <small>Last {logs.length} entries</small>
      </div>
      <div className="table-container">
        <table className="logs-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>ML Result</th>
              <th>Confidence</th>
              <th>Distance (cm)</th>
              <th>Weight (kg)</th>
              <th>Motor</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="7" className="no-data">No logs available</td>
              </tr>
            ) : (
              logs.map((log) => {
                const mlResult = log.ml?.result || 'N/A';
                const isAlgae = mlResult.toLowerCase().includes('algae');
                
                return (
                  <tr key={log.id}>
                    <td>{formatTimestamp(log.timestamp)}</td>
                    <td className={isAlgae ? 'text-algae' : ''}>{mlResult}</td>
                    <td>{formatConfidence(log.ml?.confidence)}</td>
                    <td>{log.sensors?.distance_cm?.toFixed(1) || 'N/A'}</td>
                    <td>{log.sensors?.weight_kg?.toFixed(3) || 'N/A'}</td>
                    <td>{log.motor_state || 'N/A'}</td>
                    <td>{log.system_status || 'N/A'}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default LogsTable;

