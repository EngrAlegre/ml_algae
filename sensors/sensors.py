"""
Sensor Module for AMLAC Robot
Handles all sensor readings:
- TCS34725 (RGB Color Sensor)
- JSN-SR04T (Ultrasonic Distance)
- MPU6050 (IMU - Accelerometer/Gyro)
- NEO-6M (GPS)
- HX711 (Load Cell)
- Float Switch (Water Level)

Updated for Raspberry Pi 5 compatibility using lgpio instead of RPi.GPIO
"""

import time
import serial
import math

# Try lgpio first (Raspberry Pi 5), then fall back to RPi.GPIO (older Pi)
GPIO_LIB = None
lgpio = None
GPIO = None
_gpio_handle = None  # Shared handle for lgpio

try:
    import lgpio
    GPIO_LIB = 'lgpio'
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_LIB = 'rpigpio'
    except ImportError:
        GPIO_LIB = None
        print("Warning: No GPIO library available")

try:
    import smbus2
    USE_DIRECT_I2C = False
except Exception as e:
    smbus2 = None
    print(f"Warning: smbus2 not available: {e}")
    print("  Attempting to use direct I2C implementation...")
    try:
        import os
        import sys
        # Get the directory where core module is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        i2c_path = os.path.join(parent_dir, 'core', 'i2c_direct.py')
        
        if os.path.exists(i2c_path):
            # Import directly from file path
            import importlib.util
            spec = importlib.util.spec_from_file_location("i2c_direct", i2c_path)
            i2c_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(i2c_module)
            DirectSMBus = i2c_module.SMBus
            smbus2 = type('Module', (), {'SMBus': DirectSMBus})()
            USE_DIRECT_I2C = True
            print("  ✅ Using direct I2C implementation (no ctypes required)")
        else:
            raise ImportError(f"i2c_direct.py not found at {i2c_path}")
    except Exception as e2:
        print(f"  ❌ Direct I2C also failed: {e2}")
        USE_DIRECT_I2C = False

try:
    from config import (
        # Ultrasonic
        ULTRASONIC_TRIGGER, ULTRASONIC_ECHO, ULTRASONIC_MAX_DISTANCE, ULTRASONIC_TIMEOUT,
        # I2C
        TCS34725_ADDRESS, MPU6050_ADDRESS, I2C_BUS,
        # GPS
        GPS_SERIAL_PORT, GPS_BAUDRATE, GPS_TIMEOUT,
        # Load Cell
        HX711_DATA_PIN, HX711_CLOCK_PIN, HX711_CALIBRATION_FACTOR,
        # Float Switch
        FLOAT_SWITCH_PIN,
        # Settings
        DEBUG_MODE, SIMULATE_SENSORS, SENSOR_READ_TIMEOUT, MAX_SENSOR_RETRIES
    )
except ImportError as e:
    print(f"Warning: Could not import from config: {e}")
    # Set defaults if config import fails
    ULTRASONIC_TRIGGER = 20
    ULTRASONIC_ECHO = 21
    ULTRASONIC_MAX_DISTANCE = 400
    ULTRASONIC_TIMEOUT = 0.1
    TCS34725_ADDRESS = 0x29
    MPU6050_ADDRESS = 0x68
    I2C_BUS = 1
    GPS_SERIAL_PORT = '/dev/ttyAMA0'
    GPS_BAUDRATE = 9600
    GPS_TIMEOUT = 1.0
    HX711_DATA_PIN = 8
    HX711_CLOCK_PIN = 7
    HX711_CALIBRATION_FACTOR = 1.0
    FLOAT_SWITCH_PIN = 11
    DEBUG_MODE = True
    SIMULATE_SENSORS = False
    SENSOR_READ_TIMEOUT = 1.0
    MAX_SENSOR_RETRIES = 3


