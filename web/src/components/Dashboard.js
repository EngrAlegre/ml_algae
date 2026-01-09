import React from 'react';
import './Dashboard.css';

function Dashboard({ status }) {
  // This can be expanded with charts, maps, etc.
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Dashboard</h2>
        <small>Overview and controls</small>
      </div>
      <div className="dashboard-content">
        <p>Dashboard content - Add charts, maps, or controls here</p>
      </div>
    </div>
  );
}

export default Dashboard;

