"""
Data Logger Module for AMLAC Robot
Handles CSV logging of telemetry data
"""

import os
import csv
import time
from datetime import datetime, timedelta

from config import (
    LOGS_DIR,
    CSV_HEADERS,
    LOG_FLUSH_INTERVAL,
    LOG_FLUSH_ROWS,
    LOG_RETENTION_DAYS,
    DEBUG_MODE
)


class DataLogger:
    """
    Logs robot telemetry data to CSV files
    Creates daily log files with automatic rotation
    """
    
    def __init__(self):
        """Initialize data logger"""
        self.initialized = False
        self.csv_file = None
        self.csv_writer = None
        self.current_date = None
        self.row_count = 0
        self.last_flush_time = time.time()
        
        # Ensure logs directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Create or open today's log file
        if self._create_log_file():
            self.initialized = True
            if DEBUG_MODE:
                print(f"Data logger initialized: {self.csv_file.name}")
        else:
            print("Error: Could not initialize data logger")
    
    def _create_log_file(self):
        """Create or open CSV log file for today"""
        try:
            # Get current date
            today = datetime.now().date()
            
            # Check if we need a new file (date changed)
            if self.current_date != today:
                # Close existing file if open
                if self.csv_file:
                    self.csv_file.close()
                
                # Create new filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f"amlac_log_{timestamp}.csv"
                filepath = os.path.join(LOGS_DIR, filename)
                
                # Check if file exists
                file_exists = os.path.exists(filepath)
                
                # Open file in append mode
                self.csv_file = open(filepath, 'a', newline='')
                self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=CSV_HEADERS)
                
                # Write header if new file
                if not file_exists:
                    self.csv_writer.writeheader()
                    self.csv_file.flush()
                
                self.current_date = today
                self.row_count = 0
                
                if DEBUG_MODE:
                    print(f"Created/opened log file: {filepath}")
                
                # Clean up old log files
                self._cleanup_old_logs()
            
            return True
            
        except Exception as e:
            print(f"Error creating log file: {e}")
            return False
    
    def _cleanup_old_logs(self):
        """Delete log files older than LOG_RETENTION_DAYS"""
        try:
            cutoff_date = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
            
            for filename in os.listdir(LOGS_DIR):
                if filename.startswith('amlac_log_') and filename.endswith('.csv'):
                    filepath = os.path.join(LOGS_DIR, filename)
                    
                    # Get file modification time
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    # Delete if older than cutoff
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        if DEBUG_MODE:
                            print(f"Deleted old log file: {filename}")
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error cleaning up old logs: {e}")
    
    def log(self, data):
        """
        Log a data entry to CSV
        
        Args:
            data: Dictionary with keys matching CSV_HEADERS
                Required keys:
                - gps_latitude, gps_longitude, gps_altitude
                - color_r, color_g, color_b
                - distance_cm
                - weight_kg
                - water_level
                - ml_result, ml_confidence
                - motor_state
                - system_status
        
        Returns:
            bool: True if logged successfully, False otherwise
        """
        if not self.initialized:
            return False
        
        try:
            # Check if we need a new file (date changed)
            self._create_log_file()
            
            # Add timestamp
            data['timestamp'] = datetime.now().isoformat()
            
            # Ensure all required fields are present
            row_data = {}
            for header in CSV_HEADERS:
                row_data[header] = data.get(header, '')
            
            # Write row
            self.csv_writer.writerow(row_data)
            self.row_count += 1
            
            # Flush periodically
            current_time = time.time()
            if (self.row_count >= LOG_FLUSH_ROWS or 
                current_time - self.last_flush_time >= LOG_FLUSH_INTERVAL):
                self.csv_file.flush()
                self.last_flush_time = current_time
                
                if DEBUG_MODE:
                    print(f"Flushed log file ({self.row_count} rows)")
            
            return True
            
        except Exception as e:
            print(f"Error logging data: {e}")
            return False
    
    def log_event(self, event_type, description, additional_data=None):
        """
        Log a special event (errors, state changes, etc.)
        
        Args:
            event_type: Type of event (e.g., 'error', 'warning', 'info')
            description: Event description
            additional_data: Optional dict with additional data
        """
        try:
            # Create event log entry
            data = {
                'timestamp': datetime.now().isoformat(),
                'system_status': f"{event_type.upper()}: {description}",
                'gps_latitude': '',
                'gps_longitude': '',
                'gps_altitude': '',
                'color_r': '',
                'color_g': '',
                'color_b': '',
                'distance_cm': '',
                'weight_kg': '',
                'water_level': '',
                'ml_result': '',
                'ml_confidence': '',
                'motor_state': ''
            }
            
            # Add additional data if provided
            if additional_data:
                data.update(additional_data)
            
            return self.log(data)
            
        except Exception as e:
            print(f"Error logging event: {e}")
            return False
    
    def get_current_log_path(self):
        """Get path to current log file"""
        if self.csv_file:
            return self.csv_file.name
        return None
    
    def get_log_stats(self):
        """Get statistics about current log file"""
        try:
            if not self.csv_file:
                return None
            
            filepath = self.csv_file.name
            file_size = os.path.getsize(filepath)
            
            return {
                'filepath': filepath,
                'date': self.current_date.isoformat() if self.current_date else None,
                'rows_since_flush': self.row_count,
                'file_size_bytes': file_size,
                'file_size_kb': round(file_size / 1024, 2)
            }
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error getting log stats: {e}")
            return None
    
    def force_flush(self):
        """Force flush data to disk"""
        try:
            if self.csv_file:
                self.csv_file.flush()
                os.fsync(self.csv_file.fileno())
                self.last_flush_time = time.time()
                return True
        except Exception as e:
            print(f"Error flushing log: {e}")
        return False
    
    def cleanup(self):
        """Close log file and clean up"""
        try:
            if self.csv_file:
                self.csv_file.flush()
                self.csv_file.close()
                
                if DEBUG_MODE:
                    print("Data logger cleanup complete")
                    
        except Exception as e:
            print(f"Error during logger cleanup: {e}")