class ColorSensor:
    """TCS34725 RGB Color Sensor for algae detection"""
    
    def __init__(self):
        """Initialize TCS34725 color sensor"""
        self.initialized = False
        self.bus = None
        
        if SIMULATE_SENSORS:
            self.initialized = True
            return
        
        if smbus2 is None:
            print("Warning: smbus2 not available, color sensor disabled")
            return
        
        try:
            self.bus = smbus2.SMBus(I2C_BUS)
            
            # Enable the sensor (0x80 = command bit, 0x00 = ENABLE register)
            # 0x03 = Power ON + RGBC enable
            self.bus.write_byte_data(TCS34725_ADDRESS, 0x80 | 0x00, 0x03)
            time.sleep(0.003)  # Wait 2.4ms for integration
            
            # Set integration time (0x01 = ATIME register, 0xFF = 2.4ms)
            self.bus.write_byte_data(TCS34725_ADDRESS, 0x80 | 0x01, 0xFF)
            
            # Set gain (0x0F = CONTROL register, 0x00 = 1x gain)
            self.bus.write_byte_data(TCS34725_ADDRESS, 0x80 | 0x0F, 0x00)
            
            self.initialized = True
            if DEBUG_MODE:
                print("Color sensor initialized")
                
        except Exception as e:
            print(f"Error initializing color sensor: {e}")
            self.initialized = False
    
    def read(self):
        """
        Read RGB color values
        
        Returns:
            dict: {'r': int, 'g': int, 'b': int, 'clear': int} or None on error
        """
        if SIMULATE_SENSORS:
            # Simulate algae-like green color
            return {'r': 80, 'g': 150, 'b': 70, 'clear': 300}
        
        if not self.initialized:
            return None
        
        try:
            # Read color data (16-bit values)
            # Register addresses: Clear=0x14, Red=0x16, Green=0x18, Blue=0x1A
            clear = self.bus.read_word_data(TCS34725_ADDRESS, 0x80 | 0x14)
            red = self.bus.read_word_data(TCS34725_ADDRESS, 0x80 | 0x16)
            green = self.bus.read_word_data(TCS34725_ADDRESS, 0x80 | 0x18)
            blue = self.bus.read_word_data(TCS34725_ADDRESS, 0x80 | 0x1A)
            
            # Normalize to 0-255 range
            if clear > 0:
                r = int((red / clear) * 255)
                g = int((green / clear) * 255)
                b = int((blue / clear) * 255)
            else:
                r = g = b = 0
            
            return {
                'r': min(255, max(0, r)),
                'g': min(255, max(0, g)),
                'b': min(255, max(0, b)),
                'clear': clear
            }
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading color sensor: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.bus and self.initialized:
                # Disable sensor
                self.bus.write_byte_data(TCS34725_ADDRESS, 0x80 | 0x00, 0x00)
                self.bus.close()
        except:
            pass


class UltrasonicSensor:
    """JSN-SR04T Ultrasonic Distance Sensor"""
    
    def __init__(self):
        """Initialize ultrasonic sensor"""
        global _gpio_handle
        self.initialized = False
        self.gpio_handle = None
        
        if SIMULATE_SENSORS:
            self.initialized = True
            return
        
        if GPIO_LIB is None:
            print("Warning: GPIO not available, ultrasonic sensor disabled")
            return
        
        try:
            if GPIO_LIB == 'lgpio':
                # Use shared handle or create new one
                if _gpio_handle is None:
                    _gpio_handle = lgpio.gpiochip_open(0)
                self.gpio_handle = _gpio_handle
                
                lgpio.gpio_claim_output(self.gpio_handle, ULTRASONIC_TRIGGER)
                lgpio.gpio_claim_input(self.gpio_handle, ULTRASONIC_ECHO)
                lgpio.gpio_write(self.gpio_handle, ULTRASONIC_TRIGGER, 0)
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(ULTRASONIC_TRIGGER, GPIO.OUT)
                GPIO.setup(ULTRASONIC_ECHO, GPIO.IN)
                GPIO.output(ULTRASONIC_TRIGGER, GPIO.LOW)
            
            time.sleep(0.1)
            
            self.initialized = True
            if DEBUG_MODE:
                print("Ultrasonic sensor initialized")
                
        except Exception as e:
            print(f"Error initializing ultrasonic sensor: {e}")
            self.initialized = False
    
    def read(self):
        """
        Read distance in centimeters
        
        Returns:
            float: Distance in cm, or None on error
        """
        if SIMULATE_SENSORS:
            return 150.0  # Simulate 150cm distance
        
        if not self.initialized:
            return None
        
        try:
            if GPIO_LIB == 'lgpio':
                # Send trigger pulse
                lgpio.gpio_write(self.gpio_handle, ULTRASONIC_TRIGGER, 1)
                time.sleep(0.00001)  # 10 microseconds
                lgpio.gpio_write(self.gpio_handle, ULTRASONIC_TRIGGER, 0)
                
                # Wait for echo
                timeout_start = time.time()
                while lgpio.gpio_read(self.gpio_handle, ULTRASONIC_ECHO) == 0:
                    pulse_start = time.time()
                    if pulse_start - timeout_start > ULTRASONIC_TIMEOUT:
                        return None
                
                timeout_start = time.time()
                while lgpio.gpio_read(self.gpio_handle, ULTRASONIC_ECHO) == 1:
                    pulse_end = time.time()
                    if pulse_end - timeout_start > ULTRASONIC_TIMEOUT:
                        return None
            else:
                # Send trigger pulse
                GPIO.output(ULTRASONIC_TRIGGER, GPIO.HIGH)
                time.sleep(0.00001)  # 10 microseconds
                GPIO.output(ULTRASONIC_TRIGGER, GPIO.LOW)
                
                # Wait for echo
                timeout_start = time.time()
                while GPIO.input(ULTRASONIC_ECHO) == GPIO.LOW:
                    pulse_start = time.time()
                    if pulse_start - timeout_start > ULTRASONIC_TIMEOUT:
                        return None
                
                timeout_start = time.time()
                while GPIO.input(ULTRASONIC_ECHO) == GPIO.HIGH:
                    pulse_end = time.time()
                    if pulse_end - timeout_start > ULTRASONIC_TIMEOUT:
                        return None
            
            # Calculate distance (speed of sound = 34300 cm/s)
            pulse_duration = pulse_end - pulse_start
            distance = (pulse_duration * 34300) / 2
            
            if distance > ULTRASONIC_MAX_DISTANCE:
                return ULTRASONIC_MAX_DISTANCE
            
            return round(distance, 2)
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading ultrasonic sensor: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        pass  # GPIO cleanup handled by motor controller


