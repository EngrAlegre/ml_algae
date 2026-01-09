# AMLAC Robot Dashboard - React.js Frontend

React.js dashboard for real-time monitoring of the AMLAC robot using Firebase Firestore.

## Setup

### 1. Install Dependencies

```bash
cd web
npm install
```

### 2. Firebase Configuration

The Firebase configuration is already set up in `firebase-config.js`. Make sure your Firebase project has Firestore enabled.

### 3. Firestore Rules

Set up Firestore security rules in Firebase Console:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /telemetry/{document=**} {
      allow read: if true;  // Public read for dashboard
      allow write: if false;  // Only server can write
    }
    match /events/{document=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

### 4. Run Development Server

```bash
npm start
```

The app will open at `http://localhost:3000`

### 5. Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## Deployment

### Deploy to Firebase Hosting

1. Install Firebase CLI:
```bash
npm install -g firebase-tools
```

2. Login to Firebase:
```bash
firebase login
```

3. Initialize Firebase Hosting:
```bash
firebase init hosting
```

4. Build and deploy:
```bash
npm run build
firebase deploy --only hosting
```

## Features

- **Real-time Updates**: Uses Firebase Firestore real-time listeners
- **Live Status**: Shows current robot status, sensors, GPS, ML detection
- **Statistics**: Displays aggregated statistics from recent logs
- **Logs Table**: Shows recent telemetry entries
- **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
web/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Dashboard.js
│   │   ├── LogsTable.js
│   │   ├── StatusPanel.js
│   │   └── StatsPanel.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   └── index.css
├── firebase-config.js
├── package.json
└── README.md
```

