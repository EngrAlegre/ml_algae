"""
AMLAC Robot - Main System Controller
Orchestrates all robot subsystems for autonomous algae collection
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
    """
    
    def __init__(self):
        """Initialize all robot subsystems"""
        print("\n" + "=" * 60)
        print(f"  {ROBOT_NAME} - Automated Machine Learning Algae Collector")
        print(f"  Version {ROBOT_VERSION}")
        print("=" * 60 + "\n")
        
        self.initialized = False
        self.state = "initializing"
        
        # Initialize shutdown handler
        self.shutdown_handler = GracefulShutdown()
        
        # Initialize subsystems
        log_info("Initializing motor controller...")
        self.motors = MotorController()
        
        log_info("Initializing sensors...")
        self.color_sensor = ColorSensor()
        self.ultrasonic_sensor = UltrasonicSensor()
        self.imu_sensor = IMUSensor()
        self.gps_sensor = GPSSensor()
        self.load_cell = LoadCellSensor()
        self.float_switch = FloatSwitch()
        
        log_info("Initializing ML detector...")
        self.ml_detector = AlgaeDetector()
        
        log_info("Initializing data logger...")
        self.logger = DataLogger()
        
        log_info("Initializing display...")
        self.display = LCDDisplay()
        
        # Initialize timers and watchdog
        self.main_loop_timer = Timer()
        self.collection_timer = Timer()
        self.patrol_timer = Timer()
        self.ml_processing_timer = Timer()  # Separate timer for high-frequency ML processing
        self.watchdog = Watchdog(WATCHDOG_TIMEOUT)
        
        # State tracking
        self.collecting = False
        self.total_algae_detected = 0
        self.loop_count = 0
        self.ml_result = None  # Store latest ML result for main loop
        
        # Check if critical systems initialized
        if not self.motors.initialized:
            log_error("Motor controller failed to initialize")
            self.state = "error"
            return
        
        if not self.ml_detector.initialized:
            log_error("ML detector failed to initialize")
            self.state = "error"
            return
        
        if not self.logger.initialized:
            log_error("Data logger failed to initialize")
            self.state = "error"
            return
        
        self.initialized = True
        self.state = "ready"
        
        log_info("All systems initialized successfully!")
        if self.display.initialized:
            self.display.show_message("AMLAC Ready", "Systems OK")
            time.sleep(2)
    
    def read_all_sensors(self):
        """
        Read data from all sensors
        
        Returns:
            dict: Dictionary containing all sensor readings
        """
        sensor_data = {}
        
        # Read color sensor
        color_data = self.color_sensor.read()
        if color_data:
            sensor_data['color_r'] = color_data['r']
            sensor_data['color_g'] = color_data['g']
            sensor_data['color_b'] = color_data['b']
        else:
            sensor_data['color_r'] = 0
            sensor_data['color_g'] = 0
            sensor_data['color_b'] = 0
        
        # Read ultrasonic sensor
        distance = self.ultrasonic_sensor.read()
        sensor_data['distance_cm'] = distance if distance is not None else 999.9
        
        # Read IMU (not used in main logic yet, but logged)
        imu_data = self.imu_sensor.read()
        sensor_data['imu_data'] = imu_data
        
        # Read GPS
        gps_data = self.gps_sensor.read()
        if gps_data:
            sensor_data['gps_latitude'] = gps_data['latitude']
            sensor_data['gps_longitude'] = gps_data['longitude']
            sensor_data['gps_altitude'] = gps_data['altitude']
        else:
            sensor_data['gps_latitude'] = None
            sensor_data['gps_longitude'] = None
            sensor_data['gps_altitude'] = None
        
        # Read load cell
        weight = self.load_cell.read()
        sensor_data['weight_kg'] = weight if weight is not None else 0.0
        
        # Read float switch
        water_level = self.float_switch.read()
        sensor_data['water_level'] = water_level if water_level is not None else True
        
        return sensor_data
    
    def check_safety_conditions(self, sensor_data):
        """
        Check safety conditions and return status
        
        Args:
            sensor_data: Dictionary of sensor readings
            
        Returns:
            tuple: (is_safe: bool, reason: str)
        """
        # Check water level
        if ENABLE_WATER_LEVEL_CHECK:
            if not sensor_data.get('water_level', True):
                return False, "No water detected"
        
        # Check obstacle distance
        if ENABLE_OBSTACLE_AVOIDANCE:
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
                
                if self.display.initialized:
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
        Log telemetry data to CSV
        
        Args:
            sensor_data: Dictionary of sensor readings
            ml_result: ML detection results
        """
        try:
            log_data = {
                'gps_latitude': sensor_data.get('gps_latitude', ''),
                'gps_longitude': sensor_data.get('gps_longitude', ''),
                'gps_altitude': sensor_data.get('gps_altitude', ''),
                'color_r': sensor_data.get('color_r', ''),
                'color_g': sensor_data.get('color_g', ''),
                'color_b': sensor_data.get('color_b', ''),
                'distance_cm': sensor_data.get('distance_cm', ''),
                'weight_kg': sensor_data.get('weight_kg', ''),
                'water_level': sensor_data.get('water_level', ''),
                'ml_result': ml_result.get('label', ''),
                'ml_confidence': ml_result.get('confidence', ''),
                'motor_state': self.motors.get_state(),
                'system_status': self.state
            }
            
            self.logger.log(log_data)
            
        except Exception as e:
            log_error("Error logging telemetry", e)
    
    def update_display(self, sensor_data, ml_result):
        """
        Update LCD display with current status
        
        Args:
            sensor_data: Dictionary of sensor readings
            ml_result: ML detection results
        """
        try:
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
        """Main robot control loop"""
        if not self.initialized:
            log_error("Robot not initialized properly")
            return
        
        log_info("Starting main control loop...")
        self.state = "running"
        
        if self.display.initialized:
            self.display.show_message("AMLAC Active", "Searching...")
        
        # Main loop
        while not self.shutdown_handler.should_shutdown():
            try:
                self.loop_count += 1
                loop_start = time.time()
                
                # Feed watchdog
                self.watchdog.feed()
                
                if DEBUG_MODE:
                    print(f"\n--- Loop {self.loop_count} ---")
                
                # Process camera sensor at high frequency (10 FPS) - continuous sensor mode
                # Process multiple times per main loop cycle for real-time detection
                ml_checks_this_cycle = int(MAIN_LOOP_INTERVAL / ML_INFERENCE_INTERVAL)
                for _ in range(ml_checks_this_cycle):
                    if self.ml_processing_timer.has_elapsed(ML_INFERENCE_INTERVAL):
                        self.ml_result = self.perform_algae_detection()
                        self.ml_processing_timer.reset()
                        # Small sleep to maintain processing rate
                        time.sleep(max(0, ML_INFERENCE_INTERVAL - 0.01))
                
                # Read all other sensors (at normal rate)
                sensor_data = self.read_all_sensors()
                
                # Use latest ML result (from continuous processing)
                ml_result = self.ml_result if self.ml_result else self.perform_algae_detection()
                
                # Check safety conditions
                is_safe, safety_reason = self.check_safety_conditions(sensor_data)
                
                if not is_safe:
                    log_info(f"Safety check failed: {safety_reason}")
                    self.motors.stop()
                    self.motors.stop_conveyor()
                    self.state = "safety_stop"
                    
                    if self.display.initialized:
                        self.display.show_message("SAFETY STOP", safety_reason[:16])
                    
                    # Log event
                    self.logger.log_event('warning', f'Safety stop: {safety_reason}')
                    
                    # Wait before retrying
                    time.sleep(5)
                    self.state = "running"
                    continue
                
                # Handle obstacle avoidance
                if ENABLE_OBSTACLE_AVOIDANCE:
                    distance = sensor_data.get('distance_cm', 999)
                    if distance < OBSTACLE_WARNING_DISTANCE:
                        self.handle_obstacle(sensor_data)
                        continue
                
                # Execute collection behavior
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
                
                # Check watchdog
                if self.watchdog.is_expired():
                    log_error("Watchdog expired - system may be unresponsive")
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
                self.motors.stop()
                self.motors.stop_conveyor()
                
                # Log error event
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
        self.motors.stop()
        self.motors.stop_conveyor()
        
        # Log final statistics
        log_info(f"Total loops: {self.loop_count}")
        log_info(f"Total algae detected: {self.total_algae_detected}")
        
        # Save final log entry
        self.logger.log_event('info', 'System shutdown', {
            'motor_state': 'stopped',
            'system_status': 'shutdown'
        })
        
        # Force flush logs
        log_info("Flushing logs...")
        self.logger.force_flush()
        
        # Show shutdown message on display
        if self.display.initialized:
            self.display.show_message("AMLAC", "Shutdown")
            time.sleep(1)
        
        # Cleanup all subsystems
        log_info("Cleaning up subsystems...")
        self.motors.cleanup()
        self.color_sensor.cleanup()
        self.ultrasonic_sensor.cleanup()
        self.imu_sensor.cleanup()
        self.gps_sensor.cleanup()
        self.load_cell.cleanup()
        self.float_switch.cleanup()
        self.ml_detector.cleanup()
        self.logger.cleanup()
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
        
        if not robot.initialized:
            print("\nERROR: Robot initialization failed!")
            print("Please check hardware connections and try again.")
            sys.exit(1)
        
        # Start main loop
        robot.main_loop()
        
    except Exception as e:
        log_error("Fatal error in main", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

