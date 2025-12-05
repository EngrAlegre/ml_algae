"""
Utility Functions for AMLAC Robot
Helper functions for various tasks
"""

import time
import os
import signal
import sys
from datetime import datetime

from config import (
    ALGAE_GREEN_THRESHOLD,
    ALGAE_GREEN_RATIO,
    DEBUG_MODE
)


class GracefulShutdown:
    """
    Handle graceful shutdown on SIGINT (Ctrl+C) or SIGTERM
    """
    
    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n\nShutdown signal received. Cleaning up...")
        self.shutdown_requested = True
    
    def should_shutdown(self):
        """Check if shutdown was requested"""
        return self.shutdown_requested


class Timer:
    """
    Simple timer for tracking elapsed time
    """
    
    def __init__(self):
        self.start_time = time.time()
    
    def reset(self):
        """Reset timer to current time"""
        self.start_time = time.time()
    
    def elapsed(self):
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def has_elapsed(self, seconds):
        """Check if specified seconds have elapsed"""
        return self.elapsed() >= seconds


class RateLimiter:
    """
    Rate limiter to control execution frequency
    """
    
    def __init__(self, interval):
        """
        Initialize rate limiter
        
        Args:
            interval: Minimum seconds between executions
        """
        self.interval = interval
        self.last_execution = 0
    
    def should_execute(self):
        """Check if enough time has passed to execute again"""
        current_time = time.time()
        if current_time - self.last_execution >= self.interval:
            self.last_execution = current_time
            return True
        return False
    
    def reset(self):
        """Reset the rate limiter"""
        self.last_execution = 0


def validate_color_for_algae(color_data):
    """
    Validate if color data indicates algae presence (backup validation)
    
    Args:
        color_data: Dictionary with 'r', 'g', 'b' keys
        
    Returns:
        bool: True if color suggests algae, False otherwise
    """
    if not color_data or not all(k in color_data for k in ['r', 'g', 'b']):
        return False
    
    r = color_data['r']
    g = color_data['g']
    b = color_data['b']
    
    # Check if green channel is dominant
    if g < ALGAE_GREEN_THRESHOLD:
        return False
    
    # Check if green is significantly higher than red and blue
    avg_rb = (r + b) / 2
    if avg_rb == 0:
        return g > ALGAE_GREEN_THRESHOLD
    
    green_ratio = g / avg_rb
    return green_ratio >= ALGAE_GREEN_RATIO


def format_gps_coordinates(latitude, longitude):
    """
    Format GPS coordinates for display
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        str: Formatted coordinates
    """
    if latitude is None or longitude is None:
        return "N/A"
    
    lat_dir = 'N' if latitude >= 0 else 'S'
    lon_dir = 'E' if longitude >= 0 else 'W'
    
    return f"{abs(latitude):.4f}°{lat_dir}, {abs(longitude):.4f}°{lon_dir}"


