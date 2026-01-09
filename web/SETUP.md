# AMLAC Robot Dashboard - Setup Guide

## Quick Start

### 1. Install Node.js Dependencies

```bash
cd web
npm install
```

### 2. Firebase Setup

The Firebase configuration is already in `firebase-config.js`. Make sure:

1. **Firestore is enabled** in your Firebase project
2. **Firestore rules** are set (see `firestore.rules`)
3. **Service Account Key** is set up for the Python backend

### 3. Run Development Server

```bash
npm start
```

Opens at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

### 5. Deploy to Firebase Hosting

```bash
# Install Firebase CLI (if not installed)
npm install -g firebase-tools

# Login
firebase login

# Deploy
firebase deploy --only hosting
```

## Backend Setup (Python)

### Install Firebase Admin SDK

```bash
pip install firebase-admin
```

### Set Up Service Account

1. Go to Firebase Console → Project Settings → Service Accounts
2. Generate new private key
3. Save as `serviceAccountKey.json` in the `robot_system/` directory
4. **IMPORTANT**: Add `serviceAccountKey.json` to `.gitignore` (never commit this file!)

### Alternative: Use Application Default Credentials

For deployed environments, you can use:
```bash
gcloud auth application-default login
```

## Features

- ✅ Real-time data updates via Firestore listeners
- ✅ Live status monitoring
- ✅ Statistics dashboard
- ✅ Recent logs table
- ✅ Responsive design
- ✅ Connection status indicator

## Project Structure

```
web/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/         # React components
│   │   ├── Dashboard.js
│   │   ├── LogsTable.js
│   │   ├── StatusPanel.js
│   │   └── StatsPanel.js
│   ├── App.js              # Main app component
│   ├── App.css
│   ├── index.js            # Entry point
│   └── index.css
├── firebase-config.js      # Firebase configuration
├── firebase.json           # Firebase hosting config
├── firestore.rules         # Firestore security rules
├── package.json
└── README.md
```

## Troubleshooting

### "Firebase not initialized"
- Check `firebase-config.js` has correct config
- Verify Firestore is enabled in Firebase Console

### "Permission denied" errors
- Check Firestore security rules
- Make sure rules allow public read access

### Build fails
- Run `npm install` again
- Check Node.js version (requires Node 14+)

