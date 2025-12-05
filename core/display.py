"""
LCD Display Module for AMLAC Robot
Handles 16x2 I2C LCD display for status information
"""

import time

try:
    import smbus2
except ImportError:
    smbus2 = None
    print("Warning: smbus2 not available")

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
            print("Warning: smbus2 not available, LCD disabled")
            return
        
        try:
            self.bus = smbus2.SMBus(I2C_BUS)
            
            # Initialize display
            self._lcd_init()
            
            # Show startup message
            self.clear()
            self.write_line("AMLAC Robot", 0)
            self.write_line("Initializing...", 1)
            
            self.initialized = True
            if DEBUG_MODE:
                print("LCD display initialized")
                
        except Exception as e:
            print(f"Error initializing LCD: {e}")
            self.initialized = False
    
    def _lcd_write(self, cmd):
        """Write a command to LCD"""
        try:
            self.bus.write_byte(LCD_ADDRESS, cmd)
            time.sleep(0.0001)
        except:
            pass
    
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
        """Initialize LCD in 4-bit mode"""
        self._lcd_write(0x03)
        self._lcd_write(0x03)
        self._lcd_write(0x03)
        self._lcd_write(0x02)
        
        self._lcd_write_byte(self.LCD_FUNCTIONSET | self.LCD_2LINE | self.LCD_5x8DOTS | self.LCD_4BITMODE)
        self._lcd_write_byte(self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYON)
        self._lcd_write_byte(self.LCD_CLEARDISPLAY)
        self._lcd_write_byte(self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT)
        time.sleep(0.2)
    
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
            time.sleep(0.002)
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
            
            # Set cursor position
            line_addr = 0x80 if line == 0 else 0xC0
            self._lcd_write_byte(line_addr)
            
            # Write characters
            for char in text:
                self._lcd_write_byte(ord(char), self.Rs)
            
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