class IMUSensor:
    """MPU6050 IMU (Accelerometer + Gyroscope)"""
    
    def __init__(self):
        """Initialize MPU6050 IMU"""
        self.initialized = False
        self.bus = None
        
        if SIMULATE_SENSORS:
            self.initialized = True
            return
        
        if smbus2 is None:
            print("Warning: smbus2 not available, IMU disabled")
            return
        
        try:
            self.bus = smbus2.SMBus(I2C_BUS)
            
            # Wake up MPU6050 (write 0 to PWR_MGMT_1 register)
            self.bus.write_byte_data(MPU6050_ADDRESS, 0x6B, 0x00)
            time.sleep(0.1)
            
            self.initialized = True
            if DEBUG_MODE:
                print("IMU sensor initialized")
                
        except Exception as e:
            print(f"Error initializing IMU: {e}")
            self.initialized = False
    
    def _read_raw_data(self, addr):
        """Read raw 16-bit data from MPU6050"""
        high = self.bus.read_byte_data(MPU6050_ADDRESS, addr)
        low = self.bus.read_byte_data(MPU6050_ADDRESS, addr + 1)
        value = (high << 8) | low
        
        # Convert to signed value
        if value > 32768:
            value -= 65536
        
        return value
    
    def read(self):
        """
        Read accelerometer and gyroscope data
        
        Returns:
            dict: {'accel': {'x', 'y', 'z'}, 'gyro': {'x', 'y', 'z'}} or None
        """
        if SIMULATE_SENSORS:
            return {
                'accel': {'x': 0.0, 'y': 0.0, 'z': 9.8},
                'gyro': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            }
        
        if not self.initialized:
            return None
        
        try:
            # Read accelerometer data (registers 0x3B to 0x40)
            accel_x = self._read_raw_data(0x3B) / 16384.0  # ±2g range
            accel_y = self._read_raw_data(0x3D) / 16384.0
            accel_z = self._read_raw_data(0x3F) / 16384.0
            
            # Read gyroscope data (registers 0x43 to 0x48)
            gyro_x = self._read_raw_data(0x43) / 131.0  # ±250°/s range
            gyro_y = self._read_raw_data(0x45) / 131.0
            gyro_z = self._read_raw_data(0x47) / 131.0
            
            return {
                'accel': {
                    'x': round(accel_x, 3),
                    'y': round(accel_y, 3),
                    'z': round(accel_z, 3)
                },
                'gyro': {
                    'x': round(gyro_x, 3),
                    'y': round(gyro_y, 3),
                    'z': round(gyro_z, 3)
                }
            }
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading IMU: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.bus and self.initialized:
                self.bus.close()
        except:
            pass


