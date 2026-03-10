#!/usr/bin/env python3
"""
Motor Direction Test Script
Run this to check if both motors spin the same direction for forward movement.
"""

import time
import lgpio

# Import pin configuration from config.py
from config import (
    MOTOR_LEFT_IN1 as LEFT_IN1,
    MOTOR_LEFT_IN2 as LEFT_IN2,
    MOTOR_LEFT_PWM as LEFT_PWM,
    MOTOR_RIGHT_IN1 as RIGHT_IN1,
    MOTOR_RIGHT_IN2 as RIGHT_IN2,
    MOTOR_RIGHT_PWM as RIGHT_PWM
)

def main():
    print("=" * 50)
    print("  MOTOR DIRECTION TEST")
    print("=" * 50)
    print()
    print(f"  LEFT pins:  IN1={LEFT_IN1}, IN2={LEFT_IN2}, PWM={LEFT_PWM}")
    print(f"  RIGHT pins: IN1={RIGHT_IN1}, IN2={RIGHT_IN2}, PWM={RIGHT_PWM}")
    print()
    
    # Open GPIO
    h = lgpio.gpiochip_open(0)
    
    # Setup all pins as outputs
    pins = [LEFT_IN1, LEFT_IN2, LEFT_PWM, RIGHT_IN1, RIGHT_IN2, RIGHT_PWM]
    for pin in pins:
        lgpio.gpio_claim_output(h, pin)
        lgpio.gpio_write(h, pin, 0)
    
    try:
        # Test 1: Left motor only
        print("TEST 1: LEFT motor only")
        print("  Watch the LEFT wheel...")
        input("  Press ENTER to start...")
        
        lgpio.gpio_write(h, LEFT_IN1, 1)
        lgpio.gpio_write(h, LEFT_IN2, 0)
        lgpio.tx_pwm(h, LEFT_PWM, 1000, 40)  # 40% speed
        
        time.sleep(3)
        
        lgpio.tx_pwm(h, LEFT_PWM, 1000, 0)
        lgpio.gpio_write(h, LEFT_IN1, 0)
        lgpio.gpio_write(h, LEFT_IN2, 0)
        
        left_direction = input("  Which way did LEFT spin? (f=forward, b=backward): ").lower()
        print()
        
        # Test 2: Right motor only
        print("TEST 2: RIGHT motor only")
        print("  Watch the RIGHT wheel...")
        input("  Press ENTER to start...")
        
        lgpio.gpio_write(h, RIGHT_IN1, 1)
        lgpio.gpio_write(h, RIGHT_IN2, 0)
        lgpio.tx_pwm(h, RIGHT_PWM, 1000, 40)  # 40% speed
        
        time.sleep(3)
        
        lgpio.tx_pwm(h, RIGHT_PWM, 1000, 0)
        lgpio.gpio_write(h, RIGHT_IN1, 0)
        lgpio.gpio_write(h, RIGHT_IN2, 0)
        
        right_direction = input("  Which way did RIGHT spin? (f=forward, b=backward): ").lower()
        print()
        
        # Test 3: Both motors together
        print("TEST 3: BOTH motors together")
        print("  Robot should move FORWARD (straight)...")
        input("  Press ENTER to start...")
        
        lgpio.gpio_write(h, LEFT_IN1, 1)
        lgpio.gpio_write(h, LEFT_IN2, 0)
        lgpio.gpio_write(h, RIGHT_IN1, 1)
        lgpio.gpio_write(h, RIGHT_IN2, 0)
        lgpio.tx_pwm(h, LEFT_PWM, 1000, 40)
        lgpio.tx_pwm(h, RIGHT_PWM, 1000, 40)
        
        time.sleep(3)
        
        lgpio.tx_pwm(h, LEFT_PWM, 1000, 0)
        lgpio.tx_pwm(h, RIGHT_PWM, 1000, 0)
        lgpio.gpio_write(h, LEFT_IN1, 0)
        lgpio.gpio_write(h, LEFT_IN2, 0)
        lgpio.gpio_write(h, RIGHT_IN1, 0)
        lgpio.gpio_write(h, RIGHT_IN2, 0)
        
        print()
        print("=" * 50)
        print("  RESULTS")
        print("=" * 50)
        print(f"  LEFT motor spun:  {'FORWARD' if left_direction == 'f' else 'BACKWARD'}")
        print(f"  RIGHT motor spun: {'FORWARD' if right_direction == 'f' else 'BACKWARD'}")
        print()
        
        if left_direction == right_direction:
            print("  ✅ Both motors spin SAME direction - wiring is correct!")
            print("     If robot still pivots, check wheel mounting.")
        else:
            print("  ❌ Motors spin OPPOSITE directions - need to fix!")
            if left_direction == 'b':
                print("     FIX: Swap LEFT motor wires (OUT1 <-> OUT2 on L298N)")
                print("     Or tell me to reverse LEFT motor in software")
            else:
                print("     FIX: Swap RIGHT motor wires (OUT1 <-> OUT2 on L298N)")
                print("     Or tell me to reverse RIGHT motor in software")
        print()
        
    except KeyboardInterrupt:
        print("\nTest cancelled")
    
    finally:
        # Cleanup - stop all motors
        for pin in pins:
            lgpio.gpio_write(h, pin, 0)
        lgpio.gpiochip_close(h)
        print("Motors stopped, GPIO cleaned up")

if __name__ == "__main__":
    main()
