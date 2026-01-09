"""
Motor Control Module for AMLAC Robot
Handles paddle wheel motors (L298N) and conveyor belt motor (L298N)

Updated for Raspberry Pi 5 compatibility using lgpio instead of RPi.GPIO
"""

import time

# Try lgpio first (Raspberry Pi 5), then fall back to RPi.GPIO (older Pi)
GPIO_LIB = None
lgpio = None
GPIO = None

try:
    import lgpio
    GPIO_LIB = 'lgpio'
    print("Using lgpio for GPIO control (Raspberry Pi 5 compatible)")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_LIB = 'rpigpio'
        print("Using RPi.GPIO for GPIO control")
    except ImportError:
        print("Warning: No GPIO library available. Using simulation mode.")
        GPIO_LIB = None

from config import (
    MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_LEFT_PWM,
    MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, MOTOR_RIGHT_PWM,
    CONVEYOR_IN1, CONVEYOR_IN2, CONVEYOR_PWM,
    PWM_FREQUENCY,
    PADDLE_DEFAULT_SPEED, PADDLE_MAX_SPEED,
    CONVEYOR_DEFAULT_SPEED, CONVEYOR_MAX_SPEED,
    DEBUG_MODE,
    SIMULATE_SENSORS
)


class MotorController:
    """
    Controls all motors for the AMLAC robot:
    - Left and right paddle wheels (2x 12V DC motors, 78 RPM)
    - Conveyor belt (1x 6-12V DC motor, 188 RPM)
    
    Supports both lgpio (Raspberry Pi 5) and RPi.GPIO (older Pi models)
    """
    
    def __init__(self):
        """Initialize motor controller and setup GPIO pins"""
        self.initialized = False
        self.gpio_handle = None  # For lgpio
        self.left_pwm = None
        self.right_pwm = None
        self.conveyor_pwm = None
        self.current_state = "stopped"
        
        # Current duty cycles (for lgpio)
        self.left_duty = 0
        self.right_duty = 0
        self.conveyor_duty = 0
        
        # Skip GPIO setup entirely if SIMULATE_SENSORS is True or no GPIO library
        if SIMULATE_SENSORS or GPIO_LIB is None:
            print("Motor controller running in simulation mode")
            self.initialized = True
            return
        
        try:
            if GPIO_LIB == 'lgpio':
                self._init_lgpio()
            else:
                self._init_rpigpio()
                
        except Exception as e:
            print(f"Error initializing motor controller: {e}")
            self.initialized = False
    
    def _init_lgpio(self):
        """Initialize motors using lgpio (Raspberry Pi 5)"""
        # Open GPIO chip
        self.gpio_handle = lgpio.gpiochip_open(0)
        
        # Setup all motor pins as outputs
        all_pins = [
            MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, MOTOR_LEFT_PWM,
            MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, MOTOR_RIGHT_PWM,
            CONVEYOR_IN1, CONVEYOR_IN2, CONVEYOR_PWM
        ]
        
        for pin in all_pins:
            lgpio.gpio_claim_output(self.gpio_handle, pin)
            lgpio.gpio_write(self.gpio_handle, pin, 0)
        
        # Initialize all motors to stopped state
        self.stop()
        self.stop_conveyor()
        
        self.initialized = True
        if DEBUG_MODE:
            print("Motor controller initialized successfully (lgpio)")
    
    def _init_rpigpio(self):
        """Initialize motors using RPi.GPIO (older Pi models)"""
        # Setup GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup left paddle wheel
        GPIO.setup(MOTOR_LEFT_IN1, GPIO.OUT)
        GPIO.setup(MOTOR_LEFT_IN2, GPIO.OUT)
        GPIO.setup(MOTOR_LEFT_PWM, GPIO.OUT)
        self.left_pwm = GPIO.PWM(MOTOR_LEFT_PWM, PWM_FREQUENCY)
        self.left_pwm.start(0)
        
        # Setup right paddle wheel
        GPIO.setup(MOTOR_RIGHT_IN1, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_IN2, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_PWM, GPIO.OUT)
        self.right_pwm = GPIO.PWM(MOTOR_RIGHT_PWM, PWM_FREQUENCY)
        self.right_pwm.start(0)
        
        # Setup conveyor belt
        GPIO.setup(CONVEYOR_IN1, GPIO.OUT)
        GPIO.setup(CONVEYOR_IN2, GPIO.OUT)
        GPIO.setup(CONVEYOR_PWM, GPIO.OUT)
        self.conveyor_pwm = GPIO.PWM(CONVEYOR_PWM, PWM_FREQUENCY)
        self.conveyor_pwm.start(0)
        
        # Initialize all motors to stopped state
        self.stop()
        self.stop_conveyor()
        
        self.initialized = True
        if DEBUG_MODE:
            print("Motor controller initialized successfully (RPi.GPIO)")
    
    def _gpio_write(self, pin, value):
        """Write to a GPIO pin (abstraction layer)"""
        if SIMULATE_SENSORS or GPIO_LIB is None:
            return
        
        if GPIO_LIB == 'lgpio':
            lgpio.gpio_write(self.gpio_handle, pin, value)
        else:
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
    
    def _set_pwm(self, pin, duty_cycle, pwm_obj=None):
        """
        Set PWM duty cycle (abstraction layer)
        
        Args:
            pin: GPIO pin number
            duty_cycle: Duty cycle 0-100%
            pwm_obj: RPi.GPIO PWM object (only used with RPi.GPIO)
        """
        if SIMULATE_SENSORS or GPIO_LIB is None:
            return
        
        if GPIO_LIB == 'lgpio':
            # lgpio.tx_pwm(handle, pin, frequency, duty_cycle)
            # duty_cycle is 0-100 for lgpio
            lgpio.tx_pwm(self.gpio_handle, pin, PWM_FREQUENCY, duty_cycle)
        else:
            if pwm_obj:
                pwm_obj.ChangeDutyCycle(duty_cycle)
    
    def _set_motor_direction(self, in1_pin, in2_pin, direction):
        """
        Set motor direction using IN1 and IN2 pins
        
        Args:
            in1_pin: GPIO pin for IN1
            in2_pin: GPIO pin for IN2
            direction: 'forward', 'backward', or 'stop'
        """
        if SIMULATE_SENSORS or GPIO_LIB is None:
            return
        
        if direction == 'forward':
            self._gpio_write(in1_pin, 1)
            self._gpio_write(in2_pin, 0)
        elif direction == 'backward':
            self._gpio_write(in1_pin, 0)
            self._gpio_write(in2_pin, 1)
        else:  # stop
            self._gpio_write(in1_pin, 0)
            self._gpio_write(in2_pin, 0)
    
    def _clamp_speed(self, speed, max_speed):
        """Ensure speed is within valid range (0-max_speed)"""
        return max(0, min(speed, max_speed))
    
    def _speed_to_duty(self, speed):
        """Convert 0-255 speed to 0-100 duty cycle"""
        return (speed / 255.0) * 100.0
    
    def move_forward(self, speed=None):
        """
        Move robot forward using both paddle wheels
        
        Args:
            speed: PWM value (0-255), defaults to PADDLE_DEFAULT_SPEED
        """
        if not self.initialized:
            return False
        
        speed = speed or PADDLE_DEFAULT_SPEED
        speed = self._clamp_speed(speed, PADDLE_MAX_SPEED)
        duty = self._speed_to_duty(speed)
        
        try:
            # Set both motors to forward
            self._set_motor_direction(MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, 'forward')
            self._set_motor_direction(MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, 'forward')
            
            # Set PWM speed
            self._set_pwm(MOTOR_LEFT_PWM, duty, self.left_pwm)
            self._set_pwm(MOTOR_RIGHT_PWM, duty, self.right_pwm)
            
            self.left_duty = duty
            self.right_duty = duty
            self.current_state = f"forward_speed_{speed}"
            
            if DEBUG_MODE:
                print(f"Moving forward at speed {speed}")
            return True
            
        except Exception as e:
            print(f"Error moving forward: {e}")
            return False
    
    def move_backward(self, speed=None):
        """
        Move robot backward using both paddle wheels
        
        Args:
            speed: PWM value (0-255), defaults to PADDLE_DEFAULT_SPEED
        """
        if not self.initialized:
            return False
        
        speed = speed or PADDLE_DEFAULT_SPEED
        speed = self._clamp_speed(speed, PADDLE_MAX_SPEED)
        duty = self._speed_to_duty(speed)
        
        try:
            # Set both motors to backward
            self._set_motor_direction(MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, 'backward')
            self._set_motor_direction(MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, 'backward')
            
            # Set PWM speed
            self._set_pwm(MOTOR_LEFT_PWM, duty, self.left_pwm)
            self._set_pwm(MOTOR_RIGHT_PWM, duty, self.right_pwm)
            
            self.left_duty = duty
            self.right_duty = duty
            self.current_state = f"backward_speed_{speed}"
            
            if DEBUG_MODE:
                print(f"Moving backward at speed {speed}")
            return True
            
        except Exception as e:
            print(f"Error moving backward: {e}")
            return False
    
    def turn_left(self, speed=None):
        """
        Turn robot left (right wheel forward, left wheel backward/stopped)
        
        Args:
            speed: PWM value (0-255), defaults to PADDLE_DEFAULT_SPEED
        """
        if not self.initialized:
            return False
        
        speed = speed or PADDLE_DEFAULT_SPEED
        speed = self._clamp_speed(speed, PADDLE_MAX_SPEED)
        duty = self._speed_to_duty(speed)
        
        try:
            # Left wheel backward (or stopped), right wheel forward
            self._set_motor_direction(MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, 'backward')
            self._set_motor_direction(MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, 'forward')
            
            # Set PWM speed
            self._set_pwm(MOTOR_LEFT_PWM, duty, self.left_pwm)
            self._set_pwm(MOTOR_RIGHT_PWM, duty, self.right_pwm)
            
            self.left_duty = duty
            self.right_duty = duty
            self.current_state = f"turn_left_speed_{speed}"
            
            if DEBUG_MODE:
                print(f"Turning left at speed {speed}")
            return True
            
        except Exception as e:
            print(f"Error turning left: {e}")
            return False
    
    def turn_right(self, speed=None):
        """
        Turn robot right (left wheel forward, right wheel backward/stopped)
        
        Args:
            speed: PWM value (0-255), defaults to PADDLE_DEFAULT_SPEED
        """
        if not self.initialized:
            return False
        
        speed = speed or PADDLE_DEFAULT_SPEED
        speed = self._clamp_speed(speed, PADDLE_MAX_SPEED)
        duty = self._speed_to_duty(speed)
        
        try:
            # Left wheel forward, right wheel backward (or stopped)
            self._set_motor_direction(MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, 'forward')
            self._set_motor_direction(MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, 'backward')
            
            # Set PWM speed
            self._set_pwm(MOTOR_LEFT_PWM, duty, self.left_pwm)
            self._set_pwm(MOTOR_RIGHT_PWM, duty, self.right_pwm)
            
            self.left_duty = duty
            self.right_duty = duty
            self.current_state = f"turn_right_speed_{speed}"
            
            if DEBUG_MODE:
                print(f"Turning right at speed {speed}")
            return True
            
        except Exception as e:
            print(f"Error turning right: {e}")
            return False
    
    def stop(self):
        """Stop both paddle wheel motors"""
        if not self.initialized:
            return False
        
        try:
            # Stop both motors
            self._set_motor_direction(MOTOR_LEFT_IN1, MOTOR_LEFT_IN2, 'stop')
            self._set_motor_direction(MOTOR_RIGHT_IN1, MOTOR_RIGHT_IN2, 'stop')
            
            # Set PWM to 0
            self._set_pwm(MOTOR_LEFT_PWM, 0, self.left_pwm)
            self._set_pwm(MOTOR_RIGHT_PWM, 0, self.right_pwm)
            
            self.left_duty = 0
            self.right_duty = 0
            self.current_state = "stopped"
            
            if DEBUG_MODE:
                print("Paddle wheels stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping motors: {e}")
            return False
    
    def start_conveyor(self, speed=None):
        """
        Start conveyor belt motor for algae collection
        
        Args:
            speed: PWM value (0-255), defaults to CONVEYOR_DEFAULT_SPEED
        """
        if not self.initialized:
            return False
        
        speed = speed or CONVEYOR_DEFAULT_SPEED
        speed = self._clamp_speed(speed, CONVEYOR_MAX_SPEED)
        duty = self._speed_to_duty(speed)
        
        try:
            # Set conveyor to forward
            self._set_motor_direction(CONVEYOR_IN1, CONVEYOR_IN2, 'forward')
            
            # Set PWM speed
            self._set_pwm(CONVEYOR_PWM, duty, self.conveyor_pwm)
            
            self.conveyor_duty = duty
            
            if DEBUG_MODE:
                print(f"Conveyor started at speed {speed}")
            return True
            
        except Exception as e:
            print(f"Error starting conveyor: {e}")
            return False
    
    def stop_conveyor(self):
        """Stop conveyor belt motor"""
        if not self.initialized:
            return False
        
        try:
            # Stop conveyor
            self._set_motor_direction(CONVEYOR_IN1, CONVEYOR_IN2, 'stop')
            
            # Set PWM to 0
            self._set_pwm(CONVEYOR_PWM, 0, self.conveyor_pwm)
            
            self.conveyor_duty = 0
            
            if DEBUG_MODE:
                print("Conveyor stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping conveyor: {e}")
            return False
    
    def get_state(self):
        """Return current motor state"""
        return self.current_state
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            self.stop()
            self.stop_conveyor()
            
            if not SIMULATE_SENSORS and GPIO_LIB is not None:
                if GPIO_LIB == 'lgpio':
                    if self.gpio_handle is not None:
                        # Stop all PWM
                        lgpio.tx_pwm(self.gpio_handle, MOTOR_LEFT_PWM, 0, 0)
                        lgpio.tx_pwm(self.gpio_handle, MOTOR_RIGHT_PWM, 0, 0)
                        lgpio.tx_pwm(self.gpio_handle, CONVEYOR_PWM, 0, 0)
                        lgpio.gpiochip_close(self.gpio_handle)
                        self.gpio_handle = None
                else:
                    if self.left_pwm:
                        self.left_pwm.stop()
                    if self.right_pwm:
                        self.right_pwm.stop()
                    if self.conveyor_pwm:
                        self.conveyor_pwm.stop()
                    GPIO.cleanup()
            
            if DEBUG_MODE:
                print("Motor controller cleanup complete")
                
        except Exception as e:
            print(f"Error during motor cleanup: {e}")


# Test function for standalone testing
if __name__ == "__main__":
    print("Testing Motor Controller...")
    controller = MotorController()
    
    if controller.initialized:
        print("\n1. Testing forward movement...")
        controller.move_forward(100)
        time.sleep(2)
        
        print("\n2. Testing backward movement...")
        controller.move_backward(100)
        time.sleep(2)
        
        print("\n3. Testing left turn...")
        controller.turn_left(80)
        time.sleep(1)
        
        print("\n4. Testing right turn...")
        controller.turn_right(80)
        time.sleep(1)
        
        print("\n5. Testing conveyor...")
        controller.start_conveyor(150)
        time.sleep(3)
        controller.stop_conveyor()
        
        print("\n6. Stopping all motors...")
        controller.stop()
        
        print("\nTest complete!")
    
    controller.cleanup()