class GPSSensor:
    """NEO-6M GPS Module"""
    
    def __init__(self):
        """Initialize GPS module"""
        self.initialized = False
        self.serial = None
        
        if SIMULATE_SENSORS:
            self.initialized = True
            return
        
        try:
            self.serial = serial.Serial(
                GPS_SERIAL_PORT,
                baudrate=GPS_BAUDRATE,
                timeout=GPS_TIMEOUT
            )
            
            self.initialized = True
            if DEBUG_MODE:
                print("GPS sensor initialized")
                
        except Exception as e:
            print(f"Error initializing GPS: {e}")
            self.initialized = False
    
    def _parse_nmea(self, sentence):
        """Parse NMEA sentence (GPGGA format)"""
        try:
            parts = sentence.split(',')
            
            if parts[0] == '$GPGGA' and len(parts) >= 10:
                # Latitude
                lat = float(parts[2][:2]) + float(parts[2][2:]) / 60
                if parts[3] == 'S':
                    lat = -lat
                
                # Longitude
                lon = float(parts[4][:3]) + float(parts[4][3:]) / 60
                if parts[5] == 'W':
                    lon = -lon
                
                # Altitude
                alt = float(parts[9]) if parts[9] else 0.0
                
                return {
                    'latitude': round(lat, 6),
                    'longitude': round(lon, 6),
                    'altitude': round(alt, 2)
                }
        except:
            pass
        
        return None
    
    def read(self):
        """
        Read GPS coordinates
        
        Returns:
            dict: {'latitude', 'longitude', 'altitude'} or None
        """
        if SIMULATE_SENSORS:
            return {
                'latitude': 14.5995,  # Example: Philippines
                'longitude': 120.9842,
                'altitude': 10.0
            }
        
        if not self.initialized:
            return None
        
        try:
            # Read lines until we get a valid GPGGA sentence
            for _ in range(10):  # Try up to 10 lines
                line = self.serial.readline().decode('ascii', errors='ignore').strip()
                
                if line.startswith('$GPGGA'):
                    result = self._parse_nmea(line)
                    if result:
                        return result
            
            return None
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading GPS: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.serial and self.initialized:
                self.serial.close()
        except:
            pass


class LoadCellSensor:
    """HX711 Load Cell Amplifier for weight measurement"""
    
    def __init__(self):
        """Initialize HX711 load cell"""
        global _gpio_handle
        self.initialized = False
        self.offset = 0
        self.gpio_handle = None
        
        if SIMULATE_SENSORS:
            self.initialized = True
            return
        
        if GPIO_LIB is None:
            print("Warning: GPIO not available, load cell disabled")
            return
        
        try:
            if GPIO_LIB == 'lgpio':
                # Use shared handle or create new one
                if _gpio_handle is None:
                    _gpio_handle = lgpio.gpiochip_open(0)
                self.gpio_handle = _gpio_handle
                
                lgpio.gpio_claim_input(self.gpio_handle, HX711_DATA_PIN)
                lgpio.gpio_claim_output(self.gpio_handle, HX711_CLOCK_PIN)
                lgpio.gpio_write(self.gpio_handle, HX711_CLOCK_PIN, 0)
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(HX711_DATA_PIN, GPIO.IN)
                GPIO.setup(HX711_CLOCK_PIN, GPIO.OUT)
                GPIO.output(HX711_CLOCK_PIN, GPIO.LOW)
            
            # Tare (zero) the scale
            self.tare()
            
            self.initialized = True
            if DEBUG_MODE:
                print("Load cell initialized")
                
        except Exception as e:
            print(f"Error initializing load cell: {e}")
            self.initialized = False
    
    def _read_raw(self):
        """Read raw 24-bit value from HX711"""
        if not self.initialized or GPIO_LIB is None:
            return 0
        
        try:
            if GPIO_LIB == 'lgpio':
                # Wait for data ready (DATA pin goes LOW)
                timeout = time.time() + 1.0
                while lgpio.gpio_read(self.gpio_handle, HX711_DATA_PIN) == 1:
                    if time.time() > timeout:
                        return 0
                
                # Read 24 bits
                value = 0
                for _ in range(24):
                    lgpio.gpio_write(self.gpio_handle, HX711_CLOCK_PIN, 1)
                    value = (value << 1) | lgpio.gpio_read(self.gpio_handle, HX711_DATA_PIN)
                    lgpio.gpio_write(self.gpio_handle, HX711_CLOCK_PIN, 0)
                
                # One more pulse to set gain to 128 for next reading
                lgpio.gpio_write(self.gpio_handle, HX711_CLOCK_PIN, 1)
                lgpio.gpio_write(self.gpio_handle, HX711_CLOCK_PIN, 0)
            else:
                # Wait for data ready (DATA pin goes LOW)
                timeout = time.time() + 1.0
                while GPIO.input(HX711_DATA_PIN) == GPIO.HIGH:
                    if time.time() > timeout:
                        return 0
                
                # Read 24 bits
                value = 0
                for _ in range(24):
                    GPIO.output(HX711_CLOCK_PIN, GPIO.HIGH)
                    value = (value << 1) | GPIO.input(HX711_DATA_PIN)
                    GPIO.output(HX711_CLOCK_PIN, GPIO.LOW)
                
                # One more pulse to set gain to 128 for next reading
                GPIO.output(HX711_CLOCK_PIN, GPIO.HIGH)
                GPIO.output(HX711_CLOCK_PIN, GPIO.LOW)
            
            # Convert to signed 24-bit
            if value & 0x800000:
                value -= 0x1000000
            
            return value
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading HX711 raw: {e}")
            return 0
    
    def tare(self, samples=10):
        """Zero the scale by reading current weight as offset"""
        if not self.initialized:
            return
        
        total = 0
        for _ in range(samples):
            total += self._read_raw()
            time.sleep(0.1)
        
        self.offset = total / samples
    
    def read(self):
        """
        Read weight in kilograms
        
        Returns:
            float: Weight in kg, or None on error
        """
        if SIMULATE_SENSORS:
            return 2.5  # Simulate 2.5 kg collected
        
        if not self.initialized:
            return None
        
        try:
            raw = self._read_raw()
            weight = (raw - self.offset) / HX711_CALIBRATION_FACTOR
            return round(max(0, weight), 3)  # Ensure non-negative
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading load cell: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        pass  # GPIO cleanup handled by motor controller


