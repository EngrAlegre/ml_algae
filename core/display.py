"""
LCD Display Module for AMLAC Robot
Handles 16x2 I2C LCD display for status information
"""

import time

try:
    import smbus2
    SMBUS2_AVAILABLE = True
    USE_DIRECT_I2C = False
except Exception as e:
    smbus2 = None
    SMBUS2_AVAILABLE = False
    print(f"Warning: smbus2 not available: {e}")
    print("  Attempting to use direct I2C implementation...")
    try:
        import os
        import sys
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        i2c_path = os.path.join(current_dir, 'i2c_direct.py')
        
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
        LCD_ADDRESS,
        I2C_BUS,
        LCD_ROWS,
        LCD_COLS,
        DISPLAY_MODES,
        DISPLAY_ROTATE_INTERVAL,
        DEBUG_MODE,
        SIMULATE_SENSORS
    )
except ImportError as e:
    print(f"Warning: Could not import from config: {e}")
    # Set defaults if config import fails
    LCD_ADDRESS = 0x27
    I2C_BUS = 1
    LCD_ROWS = 2
    LCD_COLS = 16
    DISPLAY_MODES = ['algae', 'gps', 'weight', 'distance', 'status']
    DISPLAY_ROTATE_INTERVAL = 5.0
    DEBUG_MODE = True
    SIMULATE_SENSORS = False


