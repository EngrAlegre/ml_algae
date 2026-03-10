"""
AMLAC Robot - Main System Controller
Orchestrates all robot subsystems for autonomous algae collection
Supports graceful degradation when hardware is not connected
"""

import time
import sys

# Import all modules
from config import (
    MAIN_LOOP_INTERVAL,
    ML_INFERENCE_INTERVAL,
    ML_CONFIDENCE_THRESHOLD,
    COLLECTION_DURATION,
    PATROL_MOVE_DURATION,
    OBSTACLE_WARNING_DISTANCE,
    ENABLE_WATER_LEVEL_CHECK,
    ENABLE_OBSTACLE_AVOIDANCE,
    WATCHDOG_TIMEOUT,
    ALGAE_APPROACH_SPEED,
    PADDLE_DEFAULT_SPEED,
    WATER_CLEAR_CHANNEL_THRESHOLD,
    DEBUG_MODE,
    ROBOT_NAME,
    ROBOT_VERSION
)

from core.motors import MotorController
from sensors.sensors import (
    ColorSensor,
    UltrasonicSensor,
    IMUSensor,
    GPSSensor,
    LoadCellSensor,
    FloatSwitch
)
from core.ml_inference import AlgaeDetector
from core.data_logger import DataLogger
try:
    from core.firebase_logger import FirebaseLogger
    FIREBASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Firebase logger not available: {e}")
    FirebaseLogger = None
    FIREBASE_AVAILABLE = False
from core.display import LCDDisplay
from utils import (
    GracefulShutdown,
    Timer,
    Watchdog,
    print_system_info,
    print_sensor_summary,
    log_error,
    log_info,
    validate_color_for_algae
)


