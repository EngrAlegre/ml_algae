"""
Direct I2C communication using /dev/i2c-* files
This is an alternative to smbus2 that doesn't require ctypes
Provides SMBus-compatible interface
"""

import os
import struct
import fcntl
import time

# I2C bus operations (from linux/i2c-dev.h)
I2C_SLAVE = 0x0703
I2C_SMBUS = 0x0720
I2C_SMBUS_READ = 1
I2C_SMBUS_WRITE = 0
I2C_SMBUS_BYTE = 1
I2C_SMBUS_BYTE_DATA = 2
I2C_SMBUS_WORD_DATA = 3

class SMBus:
    """
    SMBus-compatible class for I2C communication
    Drop-in replacement for smbus2.SMBus that doesn't require ctypes
    """
    
    def __init__(self, bus_number):
        """
        Initialize I2C bus
        
        Args:
            bus_number: I2C bus number (typically 1 on Raspberry Pi)
        """
        self.bus_number = bus_number
        self.device_path = f"/dev/i2c-{bus_number}"
        self.file = None
        self.current_address = None
        
        if not os.path.exists(self.device_path):
            raise FileNotFoundError(f"I2C device {self.device_path} not found. Enable I2C in raspi-config.")
        
        try:
            self.file = open(self.device_path, 'rb+', buffering=0)
        except Exception as e:
            raise IOError(f"Cannot open I2C device {self.device_path}: {e}")
    
    def _set_address(self, address):
        """Set I2C slave address (internal method)"""
        if self.current_address != address:
            try:
                fcntl.ioctl(self.file.fileno(), I2C_SLAVE, address)
                self.current_address = address
            except Exception as e:
                raise IOError(f"Cannot set I2C address {address}: {e}")
    
    def write_byte(self, address, value):
        """Write a single byte to I2C device (smbus2 compatible)"""
        self._set_address(address)
        try:
            self.file.write(bytes([value]))
            time.sleep(0.001)  # Small delay for I2C
            return True
        except Exception as e:
            raise IOError(f"Error writing byte to address {address}: {e}")
    
    def read_byte(self, address):
        """Read a single byte from I2C device (smbus2 compatible)"""
        self._set_address(address)
        try:
            data = self.file.read(1)
            if len(data) == 1:
                return data[0]
            else:
                raise IOError(f"Error reading byte from address {address}")
        except Exception as e:
            raise IOError(f"Error reading byte from address {address}: {e}")
    
    def write_byte_data(self, address, register, value):
        """Write a byte to a specific register (smbus2 compatible)"""
        self._set_address(address)
        try:
            # Write register address followed by data byte
            self.file.write(bytes([register, value]))
            time.sleep(0.001)  # Small delay for I2C
            return True
        except Exception as e:
            raise IOError(f"Error writing byte data to address {address}, register {register}: {e}")
    
    def read_byte_data(self, address, register):
        """Read a byte from a specific register (smbus2 compatible)"""
        self._set_address(address)
        try:
            # Write register address
            self.file.write(bytes([register]))
            time.sleep(0.001)  # Small delay
            # Read data
            data = self.file.read(1)
            if len(data) == 1:
                return data[0]
            else:
                raise IOError(f"Error reading byte data from address {address}, register {register}")
        except Exception as e:
            raise IOError(f"Error reading byte data from address {address}, register {register}: {e}")
    
    def write_word_data(self, address, register, value):
        """Write a 16-bit word to a specific register (smbus2 compatible)"""
        self._set_address(address)
        try:
            # Write register address followed by low byte, then high byte
            low_byte = value & 0xFF
            high_byte = (value >> 8) & 0xFF
            self.file.write(bytes([register, low_byte, high_byte]))
            time.sleep(0.001)
            return True
        except Exception as e:
            raise IOError(f"Error writing word data to address {address}, register {register}: {e}")
    
    def read_word_data(self, address, register):
        """Read a 16-bit word from a specific register (smbus2 compatible)"""
        self._set_address(address)
        try:
            # Write register address
            self.file.write(bytes([register]))
            time.sleep(0.001)
            # Read 2 bytes (low byte first, then high byte)
            data = self.file.read(2)
            if len(data) == 2:
                return data[0] | (data[1] << 8)
            else:
                raise IOError(f"Error reading word data from address {address}, register {register}")
        except Exception as e:
            raise IOError(f"Error reading word data from address {address}, register {register}: {e}")
    
    def close(self):
        """Close I2C bus"""
        if self.file:
            self.file.close()
            self.file = None
            self.current_address = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Legacy alias for backward compatibility
I2CBus = SMBus