# Test function for standalone testing
if __name__ == "__main__":
    print("Testing Data Logger...\n")
    
    # Initialize logger
    logger = DataLogger()
    
    if logger.initialized:
        print("Logger initialized successfully\n")
        
        # Log some test data
        print("Logging test entries...")
        for i in range(5):
            test_data = {
                'gps_latitude': 14.5995 + i * 0.0001,
                'gps_longitude': 120.9842 + i * 0.0001,
                'gps_altitude': 10.0,
                'color_r': 80 + i * 5,
                'color_g': 150 + i * 5,
                'color_b': 70 + i * 5,
                'distance_cm': 150.0 - i * 10,
                'weight_kg': 2.5 + i * 0.1,
                'water_level': True,
                'ml_result': 'Algae' if i % 2 == 0 else 'No Algae',
                'ml_confidence': 0.85 + i * 0.02,
                'motor_state': 'forward_speed_128',
                'system_status': 'normal'
            }
            
            logger.log(test_data)
            print(f"  Entry {i+1} logged")
            time.sleep(0.1)
        
        # Log an event
        print("\nLogging test event...")
        logger.log_event('info', 'Test event logged', {'motor_state': 'stopped'})
        
        # Get stats
        print("\nLog statistics:")
        stats = logger.get_log_stats()
        if stats:
            print(f"  File: {stats['filepath']}")
            print(f"  Date: {stats['date']}")
            print(f"  Rows: {stats['rows_since_flush']}")
            print(f"  Size: {stats['file_size_kb']} KB")
        
        # Force flush
        print("\nForcing flush...")
        logger.force_flush()
        
        print("\nTest complete!")
    
    else:
        print("Failed to initialize logger")
    
    # Cleanup
    logger.cleanup()