class AMLACRobot:
    """
    Main AMLAC Robot Controller
    Integrates all subsystems and implements autonomous behavior
    Supports graceful degradation when hardware is unavailable
    """
    
    def __init__(self):
        """Initialize all robot subsystems with graceful degradation"""
        print("\n" + "=" * 60)
        print(f"  {ROBOT_NAME} - Automated Machine Learning Algae Collector")
        print(f"  Version {ROBOT_VERSION}")
        print("=" * 60 + "\n")
        
        self.initialized = False
        self.state = "initializing"
        
        # Track hardware status
        self.hardware_status = {
            'motors': False,
            'camera': False,
            'ml_model': False,
            'color_sensor': False,
            'ultrasonic': False,
            'imu': False,
            'gps': False,
            'load_cell': False,
            'float_switch': False,
            'display': False,
            'firebase': False,
            'logger': False
        }
        
        # Initialize shutdown handler
        self.shutdown_handler = GracefulShutdown()
        
        # Initialize all subsystems with error handling
        self._init_motors()
        self._init_sensors()
        self._init_ml_detector()
        self._init_loggers()
        self._init_display()
        
        # Initialize timers and watchdog
        self.main_loop_timer = Timer()
        self.collection_timer = Timer()
        self.patrol_timer = Timer()
        self.ml_processing_timer = Timer()
        self.watchdog = Watchdog(WATCHDOG_TIMEOUT)
        self.status_display_timer = Timer()  # For cycling hardware status
        
        # State tracking
        self.collecting = False
        self.total_algae_detected = 0
        self.loop_count = 0
        self.ml_result = None
        self.status_display_index = 0  # For cycling through status messages
        
        # Count working systems
        working_count = sum(1 for v in self.hardware_status.values() if v)
        total_count = len(self.hardware_status)
        
        # Always initialize - run in degraded mode if needed
        self.initialized = True
        self.state = "ready"
        
        # Print hardware status summary
        self._print_hardware_status()
        
        log_info(f"System initialized: {working_count}/{total_count} components ready")
        
        # Show status on display
        if self.hardware_status['display']:
            self._show_startup_status()
    
    def _init_motors(self):
        """Initialize motor controller"""
        log_info("Initializing motor controller...")
        try:
            self.motors = MotorController()
            self.hardware_status['motors'] = self.motors.initialized
        except Exception as e:
            log_error("Motor controller init failed", e)
            self.motors = None
            self.hardware_status['motors'] = False
    
    def _init_sensors(self):
        """Initialize all sensors"""
        log_info("Initializing sensors...")
        
        # Color sensor
        try:
            self.color_sensor = ColorSensor()
            self.hardware_status['color_sensor'] = self.color_sensor.initialized
        except Exception as e:
            log_error("Color sensor init failed", e)
            self.color_sensor = None
            
        # Ultrasonic sensor
        try:
            self.ultrasonic_sensor = UltrasonicSensor()
            self.hardware_status['ultrasonic'] = self.ultrasonic_sensor.initialized
        except Exception as e:
            log_error("Ultrasonic sensor init failed", e)
            self.ultrasonic_sensor = None
            
        # IMU sensor
        try:
            self.imu_sensor = IMUSensor()
            self.hardware_status['imu'] = self.imu_sensor.initialized
        except Exception as e:
            log_error("IMU sensor init failed", e)
            self.imu_sensor = None
            
        # GPS sensor
        try:
            self.gps_sensor = GPSSensor()
            self.hardware_status['gps'] = self.gps_sensor.initialized
        except Exception as e:
            log_error("GPS sensor init failed", e)
            self.gps_sensor = None
            
        # Load cell
        try:
            self.load_cell = LoadCellSensor()
            self.hardware_status['load_cell'] = self.load_cell.initialized
        except Exception as e:
            log_error("Load cell init failed", e)
            self.load_cell = None
            
        # Float switch
        try:
            self.float_switch = FloatSwitch()
            self.hardware_status['float_switch'] = self.float_switch.initialized
        except Exception as e:
            log_error("Float switch init failed", e)
            self.float_switch = None
    
    def _init_ml_detector(self):
        """Initialize ML detector"""
        log_info("Initializing ML detector...")
        try:
            self.ml_detector = AlgaeDetector()
            self.hardware_status['ml_model'] = self.ml_detector.initialized
            self.hardware_status['camera'] = self.ml_detector.camera_initialized if hasattr(self.ml_detector, 'camera_initialized') else self.ml_detector.initialized
        except Exception as e:
            log_error("ML detector init failed", e)
            self.ml_detector = None
            self.hardware_status['ml_model'] = False
            self.hardware_status['camera'] = False
    
    def _init_loggers(self):
        """Initialize data loggers"""
        log_info("Initializing data logger...")
        try:
            self.logger = DataLogger()
            self.hardware_status['logger'] = self.logger.initialized
        except Exception as e:
            log_error("Data logger init failed", e)
            self.logger = None
            
        log_info("Initializing Firebase logger...")
        if FIREBASE_AVAILABLE and FirebaseLogger:
            try:
                self.firebase_logger = FirebaseLogger()
                self.hardware_status['firebase'] = self.firebase_logger.initialized
            except Exception as e:
                log_error("Firebase logger init failed", e)
                self.firebase_logger = None
        else:
            print("Warning: Firebase logger not available - skipping")
            self.firebase_logger = None
            self.hardware_status['firebase'] = False
    
    def _init_display(self):
        """Initialize LCD display with extra reliability"""
        log_info("Initializing display...")
        try:
            self.display = LCDDisplay()
            
            if self.display.initialized:
                # Give LCD extra settling time after initialization
                time.sleep(0.5)
                
                # Reinitialize once more to ensure clean state
                # This helps prevent garbled text on cold boot
                self.display.reinit()
                time.sleep(0.3)
            
            self.hardware_status['display'] = self.display.initialized
        except Exception as e:
            log_error("Display init failed", e)
            self.display = None
    
    def _print_hardware_status(self):
        """Print hardware status summary"""
        print("\n" + "-" * 40)
        print("  HARDWARE STATUS")
        print("-" * 40)
        
        status_items = [
            ('Motors', 'motors'),
            ('Camera', 'camera'),
            ('ML Model', 'ml_model'),
            ('Color Sensor', 'color_sensor'),
            ('Ultrasonic', 'ultrasonic'),
            ('IMU', 'imu'),
            ('GPS', 'gps'),
            ('Load Cell', 'load_cell'),
            ('Float Switch', 'float_switch'),
            ('LCD Display', 'display'),
            ('Firebase', 'firebase'),
            ('Logger', 'logger'),
        ]
        
        for name, key in status_items:
            status = "OK" if self.hardware_status[key] else "NOT CONNECTED"
            symbol = "✓" if self.hardware_status[key] else "✗"
            print(f"  {symbol} {name}: {status}")
        
        print("-" * 40 + "\n")
    
    def _show_startup_status(self):
        """Show startup status on LCD"""
        if not self.display or not self.hardware_status['display']:
            return
            
        # Count working/total
        working = sum(1 for v in self.hardware_status.values() if v)
        total = len(self.hardware_status)
        
        # Show summary
        self.display.show_message("AMLAC Starting", f"HW: {working}/{total} Ready")
        time.sleep(2)
        
        # Show critical systems status
        critical_status = []
        
        if not self.hardware_status['motors']:
            critical_status.append(("MOTORS", "NOT FOUND"))
        if not self.hardware_status['camera']:
            critical_status.append(("CAMERA", "NOT FOUND"))
        if not self.hardware_status['ml_model']:
            critical_status.append(("ML MODEL", "NOT LOADED"))
            
        # Show warnings for critical systems
        for name, status in critical_status:
            self.display.show_message(f"WARN: {name}", status)
            time.sleep(1.5)
        
        # Final ready message
        if working == total:
            self.display.show_message("AMLAC Ready", "All Systems OK")
        else:
            self.display.show_message("AMLAC Ready", f"Degraded Mode")
        time.sleep(1)
    
    def _get_status_message(self):
        """Get current hardware status message for LCD rotation"""
        # List of status messages to cycle through
        messages = []
        
        # Add status for each component
        if not self.hardware_status['motors']:
            messages.append(("MOTORS", "Disconnected"))
        if not self.hardware_status['camera']:
            messages.append(("CAMERA", "Disconnected"))
        if not self.hardware_status['ml_model']:
            messages.append(("ML MODEL", "Not Loaded"))
        if not self.hardware_status['color_sensor']:
            messages.append(("COLOR SENS", "Disconnected"))
        if not self.hardware_status['ultrasonic']:
            messages.append(("ULTRASONIC", "Disconnected"))
        if not self.hardware_status['gps']:
            messages.append(("GPS", "Disconnected"))
        if not self.hardware_status['load_cell']:
            messages.append(("LOAD CELL", "Disconnected"))
        if not self.hardware_status['float_switch']:
            messages.append(("FLOAT SW", "Disconnected"))
        if not self.hardware_status['firebase']:
            messages.append(("FIREBASE", "Offline"))
        
        if not messages:
            return None  # All systems OK
        
        # Cycle through messages
        self.status_display_index = (self.status_display_index + 1) % len(messages)
        return messages[self.status_display_index]
    
    def read_all_sensors(self):
        """
        Read data from all sensors with graceful handling
        
        Returns:
            dict: Dictionary containing all sensor readings
        """
        sensor_data = {}
        
        # Read color sensor
        if self.color_sensor and self.hardware_status['color_sensor']:
            color_data = self.color_sensor.read()
            if color_data:
                sensor_data['color_r'] = color_data['r']
                sensor_data['color_g'] = color_data['g']
                sensor_data['color_b'] = color_data['b']
                sensor_data['color_clear'] = color_data.get('clear')
            else:
                sensor_data['color_r'] = 0
                sensor_data['color_g'] = 0
                sensor_data['color_b'] = 0
                sensor_data['color_clear'] = None
        else:
            sensor_data['color_r'] = 0
            sensor_data['color_g'] = 0
            sensor_data['color_b'] = 0
            sensor_data['color_clear'] = None
        
        # Read ultrasonic sensor
        if self.ultrasonic_sensor and self.hardware_status['ultrasonic']:
            distance = self.ultrasonic_sensor.read()
            sensor_data['distance_cm'] = distance if distance is not None else 999.9
        else:
            sensor_data['distance_cm'] = 999.9  # Safe default (no obstacle)
        
        # Read IMU
        if self.imu_sensor and self.hardware_status['imu']:
            imu_data = self.imu_sensor.read()
            sensor_data['imu_data'] = imu_data
        else:
            sensor_data['imu_data'] = None
        
        # Read GPS
        if self.gps_sensor and self.hardware_status['gps']:
            gps_data = self.gps_sensor.read()
            if gps_data:
                sensor_data['gps_latitude'] = gps_data['latitude']
                sensor_data['gps_longitude'] = gps_data['longitude']
                sensor_data['gps_altitude'] = gps_data['altitude']
            else:
                sensor_data['gps_latitude'] = None
                sensor_data['gps_longitude'] = None
                sensor_data['gps_altitude'] = None
        else:
            sensor_data['gps_latitude'] = None
            sensor_data['gps_longitude'] = None
            sensor_data['gps_altitude'] = None
        
        # Read load cell
        if self.load_cell and self.hardware_status['load_cell']:
            weight = self.load_cell.read()
            sensor_data['weight_kg'] = weight if weight is not None else 0.0
        else:
            sensor_data['weight_kg'] = 0.0
        
        # Read float switch
        if self.float_switch and self.hardware_status['float_switch']:
            water_level = self.float_switch.read()
            sensor_data['water_level'] = water_level if water_level is not None else True
        else:
            sensor_data['water_level'] = True  # Assume water present if no sensor
        
        return sensor_data
    
    def check_safety_conditions(self, sensor_data):
        """
        Check safety conditions and return status
        
        Args:
            sensor_data: Dictionary of sensor readings
            
        Returns:
            tuple: (is_safe: bool, reason: str)
        """
        # Check water level (only if sensor is connected)
        if ENABLE_WATER_LEVEL_CHECK and self.hardware_status['float_switch']:
            if not sensor_data.get('water_level', True):
                return False, "No water detected"
        
        # Check obstacle distance (only if sensor is connected)
        if ENABLE_OBSTACLE_AVOIDANCE and self.hardware_status['ultrasonic']:
            distance = sensor_data.get('distance_cm', 999)
            if distance < OBSTACLE_WARNING_DISTANCE:
                return False, f"Obstacle too close ({distance:.1f}cm)"
        
        return True, "OK"
    
    def perform_algae_detection(self):
        """
        Perform ML-based algae detection
        
        Returns:
            dict: Detection results
        """
        # Check if ML detector is available
        if not self.ml_detector or not self.hardware_status['ml_model']:
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'ML Unavailable',
                'all_scores': []
            }
        
        try:
            result = self.ml_detector.detect()
            return result
        except Exception as e:
            log_error("Error during algae detection", e)
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'Error',
                'all_scores': []
            }
    
    def execute_collection_behavior(self, sensor_data, ml_result):
        """
        Execute algae collection behavior
        
        Args:
            sensor_data: Dictionary of sensor readings
            ml_result: ML detection results
        """
        # Check if motors are available
        if not self.motors or not self.hardware_status['motors']:
            return  # Can't execute behavior without motors
        
        is_algae = ml_result['is_algae']
        confidence = ml_result['confidence']
        
        if is_algae and confidence >= ML_CONFIDENCE_THRESHOLD:
            # Algae detected with high confidence
            if not self.collecting:
                log_info(f"Algae detected! Confidence: {confidence*100:.1f}%")
                self.total_algae_detected += 1
                
                # Start collection sequence
                self.collecting = True
                self.collection_timer.reset()
                
                # Move toward algae
                self.motors.move_forward(ALGAE_APPROACH_SPEED)
                
                # Start conveyor
                self.motors.start_conveyor()
                
                if self.display and self.hardware_status['display']:
                    self.display.show_message("COLLECTING", "Algae Detected!")
            
            # Continue collection for specified duration
            if self.collection_timer.has_elapsed(COLLECTION_DURATION):
                log_info("Collection complete")
                
                # Stop motors
                self.motors.stop()
                self.motors.stop_conveyor()
                
                self.collecting = False
                self.patrol_timer.reset()
        
        else:
            # No algae or low confidence - patrol mode
            if self.collecting:
                # Stop collection
                self.motors.stop()
                self.motors.stop_conveyor()
                self.collecting = False
                self.patrol_timer.reset()
            
            # Patrol behavior - move forward slowly
            if not self.collecting:
                # Check if it's time to move
                if self.patrol_timer.has_elapsed(PATROL_MOVE_DURATION):
                    self.motors.stop()
                    time.sleep(0.5)
                    self.patrol_timer.reset()
                else:
                    # Continue patrol
                    self.motors.move_forward(PADDLE_DEFAULT_SPEED)
    
    def handle_obstacle(self, sensor_data):
        """
        Handle obstacle avoidance
        
        Args:
            sensor_data: Dictionary of sensor readings
        """
        if not self.motors or not self.hardware_status['motors']:
            return  # Can't handle obstacle without motors
        
        distance = sensor_data.get('distance_cm', 999)
        
        if distance < OBSTACLE_WARNING_DISTANCE:
            log_info(f"Obstacle detected at {distance:.1f}cm - avoiding")
            
            # Stop
            self.motors.stop()
            self.motors.stop_conveyor()
            time.sleep(0.5)
            
            # Back up
            self.motors.move_backward(PADDLE_DEFAULT_SPEED)
            time.sleep(1)
            
            # Turn right
            self.motors.turn_right(PADDLE_DEFAULT_SPEED)
            time.sleep(1.5)
            
            # Stop
            self.motors.stop()
            
            self.collecting = False
            self.patrol_timer.reset()
    
    def log_telemetry(self, sensor_data, ml_result):
        """
        Log telemetry data to CSV and Firebase
        
        Args:
            sensor_data: Dictionary of sensor readings
            ml_result: ML detection results
        """
        try:
            motor_state = self.motors.get_state() if self.motors else "unavailable"
            color_clear = sensor_data.get('color_clear')

            if color_clear is None:
                water_condition = 'unknown'
            elif color_clear >= WATER_CLEAR_CHANNEL_THRESHOLD:
                water_condition = 'clear'
            else:
                water_condition = 'muddy'
            
            log_data = {
                'gps_latitude': sensor_data.get('gps_latitude', ''),
                'gps_longitude': sensor_data.get('gps_longitude', ''),
                'gps_altitude': sensor_data.get('gps_altitude', ''),
                'color_r': sensor_data.get('color_r', ''),
                'color_g': sensor_data.get('color_g', ''),
                'color_b': sensor_data.get('color_b', ''),
                'color_clear': color_clear,
                'distance_cm': sensor_data.get('distance_cm', ''),
                'weight_kg': sensor_data.get('weight_kg', ''),
                'water_level': sensor_data.get('water_level', ''),
                'water_condition': water_condition,
                'ml_result': ml_result.get('label', ''),
                'ml_confidence': ml_result.get('confidence', ''),
                'actual_label': sensor_data.get('actual_label', ''),
                'motor_state': motor_state,
                'system_status': self.state
            }
            
            # Log to CSV (local backup)
            if self.logger and self.hardware_status['logger']:
                self.logger.log(log_data)
            
            # Log to Firebase (real-time database)
            if self.firebase_logger and self.hardware_status['firebase']:
                self.firebase_logger.log(log_data)
                
                # Upload camera frame every 5 loops (~5 seconds) to avoid excessive uploads
                if self.loop_count % 5 == 0 and self.ml_detector and self.hardware_status['camera']:
                    try:
                        frame = self.ml_detector.capture_frame()
                        if frame is not None:
                            self.firebase_logger.upload_camera_frame(frame, ml_result)
                    except Exception as cam_err:
                        if DEBUG_MODE:
                            print(f"Camera frame upload error: {cam_err}")
            
        except Exception as e:
            log_error("Error logging telemetry", e)
    
    def update_display(self, sensor_data, ml_result):
        """
        Update LCD display with current status
        
        Args:
            sensor_data: Dictionary of sensor readings
            ml_result: ML detection results
        """
        if not self.display or not self.hardware_status['display']:
            return
        
        try:
            # Check if any hardware is disconnected - show warning periodically
            if self.status_display_timer.has_elapsed(10):  # Every 10 seconds
                status_msg = self._get_status_message()
                if status_msg:
                    self.display.show_message(f"WARN:{status_msg[0]}", status_msg[1])
                    time.sleep(1.5)
                    self.status_display_timer.reset()
            
            # Normal display update
            display_data = {
                'is_algae': ml_result.get('is_algae', False),
                'ml_confidence': ml_result.get('confidence', 0.0),
                'gps_latitude': sensor_data.get('gps_latitude'),
                'gps_longitude': sensor_data.get('gps_longitude'),
                'weight_kg': sensor_data.get('weight_kg', 0.0),
                'distance_cm': sensor_data.get('distance_cm', 0.0),
                'system_status': self.state,
                'water_level': sensor_data.get('water_level', True)
            }
            
            self.display.update_display(display_data)
            
        except Exception as e:
            log_error("Error updating display", e)
    
    def main_loop(self):
        """Main robot control loop with graceful degradation"""
        if not self.initialized:
            log_error("Robot not initialized properly")
            return
        
        log_info("Starting main control loop...")
        self.state = "running"
        
        # Show starting message
        if self.display and self.hardware_status['display']:
            if self.hardware_status['motors'] and self.hardware_status['ml_model']:
                self.display.show_message("AMLAC Active", "Searching...")
            else:
                self.display.show_message("AMLAC Active", "Limited Mode")
        
        # Main loop
        while not self.shutdown_handler.should_shutdown():
            try:
                self.loop_count += 1
                loop_start = time.time()
                
                # Feed watchdog
                self.watchdog.feed()
                
                if DEBUG_MODE:
                    print(f"\n--- Loop {self.loop_count} ---")
                
                # Process ML detection at high frequency (if available)
                if self.ml_detector and self.hardware_status['ml_model']:
                    ml_checks_this_cycle = int(MAIN_LOOP_INTERVAL / ML_INFERENCE_INTERVAL)
                    for _ in range(ml_checks_this_cycle):
                        if self.ml_processing_timer.has_elapsed(ML_INFERENCE_INTERVAL):
                            self.ml_result = self.perform_algae_detection()
                            self.ml_processing_timer.reset()
                            time.sleep(max(0, ML_INFERENCE_INTERVAL - 0.01))
                
                # Read all other sensors (at normal rate)
                sensor_data = self.read_all_sensors()
                
                # Use latest ML result
                ml_result = self.ml_result if self.ml_result else self.perform_algae_detection()
                
                # Check safety conditions
                is_safe, safety_reason = self.check_safety_conditions(sensor_data)
                
                if not is_safe:
                    log_info(f"Safety check failed: {safety_reason}")
                    if self.motors:
                        self.motors.stop()
                        self.motors.stop_conveyor()
                    self.state = "safety_stop"
                    
                    if self.display and self.hardware_status['display']:
                        self.display.show_message("SAFETY STOP", safety_reason[:16])
                    
                    # Log event
                    if self.logger:
                        self.logger.log_event('warning', f'Safety stop: {safety_reason}')
                    
                    # Wait before retrying
                    time.sleep(5)
                    self.state = "running"
                    continue
                
                # Handle obstacle avoidance
                if ENABLE_OBSTACLE_AVOIDANCE and self.hardware_status['ultrasonic']:
                    distance = sensor_data.get('distance_cm', 999)
                    if distance < OBSTACLE_WARNING_DISTANCE:
                        self.handle_obstacle(sensor_data)
                        continue
                
                # Execute collection behavior (if motors available)
                self.execute_collection_behavior(sensor_data, ml_result)
                
                # Log telemetry
                self.log_telemetry(sensor_data, ml_result)
                
                # Update display
                self.update_display(sensor_data, ml_result)
                
                # Print summary if in debug mode
                if DEBUG_MODE:
                    print(f"State: {self.state}")
                    print(f"ML: {ml_result['label']} ({ml_result['confidence']*100:.1f}%)")
                    print(f"Distance: {sensor_data.get('distance_cm', 'N/A')} cm")
                    print(f"Weight: {sensor_data.get('weight_kg', 'N/A')} kg")
                    print(f"Total algae detected: {self.total_algae_detected}")
                    
                    # Show hardware status
                    hw_ok = sum(1 for v in self.hardware_status.values() if v)
                    hw_total = len(self.hardware_status)
                    print(f"Hardware: {hw_ok}/{hw_total} connected")
                
                # Check watchdog
                if self.watchdog.is_expired():
                    log_error("Watchdog expired - system may be unresponsive")
                    if self.logger:
                        self.logger.log_event('error', 'Watchdog timeout')
                    self.watchdog.feed()
                
                # Sleep until next cycle
                loop_duration = time.time() - loop_start
                sleep_time = max(0, MAIN_LOOP_INTERVAL - loop_duration)
                
                if DEBUG_MODE:
                    print(f"Loop duration: {loop_duration:.2f}s, sleeping: {sleep_time:.2f}s")
                
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                # Handle Ctrl+C
                break
                
            except Exception as e:
                log_error("Error in main loop", e)
                self.state = "error"
                if self.motors:
                    self.motors.stop()
                    self.motors.stop_conveyor()
                
                # Log error event
                if self.logger:
                    self.logger.log_event('error', f'Main loop error: {str(e)}')
                
                # Wait before continuing
                time.sleep(2)
                self.state = "running"
        
        # Shutdown sequence
        log_info("Shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown of all systems"""
        print("\n" + "=" * 60)
        print("  Shutting down AMLAC Robot...")
        print("=" * 60 + "\n")
        
        self.state = "shutdown"
        
        # Stop all motors
        log_info("Stopping motors...")
        if self.motors:
            self.motors.stop()
            self.motors.stop_conveyor()
        
        # Log final statistics
        log_info(f"Total loops: {self.loop_count}")
        log_info(f"Total algae detected: {self.total_algae_detected}")
        
        # Save final log entry
        if self.logger:
            self.logger.log_event('info', 'System shutdown', {
                'motor_state': 'stopped',
                'system_status': 'shutdown'
            })
        
        # Force flush logs
        log_info("Flushing logs...")
        if self.logger:
            self.logger.force_flush()
        
        # Show shutdown message on display
        if self.display and self.hardware_status['display']:
            self.display.show_message("AMLAC", "Shutdown")
            time.sleep(1)
        
        # Cleanup all subsystems
        log_info("Cleaning up subsystems...")
        
        if self.motors:
            self.motors.cleanup()
        if self.color_sensor:
            self.color_sensor.cleanup()
        if self.ultrasonic_sensor:
            self.ultrasonic_sensor.cleanup()
        if self.imu_sensor:
            self.imu_sensor.cleanup()
        if self.gps_sensor:
            self.gps_sensor.cleanup()
        if self.load_cell:
            self.load_cell.cleanup()
        if self.float_switch:
            self.float_switch.cleanup()
        if self.ml_detector:
            self.ml_detector.cleanup()
        if self.logger:
            self.logger.cleanup()
        if self.firebase_logger and self.hardware_status['firebase']:
            self.firebase_logger.cleanup()
        if self.display:
            self.display.cleanup()
        
        print("\n" + "=" * 60)
        print("  Shutdown complete. Goodbye!")
        print("=" * 60 + "\n")


def main():
    """Main entry point"""
    try:
        # Print system info
        print_system_info()
        
        # Create and initialize robot
        robot = AMLACRobot()
        
        # Always start - graceful degradation handles missing hardware
        if not robot.initialized:
            print("\nWARNING: Robot running in limited mode!")
            print("Some hardware components are not connected.")
        
        # Start main loop
        robot.main_loop()
        
    except Exception as e:
        log_error("Fatal error in main", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
