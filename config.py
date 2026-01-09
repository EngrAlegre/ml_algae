"""
AMLAC Robot Configuration File
All constants, GPIO pin mappings, and settings for the robot system.
"""

import os

# ==================== SYSTEM PATHS ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'model.tflite')
LABELS_PATH = os.path.join(MODELS_DIR, 'labels.txt')

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
# Detection images directory will be created if SAVE_DETECTION_IMAGES is True

# ==================== GPIO PIN MAPPINGS ====================
# Motor Driver 1 (L298N) - Paddle Wheels
MOTOR_LEFT_IN1 = 17      # Left wheel direction pin 1
MOTOR_LEFT_IN2 = 27      # Left wheel direction pin 2
MOTOR_LEFT_PWM = 18      # Left wheel speed (PWM)

MOTOR_RIGHT_IN1 = 22     # Right wheel direction pin 1
MOTOR_RIGHT_IN2 = 23     # Right wheel direction pin 2
MOTOR_RIGHT_PWM = 13     # Right wheel speed (PWM)

# Motor Driver 2 (L298N) - Conveyor Belt
CONVEYOR_IN1 = 24        # Conveyor direction pin 1
CONVEYOR_IN2 = 25        # Conveyor direction pin 2
CONVEYOR_PWM = 12        # Conveyor speed (PWM)

# Ultrasonic Sensor (JSN-SR04T)
ULTRASONIC_TRIGGER = 20
ULTRASONIC_ECHO = 21

# Float Switch (Water Level Detection)
FLOAT_SWITCH_PIN = 11

# ==================== I2C ADDRESSES ====================
TCS34725_ADDRESS = 0x29   # RGB Color Sensor
MPU6050_ADDRESS = 0x68    # IMU (Accelerometer/Gyro)
LCD_ADDRESS = 0x27        # 16x2 LCD Display
I2C_BUS = 1               # I2C bus number (typically 1 on Pi 5)

# ==================== SENSOR SETTINGS ====================
# Ultrasonic Sensor
ULTRASONIC_MAX_DISTANCE = 400  # cm
ULTRASONIC_TIMEOUT = 0.1       # seconds
OBSTACLE_WARNING_DISTANCE = 30  # cm (stop if closer than this)

# Color Sensor (TCS34725)
COLOR_INTEGRATION_TIME = 0x01  # 2.4ms (fast reading)
COLOR_GAIN = 0x01              # 4x gain

# GPS (NEO-6M)
GPS_SERIAL_PORT = '/dev/serial0'  # UART port
GPS_BAUDRATE = 9600
GPS_TIMEOUT = 1.0

# Load Cell (HX711)
HX711_DATA_PIN = 8
HX711_CLOCK_PIN = 7
HX711_CALIBRATION_FACTOR = 2280  # Adjust based on calibration
HX711_REFERENCE_UNIT = 1         # Reference unit for weight

# ==================== MOTOR SETTINGS ====================
# Paddle Wheels (78 RPM motors)
PADDLE_DEFAULT_SPEED = 128       # 0-255 (50% PWM)
PADDLE_TURN_SPEED = 100          # Speed during turns
PADDLE_MAX_SPEED = 200           # Maximum speed limit

# Conveyor Belt (188 RPM motor)
CONVEYOR_DEFAULT_SPEED = 153     # 0-255 (60% PWM)
CONVEYOR_MAX_SPEED = 220         # Maximum speed limit

# PWM Frequency
PWM_FREQUENCY = 1000  # Hz

# ==================== ML INFERENCE SETTINGS ====================
ML_CONFIDENCE_THRESHOLD = 0.7    # Minimum confidence to act on detection
ML_INPUT_SIZE = (224, 224)       # Model input dimensions
ML_INFERENCE_INTERVAL = 0.1      # Seconds between ML checks (~10 FPS for continuous sensor mode)
ML_CONFIRMATION_FRAMES = 2       # Require N consecutive detections before acting (reduces false positives)
SAVE_DETECTION_IMAGES = False    # Save images only when algae detected (for debugging)
DETECTION_IMAGES_DIR = os.path.join(BASE_DIR, 'detection_images')  # Where to save debug images

# ==================== TIMING CONSTANTS ====================
MAIN_LOOP_INTERVAL = 2.0         # Seconds between main loop cycles
SENSOR_READ_TIMEOUT = 2.0        # Seconds to wait for sensor response
DISPLAY_ROTATE_INTERVAL = 4.0    # Seconds to show each display mode
COLLECTION_DURATION = 8.0        # Seconds to run conveyor when collecting
PATROL_MOVE_DURATION = 3.0       # Seconds to move forward during patrol

# ==================== DATA LOGGING SETTINGS ====================
LOG_FLUSH_INTERVAL = 30          # Seconds between CSV flushes
LOG_FLUSH_ROWS = 10              # Rows before forcing flush
LOG_RETENTION_DAYS = 3           # Days to keep old logs

# CSV Column Headers
CSV_HEADERS = [
    'timestamp',
    'gps_latitude',
    'gps_longitude',
    'gps_altitude',
    'color_r',
    'color_g',
    'color_b',
    'distance_cm',
    'weight_kg',
    'water_level',
    'ml_result',
    'ml_confidence',
    'motor_state',
    'system_status'
]

# ==================== DISPLAY SETTINGS ====================
LCD_ROWS = 2
LCD_COLS = 16
DISPLAY_MODES = ['algae', 'gps', 'weight', 'distance', 'status']

# ==================== SYSTEM BEHAVIOR ====================
# Algae Collection Behavior
ALGAE_APPROACH_SPEED = 100       # Speed when approaching algae
ALGAE_SEARCH_MODE = True         # Enable autonomous search

# Safety Settings
ENABLE_WATER_LEVEL_CHECK = True  # Stop if no water detected
ENABLE_OBSTACLE_AVOIDANCE = True # Stop/turn if obstacle detected
WATCHDOG_TIMEOUT = 30            # Seconds before system restart warning

# Error Handling
MAX_SENSOR_RETRIES = 3           # Retries before marking sensor as failed
GRACEFUL_DEGRADATION = True      # Continue operation if non-critical sensor fails

# ==================== DEBUG SETTINGS ====================
DEBUG_MODE = True                # Enable verbose logging
SIMULATE_SENSORS = False         # DISABLED - Running on real hardware (Raspberry Pi 5)
LOG_TO_CONSOLE = True            # Print logs to console
LOG_TO_FILE = True               # Save logs to file

# ==================== ALGAE DETECTION THRESHOLDS ====================
# Color-based algae detection (backup/validation)
ALGAE_GREEN_THRESHOLD = 100      # Minimum green channel value
ALGAE_GREEN_RATIO = 1.3          # Green should be X times higher than red/blue

# ==================== SYSTEM INFO ====================
ROBOT_NAME = "AMLAC-001"
ROBOT_VERSION = "1.0.0"
SYSTEM_DESCRIPTION = "Automated Machine Learning Algae Collector"