class LCDDisplay:
    """
    Controls 16x2 I2C LCD display
    Rotates through different display modes to show various robot status information
    """
    
    # LCD Commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80
    
    # Flags for display entry mode
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00
    
    # Flags for display on/off control
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00
    
    # Flags for display/cursor shift
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00
    
    # Flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00
    
    # Flags for backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00
    
    En = 0b00000100  # Enable bit
    Rw = 0b00000010  # Read/Write bit
    Rs = 0b00000001  # Register select bit
    
    def __init__(self):
        """Initialize LCD display"""
        self.initialized = False
        self.bus = None
        self.current_mode_index = 0
        self.last_mode_change = time.time()
        
        if SIMULATE_SENSORS:
            self.initialized = True
            if DEBUG_MODE:
                print("LCD display running in simulation mode")
            return
        
        if smbus2 is None:
            print("Warning: I2C not available, LCD disabled")
            return
        
        try:
            self.bus = smbus2.SMBus(I2C_BUS)
            
            # Test I2C communication first
            try:
                self.bus.read_byte(LCD_ADDRESS)
                if DEBUG_MODE:
                    print(f"LCD I2C communication test successful at address 0x{LCD_ADDRESS:02x}")
            except Exception as e:
                print(f"Warning: Cannot communicate with LCD at 0x{LCD_ADDRESS:02x}: {e}")
                print("Check I2C address and connections")
            
            # Initialize display with robust sequence
            self._lcd_init()
            time.sleep(0.2)  # Extra settling time after init
            
            # Show startup message - try twice for reliability
            for attempt in range(2):
                self.clear()
                time.sleep(0.1)
                self.write_line("AMLAC Robot", 0)
                time.sleep(0.05)
                self.write_line("Initializing...", 1)
                time.sleep(0.1)
                
                # Verify by re-clearing and rewriting if first attempt
                if attempt == 0:
                    time.sleep(0.3)  # Let it display briefly
            
            self.initialized = True
            if DEBUG_MODE:
                print("LCD display initialized successfully")
                
        except Exception as e:
            print(f"Error initializing LCD: {e}")
            import traceback
            if DEBUG_MODE:
                traceback.print_exc()
            self.initialized = False
    
    def _lcd_write(self, cmd):
        """Write a command to LCD"""
        try:
            self.bus.write_byte(LCD_ADDRESS, cmd)
            time.sleep(0.0001)
        except Exception as e:
            if DEBUG_MODE:
                print(f"LCD write error: {e}")
    
    def _lcd_strobe(self, data):
        """Toggle enable pin"""
        self._lcd_write(data | self.En | self.LCD_BACKLIGHT)
        time.sleep(0.0005)
        self._lcd_write(((data & ~self.En) | self.LCD_BACKLIGHT))
        time.sleep(0.0001)
    
    def _lcd_write_four_bits(self, data):
        """Write 4 bits to LCD"""
        self._lcd_write(data | self.LCD_BACKLIGHT)
        self._lcd_strobe(data)
    
    def _lcd_write_byte(self, cmd, mode=0):
        """Write a byte to LCD in 4-bit mode"""
        self._lcd_write_four_bits(mode | (cmd & 0xF0))
        self._lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))
    
    def _lcd_init(self):
        """Initialize LCD in 4-bit mode with robust timing for cold boot"""
        # === CRITICAL: Wait for LCD to power up completely ===
        # HD44780 datasheet says wait at least 40ms after VCC rises to 4.5V
        # On cold boot, the LCD might take longer to stabilize
        time.sleep(0.2)  # 200ms - generous power-up time
        
        # Turn on backlight and let it stabilize
        self._lcd_write(self.LCD_BACKLIGHT)
        time.sleep(0.1)  # 100ms for backlight
        
        # === Hard Reset Sequence ===
        # Per HD44780 datasheet, we need to send 0x30 (8-bit mode) three times
        # with specific timing to ensure a clean reset from ANY state
        
        # First attempt - LCD might be in 4-bit or 8-bit mode, unknown state
        # Send 0x30 (upper nibble 0x3 for 8-bit mode command)
        self._lcd_write_four_bits(0x30)
        time.sleep(0.005)  # Wait at least 4.1ms
        
        # Second attempt
        self._lcd_write_four_bits(0x30)
        time.sleep(0.005)  # Wait at least 4.1ms (be generous)
        
        # Third attempt  
        self._lcd_write_four_bits(0x30)
        time.sleep(0.002)  # Wait at least 100us, give it 2ms
        
        # === Now switch to 4-bit mode ===
        # Send 0x20 (upper nibble 0x2 for 4-bit mode)
        self._lcd_write_four_bits(0x20)
        time.sleep(0.005)  # Wait for mode switch
        
        # === LCD is now in 4-bit mode, send full commands ===
        
        # Function set: 4-bit mode, 2 lines, 5x8 dots
        self._lcd_write_byte(self.LCD_FUNCTIONSET | self.LCD_2LINE | self.LCD_5x8DOTS | self.LCD_4BITMODE)
        time.sleep(0.005)
        
        # Display OFF first (clean state)
        self._lcd_write_byte(self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYOFF)
        time.sleep(0.005)
        
        # Clear display
        self._lcd_write_byte(self.LCD_CLEARDISPLAY)
        time.sleep(0.005)  # Clear command needs at least 1.52ms
        
        # Entry mode set: increment, no shift
        self._lcd_write_byte(self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT)
        time.sleep(0.005)
        
        # Return home (cursor to 0,0)
        self._lcd_write_byte(self.LCD_RETURNHOME)
        time.sleep(0.005)  # Return home needs at least 1.52ms
        
        # Display ON, cursor off, blink off
        self._lcd_write_byte(self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF)
        time.sleep(0.005)
        
        # Clear one more time for good measure
        self._lcd_write_byte(self.LCD_CLEARDISPLAY)
        time.sleep(0.005)
    
    def clear(self):
        """Clear display"""
        if SIMULATE_SENSORS:
            if DEBUG_MODE:
                print("[LCD] Clear")
            return True
        
        if not self.initialized:
            return False
        
        try:
            self._lcd_write_byte(self.LCD_CLEARDISPLAY)
            time.sleep(0.003)  # Clear command needs at least 1.52ms, give it more
            return True
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error clearing LCD: {e}")
            return False
    
    def write_line(self, text, line):
        """
        Write text to a specific line
        
        Args:
            text: Text to display (will be truncated to LCD_COLS)
            line: Line number (0 or 1)
        """
        if SIMULATE_SENSORS:
            if DEBUG_MODE:
                print(f"[LCD Line {line}] {text}")
            return True
        
        if not self.initialized or line >= LCD_ROWS:
            return False
        
        try:
            # Truncate or pad text to fit LCD width
            text = text[:LCD_COLS].ljust(LCD_COLS)
            
            # Set cursor position (DDRAM address)
            line_addr = 0x80 if line == 0 else 0xC0
            self._lcd_write_byte(line_addr)
            time.sleep(0.001)  # Small delay after setting cursor
            
            # Write characters
            for char in text:
                self._lcd_write_byte(ord(char), self.Rs)
                time.sleep(0.0001)  # Small delay between characters
            
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error writing to LCD: {e}")
            return False
    
    def display_algae_status(self, is_algae, confidence):
        """Display algae detection status"""
        self.clear()
        
        if is_algae:
            self.write_line("ALGAE: YES", 0)
        else:
            self.write_line("ALGAE: NO", 0)
        
        conf_percent = int(confidence * 100)
        self.write_line(f"CONF: {conf_percent}%", 1)
    
    def display_gps(self, latitude, longitude):
        """Display GPS coordinates"""
        self.clear()
        
        # Format coordinates (truncate for display)
        lat_str = f"LAT:{latitude:.4f}" if latitude else "LAT:N/A"
        lon_str = f"LON:{longitude:.4f}" if longitude else "LON:N/A"
        
        self.write_line(lat_str[:16], 0)
        self.write_line(lon_str[:16], 1)
    
    def display_weight(self, weight_kg):
        """Display collected weight"""
        self.clear()
        
        weight_str = f"{weight_kg:.2f} kg" if weight_kg is not None else "N/A"
        self.write_line(f"WEIGHT: {weight_str}", 0)
        self.write_line("COLLECTED", 1)
    
    def display_distance(self, distance_cm):
        """Display obstacle distance"""
        self.clear()
        
        dist_str = f"{distance_cm:.1f}" if distance_cm is not None else "N/A"
        self.write_line(f"DIST: {dist_str} cm", 0)
        
        if distance_cm is not None and distance_cm < 30:
            self.write_line("STATUS: WARNING", 1)
        else:
            self.write_line("STATUS: CLEAR", 1)
    
    def display_status(self, system_status, water_level=None):
        """Display system status"""
        self.clear()
        
        status_str = system_status[:16] if system_status else "OK"
        self.write_line(f"STATUS: {status_str}", 0)
        
        if water_level is not None:
            water_str = "WATER: YES" if water_level else "WATER: NO"
            self.write_line(water_str, 1)
        else:
            self.write_line("", 1)
    
    def update_display(self, robot_data):
        """
        Update display with robot data, rotating through modes
        
        Args:
            robot_data: Dictionary containing:
                - is_algae, ml_confidence
                - gps_latitude, gps_longitude
                - weight_kg
                - distance_cm
                - system_status
                - water_level
        """
        if not self.initialized:
            return False
        
        # Check if it's time to rotate display mode
        current_time = time.time()
        if current_time - self.last_mode_change >= DISPLAY_ROTATE_INTERVAL:
            self.current_mode_index = (self.current_mode_index + 1) % len(DISPLAY_MODES)
            self.last_mode_change = current_time
        
        # Display current mode
        mode = DISPLAY_MODES[self.current_mode_index]
        
        try:
            if mode == 'algae':
                self.display_algae_status(
                    robot_data.get('is_algae', False),
                    robot_data.get('ml_confidence', 0.0)
                )
            elif mode == 'gps':
                self.display_gps(
                    robot_data.get('gps_latitude'),
                    robot_data.get('gps_longitude')
                )
            elif mode == 'weight':
                self.display_weight(robot_data.get('weight_kg'))
            elif mode == 'distance':
                self.display_distance(robot_data.get('distance_cm'))
            elif mode == 'status':
                self.display_status(
                    robot_data.get('system_status', 'OK'),
                    robot_data.get('water_level')
                )
            
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error updating display: {e}")
            return False
    
    def show_message(self, line1, line2=""):
        """
        Show a custom message on the display
        
        Args:
            line1: Text for first line
            line2: Text for second line (optional)
        """
        self.clear()
        self.write_line(line1, 0)
        if line2:
            self.write_line(line2, 1)
    
    def reinit(self):
        """
        Reinitialize the LCD display
        Call this if display shows garbled text
        """
        if SIMULATE_SENSORS:
            return True
            
        if self.bus is None:
            return False
        
        try:
            if DEBUG_MODE:
                print("Reinitializing LCD display...")
            
            # Run full initialization again
            self._lcd_init()
            time.sleep(0.2)
            
            # Show a message to confirm it's working
            self.clear()
            time.sleep(0.1)
            self.write_line("LCD Reset OK", 0)
            time.sleep(0.5)
            self.clear()
            
            if DEBUG_MODE:
                print("LCD reinitialized successfully")
            
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reinitializing LCD: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.initialized and not SIMULATE_SENSORS:
                self.clear()
                self.show_message("AMLAC Robot", "Shutdown")
                time.sleep(1)
                self.clear()
                
                if self.bus:
                    self.bus.close()
            
            if DEBUG_MODE:
                print("LCD display cleanup complete")
                
        except Exception as e:
            print(f"Error during LCD cleanup: {e}")


# Test function for standalone testing
if __name__ == "__main__":
    print("Testing LCD Display...\n")
    
    # Initialize display
    display = LCDDisplay()
    
    if display.initialized:
        print("Display initialized successfully\n")
        
        # Test each display mode
        print("Testing display modes...\n")
        
        # Test data
        test_data = {
            'is_algae': True,
            'ml_confidence': 0.87,
            'gps_latitude': 14.5995,
            'gps_longitude': 120.9842,
            'weight_kg': 3.45,
            'distance_cm': 125.5,
            'system_status': 'NORMAL',
            'water_level': True
        }
        
        # Test each mode
        for mode in DISPLAY_MODES:
            print(f"Testing {mode} mode...")
            display.current_mode_index = DISPLAY_MODES.index(mode)
            display.update_display(test_data)
            time.sleep(3)
        
        # Test custom message
        print("\nTesting custom message...")
        display.show_message("Test Complete!", "All OK")
        time.sleep(2)
        
        print("\nTest complete!")
    
    else:
        print("Failed to initialize display")
    
    # Cleanup
    display.cleanup()