def calculate_distance_2d(x1, y1, x2, y2):
    """
    Calculate 2D Euclidean distance
    
    Args:
        x1, y1: First point coordinates
        x2, y2: Second point coordinates
        
    Returns:
        float: Distance between points
    """
    import math
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def clamp(value, min_value, max_value):
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def map_range(value, in_min, in_max, out_min, out_max):
    """
    Map value from one range to another
    
    Args:
        value: Input value
        in_min, in_max: Input range
        out_min, out_max: Output range
        
    Returns:
        Mapped value
    """
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def get_timestamp():
    """
    Get current timestamp in ISO 8601 format
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.now().isoformat()


def get_timestamp_filename():
    """
    Get timestamp suitable for filenames
    
    Returns:
        str: Formatted timestamp (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def ensure_directory(path):
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        bool: True if directory exists or was created
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False


def safe_divide(numerator, denominator, default=0):
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def retry_on_failure(func, max_retries=3, delay=0.5):
    """
    Retry a function on failure
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Function result or None on failure
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if DEBUG_MODE:
                print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                if DEBUG_MODE:
                    print(f"All {max_retries} attempts failed")
                return None


def print_system_info():
    """Print system information"""
    print("=" * 50)
    print("AMLAC Robot System Information")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current Time: {get_timestamp()}")
    print("=" * 50)


def print_sensor_summary(sensor_data):
    """
    Print formatted sensor data summary
    
    Args:
        sensor_data: Dictionary containing sensor readings
    """
    print("\n" + "=" * 50)
    print("Sensor Data Summary")
    print("=" * 50)
    
    # GPS
    if 'gps_latitude' in sensor_data and 'gps_longitude' in sensor_data:
        gps_str = format_gps_coordinates(
            sensor_data['gps_latitude'],
            sensor_data['gps_longitude']
        )
        print(f"GPS: {gps_str}")
    
    # Color
    if 'color_r' in sensor_data:
        print(f"Color: R={sensor_data['color_r']}, "
              f"G={sensor_data['color_g']}, "
              f"B={sensor_data['color_b']}")
    
    # Distance
    if 'distance_cm' in sensor_data:
        print(f"Distance: {sensor_data['distance_cm']} cm")
    
    # Weight
    if 'weight_kg' in sensor_data:
        print(f"Weight: {sensor_data['weight_kg']} kg")
    
    # Water Level
    if 'water_level' in sensor_data:
        water_status = "Present" if sensor_data['water_level'] else "Not Present"
        print(f"Water Level: {water_status}")
    
    # ML Result
    if 'ml_result' in sensor_data:
        print(f"ML Detection: {sensor_data['ml_result']} "
              f"({sensor_data.get('ml_confidence', 0)*100:.1f}%)")
    
    print("=" * 50 + "\n")


class Watchdog:
    """
    Simple watchdog timer to detect system hangs
    """
    
    def __init__(self, timeout):
        """
        Initialize watchdog
        
        Args:
            timeout: Timeout in seconds
        """
        self.timeout = timeout
        self.last_feed = time.time()
    
    def feed(self):
        """Feed the watchdog (reset timer)"""
        self.last_feed = time.time()
    
    def is_expired(self):
        """Check if watchdog has expired"""
        return (time.time() - self.last_feed) > self.timeout
    
    def time_remaining(self):
        """Get time remaining before expiration"""
        elapsed = time.time() - self.last_feed
        return max(0, self.timeout - elapsed)


class MovingAverage:
    """
    Calculate moving average of values
    """
    
    def __init__(self, window_size=5):
        """
        Initialize moving average
        
        Args:
            window_size: Number of values to average
        """
        self.window_size = window_size
        self.values = []
    
    def add(self, value):
        """Add a new value"""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
    
    def get_average(self):
        """Get current average"""
        if not self.values:
            return 0
        return sum(self.values) / len(self.values)
    
    def reset(self):
        """Reset the moving average"""
        self.values = []


def log_error(message, exception=None):
    """
    Log error message with timestamp
    
    Args:
        message: Error message
        exception: Optional exception object
    """
    timestamp = get_timestamp()
    error_msg = f"[ERROR {timestamp}] {message}"
    
    if exception:
        error_msg += f"\n  Exception: {str(exception)}"
    
    print(error_msg)
    
    # Also log to file
    try:
        error_log_path = os.path.join('logs', 'errors.log')
        ensure_directory('logs')
        with open(error_log_path, 'a') as f:
            f.write(error_msg + '\n')
    except:
        pass


def log_info(message):
    """
    Log info message with timestamp
    
    Args:
        message: Info message
    """
    if DEBUG_MODE:
        timestamp = get_timestamp()
        print(f"[INFO {timestamp}] {message}")


# Test function for standalone testing
if __name__ == "__main__":
    print("Testing Utility Functions...\n")
    
    # Test color validation
    print("1. Testing color validation for algae:")
    algae_color = {'r': 80, 'g': 150, 'b': 70}
    non_algae_color = {'r': 120, 'g': 100, 'b': 130}
    print(f"   Algae color {algae_color}: {validate_color_for_algae(algae_color)}")
    print(f"   Non-algae color {non_algae_color}: {validate_color_for_algae(non_algae_color)}")
    
    # Test GPS formatting
    print("\n2. Testing GPS formatting:")
    print(f"   {format_gps_coordinates(14.5995, 120.9842)}")
    print(f"   {format_gps_coordinates(-33.8688, 151.2093)}")
    
    # Test timer
    print("\n3. Testing timer:")
    timer = Timer()
    time.sleep(1)
    print(f"   Elapsed: {timer.elapsed():.2f}s")
    print(f"   Has 0.5s elapsed? {timer.has_elapsed(0.5)}")
    
    # Test rate limiter
    print("\n4. Testing rate limiter (1 second interval):")
    limiter = RateLimiter(1.0)
    for i in range(5):
        if limiter.should_execute():
            print(f"   Execution {i+1} allowed")
        else:
            print(f"   Execution {i+1} blocked")
        time.sleep(0.3)
    
    # Test moving average
    print("\n5. Testing moving average:")
    avg = MovingAverage(window_size=3)
    for val in [10, 20, 30, 40, 50]:
        avg.add(val)
        print(f"   Added {val}, average: {avg.get_average():.1f}")
    
    # Test watchdog
    print("\n6. Testing watchdog:")
    watchdog = Watchdog(timeout=2.0)
    print(f"   Initial time remaining: {watchdog.time_remaining():.1f}s")
    time.sleep(1)
    print(f"   After 1s: {watchdog.time_remaining():.1f}s")
    watchdog.feed()
    print(f"   After feed: {watchdog.time_remaining():.1f}s")
    
    print("\nTest complete!")

