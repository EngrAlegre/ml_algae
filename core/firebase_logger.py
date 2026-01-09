"""
Firebase Logger Module for AMLAC Robot
Handles real-time data logging to Firebase Firestore
"""

import os
from datetime import datetime
from typing import Dict, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Warning: Firebase Admin SDK not available. Install with: pip install firebase-admin")

from config import DEBUG_MODE


class FirebaseLogger:
    """
    Logs robot telemetry data to Firebase Firestore
    Provides real-time data access for React frontend
    """
    
    def __init__(self, firebase_config: Optional[Dict] = None):
        """
        Initialize Firebase logger
        
        Args:
            firebase_config: Optional Firebase config dict (for service account)
        """
        self.initialized = False
        self.db = None
        
        if not FIREBASE_AVAILABLE:
            print("Warning: Firebase not available. Install firebase-admin package.")
            return
        
        try:
            # Initialize Firebase Admin SDK
            if firebase_config:
                # Use service account credentials
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
            else:
                # Try to use default credentials or environment variable
                if os.path.exists('serviceAccountKey.json'):
                    cred = credentials.Certificate('serviceAccountKey.json')
                    firebase_admin.initialize_app(cred)
                else:
                    # Use application default credentials (for deployed environments)
                    firebase_admin.initialize_app()
            
            # Get Firestore client
            self.db = firestore.client()
            self.initialized = True
            
            if DEBUG_MODE:
                print("Firebase logger initialized successfully")
                
        except Exception as e:
            print(f"Error initializing Firebase logger: {e}")
            self.initialized = False
    
    def log(self, data: Dict) -> bool:
        """
        Log a data entry to Firestore
        
        Args:
            data: Dictionary with telemetry data
                Required keys:
                - timestamp (or will be added)
                - gps_latitude, gps_longitude, gps_altitude
                - color_r, color_g, color_b
                - distance_cm, weight_kg, water_level
                - ml_result, ml_confidence
                - motor_state, system_status
        
        Returns:
            bool: True if logged successfully, False otherwise
        """
        if not self.initialized or not self.db:
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Convert timestamp to Firestore timestamp
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            
            # Prepare document data
            doc_data = {
                'timestamp': firestore.SERVER_TIMESTAMP if not data.get('timestamp') else timestamp,
                'gps': {
                    'latitude': float(data.get('gps_latitude', 0)) if data.get('gps_latitude') else None,
                    'longitude': float(data.get('gps_longitude', 0)) if data.get('gps_longitude') else None,
                    'altitude': float(data.get('gps_altitude', 0)) if data.get('gps_altitude') else None,
                },
                'sensors': {
                    'color': {
                        'r': int(data.get('color_r', 0)) if data.get('color_r') else None,
                        'g': int(data.get('color_g', 0)) if data.get('color_g') else None,
                        'b': int(data.get('color_b', 0)) if data.get('color_b') else None,
                    },
                    'distance_cm': float(data.get('distance_cm', 0)) if data.get('distance_cm') else None,
                    'weight_kg': float(data.get('weight_kg', 0)) if data.get('weight_kg') else None,
                    'water_level': bool(data.get('water_level')) if data.get('water_level') else None,
                },
                'ml': {
                    'result': data.get('ml_result', ''),
                    'confidence': float(data.get('ml_confidence', 0)) if data.get('ml_confidence') else 0.0,
                },
                'motor_state': data.get('motor_state', ''),
                'system_status': data.get('system_status', ''),
            }
            
            # Remove None values
            doc_data = self._remove_none_values(doc_data)
            
            # Add to Firestore collection
            collection_ref = self.db.collection('telemetry')
            collection_ref.add(doc_data)
            
            if DEBUG_MODE:
                print(f"Logged to Firebase: {data.get('timestamp', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"Error logging to Firebase: {e}")
            return False
    
    def _remove_none_values(self, d: Dict) -> Dict:
        """Recursively remove None values from dictionary"""
        if isinstance(d, dict):
            return {k: self._remove_none_values(v) for k, v in d.items() if v is not None}
        return d
    
    def log_event(self, event_type: str, description: str, additional_data: Optional[Dict] = None) -> bool:
        """
        Log an event to Firestore
        
        Args:
            event_type: Type of event (info, warning, error)
            description: Event description
            additional_data: Optional additional data
        
        Returns:
            bool: True if logged successfully
        """
        if not self.initialized or not self.db:
            return False
        
        try:
            event_data = {
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': event_type,
                'description': description,
                'additional_data': additional_data or {},
            }
            
            self.db.collection('events').add(event_data)
            
            if DEBUG_MODE:
                print(f"Logged event to Firebase: {event_type} - {description}")
            
            return True
            
        except Exception as e:
            print(f"Error logging event to Firebase: {e}")
            return False
    
    def get_latest_status(self) -> Optional[Dict]:
        """
        Get the latest status from Firestore
        
        Returns:
            Dict with latest telemetry data or None
        """
        if not self.initialized or not self.db:
            return None
        
        try:
            collection_ref = self.db.collection('telemetry')
            docs = collection_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            print(f"Error getting latest status from Firebase: {e}")
            return None
    
    def cleanup(self):
        """Clean up Firebase resources"""
        try:
            # Firebase Admin SDK doesn't require explicit cleanup
            if DEBUG_MODE:
                print("Firebase logger cleanup complete")
        except Exception as e:
            print(f"Error during Firebase cleanup: {e}")


# Test function
if __name__ == "__main__":
    print("Testing Firebase Logger...\n")
    
    # Initialize logger (will use default credentials or service account)
    logger = FirebaseLogger()
    
    if logger.initialized:
        print("Firebase logger initialized successfully\n")
        
        # Log test data
        print("Logging test entry...")
        test_data = {
            'gps_latitude': 14.5995,
            'gps_longitude': 120.9842,
            'gps_altitude': 10.0,
            'color_r': 80,
            'color_g': 150,
            'color_b': 70,
            'distance_cm': 150.0,
            'weight_kg': 2.5,
            'water_level': True,
            'ml_result': 'Algae',
            'ml_confidence': 0.85,
            'motor_state': 'forward_speed_128',
            'system_status': 'running'
        }
        
        if logger.log(test_data):
            print("  Test entry logged successfully")
        
        # Log test event
        print("\nLogging test event...")
        logger.log_event('info', 'Test event', {'test': True})
        
        # Get latest status
        print("\nGetting latest status...")
        latest = logger.get_latest_status()
        if latest:
            print(f"  Latest timestamp: {latest.get('timestamp')}")
        
        print("\nTest complete!")
    else:
        print("Failed to initialize Firebase logger")
        print("Make sure you have:")
        print("  1. Installed firebase-admin: pip install firebase-admin")
        print("  2. Set up service account key or application default credentials")
    
    logger.cleanup()

