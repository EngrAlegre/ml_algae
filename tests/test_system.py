"""
AMLAC Robot - System Test Script
Tests all modules individually before running the main system
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_test(test_name, status, message=""):
    """Print test result"""
    status_symbols = {
        'pass': '✓',
        'fail': '✗',
        'warn': '⚠'
    }
    symbol = status_symbols.get(status, '?')
    
    status_text = status.upper()
    print(f"[{symbol}] {test_name}: {status_text}")
    
    if message:
        print(f"    {message}")
    
    # Track results
    if status == 'pass':
        test_results['passed'].append(test_name)
    elif status == 'fail':
        test_results['failed'].append(test_name)
    else:
        test_results['warnings'].append(test_name)


def test_imports():
    """Test if all modules can be imported"""
    print_header("Testing Module Imports")
    
    modules = [
        'config',
        'motors',
        'sensors',
        'ml_inference',
        'data_logger',
        'display',
        'utils'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print_test(f"Import {module}", 'pass')
        except Exception as e:
            print_test(f"Import {module}", 'fail', str(e))


def test_config():
    """Test configuration module"""
    print_header("Testing Configuration")
    
    try:
        import config
        
        # Check critical paths exist
        required_attrs = [
            'MODEL_PATH',
            'LABELS_PATH',
            'LOGS_DIR',
            'MOTOR_LEFT_PWM',
            'MOTOR_RIGHT_PWM',
            'ML_CONFIDENCE_THRESHOLD'
        ]
        
        for attr in required_attrs:
            if hasattr(config, attr):
                print_test(f"Config.{attr}", 'pass', f"= {getattr(config, attr)}")
            else:
                print_test(f"Config.{attr}", 'fail', "Not found")
        
    except Exception as e:
        print_test("Configuration", 'fail', str(e))


def test_motor_controller():
    """Test motor controller initialization"""
    print_header("Testing Motor Controller")
    
    try:
        from core.motors import MotorController
        
        controller = MotorController()
        
        if controller.initialized:
            print_test("Motor Controller Init", 'pass')
            
            # Test state retrieval
            state = controller.get_state()
            print_test("Motor State", 'pass', f"State: {state}")
            
            # Cleanup
            controller.cleanup()
            print_test("Motor Cleanup", 'pass')
        else:
            print_test("Motor Controller Init", 'warn', "Not initialized (GPIO may not be available)")
        
    except Exception as e:
        print_test("Motor Controller", 'fail', str(e))


def test_sensors():
    """Test all sensors"""
    print_header("Testing Sensors")
    
    try:
        from sensors.sensors import (
            ColorSensor,
            UltrasonicSensor,
            IMUSensor,
            GPSSensor,
            LoadCellSensor,
            FloatSwitch
        )
        
        # Test each sensor
        sensors_list = [
            ('Color Sensor', ColorSensor),
            ('Ultrasonic Sensor', UltrasonicSensor),
            ('IMU Sensor', IMUSensor),
            ('GPS Sensor', GPSSensor),
            ('Load Cell', LoadCellSensor),
            ('Float Switch', FloatSwitch)
        ]
        
        for name, SensorClass in sensors_list:
            try:
                sensor = SensorClass()
                
                if sensor.initialized:
                    print_test(f"{name} Init", 'pass')
                    
                    # Try to read data
                    data = sensor.read()
                    if data is not None:
                        print_test(f"{name} Read", 'pass', f"Data: {data}")
                    else:
                        print_test(f"{name} Read", 'warn', "No data returned")
                    
                    # Cleanup
                    sensor.cleanup()
                else:
                    print_test(f"{name} Init", 'warn', "Not initialized (hardware may not be available)")
                
            except Exception as e:
                print_test(f"{name}", 'fail', str(e))
        
    except Exception as e:
        print_test("Sensors Module", 'fail', str(e))


def test_ml_inference():
    """Test ML inference module"""
    print_header("Testing ML Inference")
    
    try:
        from core.ml_inference import AlgaeDetector
        import os
        from config import MODEL_PATH, LABELS_PATH
        
        # Check if model files exist
        if os.path.exists(MODEL_PATH):
            print_test("Model File", 'pass', f"Found: {MODEL_PATH}")
        else:
            print_test("Model File", 'fail', f"Not found: {MODEL_PATH}")
        
        if os.path.exists(LABELS_PATH):
            print_test("Labels File", 'pass', f"Found: {LABELS_PATH}")
        else:
            print_test("Labels File", 'fail', f"Not found: {LABELS_PATH}")
        
        # Initialize detector
        detector = AlgaeDetector()
        
        if detector.initialized:
            print_test("ML Detector Init", 'pass')
            
            # Test detection (will use camera or simulation)
            result = detector.detect()
            
            if result:
                print_test("ML Detection", 'pass', 
                          f"Label: {result['label']}, Confidence: {result['confidence']*100:.1f}%")
            else:
                print_test("ML Detection", 'warn', "No result returned")
            
            # Cleanup
            detector.cleanup()
            print_test("ML Cleanup", 'pass')
        else:
            print_test("ML Detector Init", 'fail', "Initialization failed")
        
    except Exception as e:
        print_test("ML Inference", 'fail', str(e))


def test_data_logger():
    """Test data logger"""
    print_header("Testing Data Logger")
    
    try:
        from core.data_logger import DataLogger
        
        logger = DataLogger()
        
        if logger.initialized:
            print_test("Data Logger Init", 'pass')
            
            # Test logging
            test_data = {
                'gps_latitude': 14.5995,
                'gps_longitude': 120.9842,
                'gps_altitude': 10.0,
                'color_r': 100,
                'color_g': 150,
                'color_b': 80,
                'distance_cm': 125.5,
                'weight_kg': 2.5,
                'water_level': True,
                'ml_result': 'Test',
                'ml_confidence': 0.85,
                'motor_state': 'test',
                'system_status': 'testing'
            }
            
            if logger.log(test_data):
                print_test("Data Logging", 'pass', "Test entry logged")
            else:
                print_test("Data Logging", 'fail', "Failed to log")
            
            # Get stats
            stats = logger.get_log_stats()
            if stats:
                print_test("Log Stats", 'pass', f"File: {stats['filepath']}")
            
            # Cleanup
            logger.cleanup()
            print_test("Logger Cleanup", 'pass')
        else:
            print_test("Data Logger Init", 'fail', "Initialization failed")
        
    except Exception as e:
        print_test("Data Logger", 'fail', str(e))


def test_display():
    """Test LCD display"""
    print_header("Testing LCD Display")
    
    try:
        from core.display import LCDDisplay
        
        display = LCDDisplay()
        
        if display.initialized:
            print_test("LCD Display Init", 'pass')
            
            # Test display
            display.show_message("Test", "System Check")
            print_test("LCD Write", 'pass', "Test message displayed")
            
            time.sleep(1)
            
            # Cleanup
            display.cleanup()
            print_test("Display Cleanup", 'pass')
        else:
            print_test("LCD Display Init", 'warn', "Not initialized (I2C may not be available)")
        
    except Exception as e:
        print_test("LCD Display", 'fail', str(e))


def test_utils():
    """Test utility functions"""
    print_header("Testing Utility Functions")
    
    try:
        from utils import (
            Timer,
            RateLimiter,
            validate_color_for_algae,
            format_gps_coordinates,
            clamp
        )
        
        # Test Timer
        timer = Timer()
        time.sleep(0.1)
        if timer.elapsed() >= 0.1:
            print_test("Timer", 'pass', f"Elapsed: {timer.elapsed():.2f}s")
        else:
            print_test("Timer", 'fail', "Timer not working correctly")
        
        # Test RateLimiter
        limiter = RateLimiter(0.5)
        if limiter.should_execute():
            print_test("RateLimiter", 'pass', "First execution allowed")
        else:
            print_test("RateLimiter", 'fail', "First execution blocked")
        
        # Test color validation
        algae_color = {'r': 80, 'g': 150, 'b': 70}
        if validate_color_for_algae(algae_color):
            print_test("Color Validation", 'pass', "Algae color detected")
        else:
            print_test("Color Validation", 'warn', "Algae color not detected")
        
        # Test GPS formatting
        gps_str = format_gps_coordinates(14.5995, 120.9842)
        print_test("GPS Formatting", 'pass', f"Result: {gps_str}")
        
        # Test clamp
        if clamp(150, 0, 100) == 100:
            print_test("Clamp Function", 'pass')
        else:
            print_test("Clamp Function", 'fail')
        
    except Exception as e:
        print_test("Utility Functions", 'fail', str(e))


def test_integration():
    """Test basic integration"""
    print_header("Testing System Integration")
    
    try:
        # Try importing main module
        import main
        print_test("Main Module Import", 'pass')
        
        # Check if AMLACRobot class exists
        if hasattr(main, 'AMLACRobot'):
            print_test("AMLACRobot Class", 'pass')
        else:
            print_test("AMLACRobot Class", 'fail', "Class not found")
        
    except Exception as e:
        print_test("Integration Test", 'fail', str(e))


def print_summary():
    """Print test summary"""
    print_header("Test Summary")
    
    total_tests = len(test_results['passed']) + len(test_results['failed']) + len(test_results['warnings'])
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"  ✓ Passed:   {len(test_results['passed'])}")
    print(f"  ✗ Failed:   {len(test_results['failed'])}")
    print(f"  ⚠ Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\nFailed Tests:")
        for test in test_results['failed']:
            print(f"  - {test}")
    
    if test_results['warnings']:
        print("\nWarnings:")
        for test in test_results['warnings']:
            print(f"  - {test}")
    
    print("\n" + "=" * 60)
    
    if not test_results['failed']:
        print("  ✓ All critical tests passed!")
        print("  System is ready to run.")
    else:
        print("  ✗ Some tests failed.")
        print("  Please fix issues before running the main system.")
    
    print("=" * 60 + "\n")
    
    return len(test_results['failed']) == 0


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("  AMLAC Robot - System Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all tests
    test_imports()
    test_config()
    test_motor_controller()
    test_sensors()
    test_ml_inference()
    test_data_logger()
    test_display()
    test_utils()
    test_integration()
    
    # Print summary
    success = print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

