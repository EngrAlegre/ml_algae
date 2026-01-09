import React, { useState, useEffect, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, query, orderBy, limit, onSnapshot } from 'firebase/firestore';
import firebaseConfig from './firebase-config';
import './App.css';
import Dashboard from './components/Dashboard';
import StatusPanel from './components/StatusPanel';
import StatsPanel from './components/StatsPanel';
import LogsTable from './components/LogsTable';

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Connection timeout threshold (in seconds)
// If no data received within this time, consider robot disconnected
const CONNECTION_TIMEOUT_SECONDS = 30;

// Helper function to convert Firestore timestamp to Date (outside component)
function getDateFromTimestamp(ts) {
  if (!ts) return null;
  // Firestore Timestamp object
  if (ts && typeof ts.toDate === 'function') return ts.toDate();
  // Firestore Timestamp with seconds/nanoseconds
  if (ts && typeof ts.seconds === 'number') return new Date(ts.seconds * 1000);
  // Already a Date
  if (ts instanceof Date) return ts;
  // ISO string
  if (typeof ts === 'string') {
    const date = new Date(ts);
    return isNaN(date.getTime()) ? null : date;
  }
  // Unix timestamp (milliseconds)
  if (typeof ts === 'number') return new Date(ts);
  return null;
}

// Helper to format "time ago" text
function formatTimeAgo(secondsAgo) {
  // Handle negative values (clock skew - data appears to be from future)
  if (secondsAgo < 0) {
    const absSeconds = Math.abs(secondsAgo);
    if (absSeconds < 60) return 'Just now (clock skew)';
    if (absSeconds < 3600) {
      const minutes = Math.floor(absSeconds / 60);
      return `Clock skew: ${minutes}m ahead`;
    }
    const hours = Math.floor(absSeconds / 3600);
    return `Clock skew: ${hours}h ahead`;
  }
  
  if (secondsAgo < 5) return 'Just now';
  if (secondsAgo < 60) return `${secondsAgo} seconds ago`;
  if (secondsAgo < 3600) {
    const minutes = Math.floor(secondsAgo / 60);
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  }
  if (secondsAgo < 86400) {
    const hours = Math.floor(secondsAgo / 3600);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  }
  const days = Math.floor(secondsAgo / 86400);
  return `${days} day${days > 1 ? 's' : ''} ago`;
}