class FloatSwitch:
    """Float Switch for water level detection"""
    
    def __init__(self):
        """Initialize float switch"""
        global _gpio_handle
        self.initialized = False
        self.gpio_handle = None
        
        if SIMULATE_SENSORS:
            self.initialized = True
            return
        
        if GPIO_LIB is None:
            print("Warning: GPIO not available, float switch disabled")
            return
        
        try:
            if GPIO_LIB == 'lgpio':
                # Use shared handle or create new one
                if _gpio_handle is None:
                    _gpio_handle = lgpio.gpiochip_open(0)
                self.gpio_handle = _gpio_handle
                
                # Claim as input with pull-up
                lgpio.gpio_claim_input(self.gpio_handle, FLOAT_SWITCH_PIN, lgpio.SET_PULL_UP)
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(FLOAT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.initialized = True
            if DEBUG_MODE:
                print("Float switch initialized")
                
        except Exception as e:
            print(f"Error initializing float switch: {e}")
            self.initialized = False
    
    def read(self):
        """
        Read water level status
        
        Returns:
            bool: True if water present, False if no water, None on error
        """
        if SIMULATE_SENSORS:
            return True  # Simulate water present
        
        if not self.initialized:
            return None
        
        try:
            if GPIO_LIB == 'lgpio':
                # LOW = water present, HIGH = no water (with pull-up resistor)
                return lgpio.gpio_read(self.gpio_handle, FLOAT_SWITCH_PIN) == 0
            else:
                # LOW = water present, HIGH = no water (with pull-up resistor)
                return GPIO.input(FLOAT_SWITCH_PIN) == GPIO.LOW
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading float switch: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        pass  # GPIO cleanup handled by motor controller


# Test function for standalone testing
if __name__ == "__main__":
    print("Testing all sensors...\n")
    
    # Initialize sensors
    color = ColorSensor()
    ultrasonic = UltrasonicSensor()
    imu = IMUSensor()
    gps = GPSSensor()
    load_cell = LoadCellSensor()
    float_switch = FloatSwitch()
    
    # Test each sensor
    print("1. Color Sensor:")
    color_data = color.read()
    print(f"   {color_data}\n")
    
    print("2. Ultrasonic Sensor:")
    distance = ultrasonic.read()
    print(f"   Distance: {distance} cm\n")
    
    print("3. IMU Sensor:")
    imu_data = imu.read()
    print(f"   {imu_data}\n")
    
    print("4. GPS Sensor:")
    gps_data = gps.read()
    print(f"   {gps_data}\n")
    
    print("5. Load Cell:")
    weight = load_cell.read()
    print(f"   Weight: {weight} kg\n")
    
    print("6. Float Switch:")
    water_level = float_switch.read()
    print(f"   Water present: {water_level}\n")
    
    # Cleanup
    color.cleanup()
    ultrasonic.cleanup()
    imu.cleanup()
    gps.cleanup()
    load_cell.cleanup()
    float_switch.cleanup()
    
    print("Test complete!")