function App() {
  const [latestStatus, setLatestStatus] = useState(null);
  const [recentLogs, setRecentLogs] = useState([]);
  const [stats, setStats] = useState({
    totalLogs: 0,
    algaeDetections: 0,
    maxWeight: 0,
    collectionEvents: 0,
    successRate: 0
  });
  const [connected, setConnected] = useState(false);
  const [lastSeenText, setLastSeenText] = useState('Never');
  
  // Track when we LAST RECEIVED data (browser time, not robot timestamp)
  // This is immune to clock skew between robot and user's computer
  const lastReceivedTimeRef = useRef(null);
  
  // Also store the robot's timestamp for display purposes
  const robotTimestampRef = useRef(null);

  // Set up periodic connection check (every 2 seconds for faster updates)
  useEffect(() => {
    const checkConnection = () => {
      const lastReceivedTime = lastReceivedTimeRef.current;
      
      if (!lastReceivedTime) {
        setConnected(false);
        setLastSeenText('Never');
        return;
      }

      const now = Date.now();
      const secondsSinceReceived = Math.floor((now - lastReceivedTime) / 1000);
      
      // Update connection status based on when we LAST RECEIVED data
      setConnected(secondsSinceReceived <= CONNECTION_TIMEOUT_SECONDS);
      setLastSeenText(formatTimeAgo(secondsSinceReceived));
    };

    // Run immediately, then every 2 seconds
    checkConnection();
    const interval = setInterval(checkConnection, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Subscribe to latest telemetry
    const telemetryRef = collection(db, 'telemetry');
    const q = query(telemetryRef, orderBy('timestamp', 'desc'), limit(1));
    
    // Track the last document ID to detect new data vs same data
    let lastDocId = null;
    let isFirstLoad = true;
    
    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        if (!snapshot.empty) {
          const doc = snapshot.docs[0];
          const data = doc.data();
          const docId = doc.id;
          
          setLatestStatus({ id: docId, ...data });
          
          // Store robot's timestamp for reference
          const robotTime = getDateFromTimestamp(data.timestamp);
          robotTimestampRef.current = robotTime;
          
          if (isFirstLoad) {
            // On first load, check if data is reasonably recent using robot timestamp
            // Use a larger window (5 minutes) to account for clock skew
            isFirstLoad = false;
            lastDocId = docId;
            
            if (robotTime) {
              const robotSecondsAgo = Math.floor((Date.now() - robotTime.getTime()) / 1000);
              const absRobotSecondsAgo = Math.abs(robotSecondsAgo); // Handle clock skew
              
              // If data is within 5 minutes (either direction for clock skew), consider it recent
              if (absRobotSecondsAgo <= 300) {
                lastReceivedTimeRef.current = Date.now();
                setConnected(true);
                setLastSeenText('Just now');
              } else {
                // Set lastReceivedTime to when the robot last sent data (approximation)
                lastReceivedTimeRef.current = Date.now() - (absRobotSecondsAgo * 1000);
              }
            }
          } else if (docId !== lastDocId) {
            // After first load, track document ID changes = NEW data
            lastDocId = docId;
            lastReceivedTimeRef.current = Date.now();
            setConnected(true);
            setLastSeenText('Just now');
          }
        } else {
          setConnected(false);
          setLastSeenText('No data');
        }
      },
      (error) => {
        console.error('Error listening to telemetry:', error);
        setConnected(false);
      }
    );

    // Subscribe to recent logs (last 100)
    const logsQuery = query(telemetryRef, orderBy('timestamp', 'desc'), limit(100));
    
    const unsubscribeLogs = onSnapshot(
      logsQuery,
      (snapshot) => {
        const logs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        setRecentLogs(logs);
        
        // Calculate stats
        const total = logs.length;
        const algaeCount = logs.filter(log => 
          log.ml?.result?.toLowerCase() === 'algae'
        ).length;
        const weights = logs
          .map(log => log.sensors?.weight_kg)
          .filter(w => w != null)
          .map(w => parseFloat(w));
        const maxWeight = weights.length > 0 ? Math.max(...weights) : 0;
        
        // Count collection events (state changes from forward to stopped)
        let collectionEvents = 0;
        for (let i = 1; i < logs.length; i++) {
          const prev = logs[i].motor_state;
          const curr = logs[i - 1].motor_state;
          if (prev && prev.includes('forward') && curr === 'stopped') {
            collectionEvents++;
          }
        }
        
        setStats({
          totalLogs: total,
          algaeDetections: algaeCount,
          maxWeight: maxWeight.toFixed(3),
          collectionEvents,
          successRate: total > 0 ? ((algaeCount / total) * 100).toFixed(1) : 0
        });
      },
      (error) => {
        console.error('Error listening to logs:', error);
      }
    );

    return () => {
      unsubscribe();
      unsubscribeLogs();
    };
  }, []); // Run once on mount

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>AMLAC Robot Dashboard</h1>
          <div className="header-info">
            <div className="connection-status">
              <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
                {connected ? '●' : '○'}
              </span>
              <span className="status-text">{connected ? 'Connected' : 'Disconnected'}</span>
            </div>
            <span className="last-seen">Last seen: {lastSeenText}</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <StatusPanel status={connected ? latestStatus : null} connected={connected} />
        <StatsPanel stats={stats} />
        <Dashboard status={connected ? latestStatus : null} />
        <LogsTable logs={recentLogs.slice(0, 20)} />
      </main>

      <footer className="app-footer">
        <p>AMLAC Robot - Automated Machine Learning Algae Collector</p>
      </footer>
    </div>
  );
}

export default App;

