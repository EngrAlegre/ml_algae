#!/usr/bin/env python3
"""
Camera Bridge for AMLAC Robot
Provides camera functionality using system Python (3.13) which has libcamera bindings

This module is designed to be called as a subprocess from Python 3.11,
or can be imported directly in Python 3.13 environments.

Usage as subprocess:
    python3.13 camera_bridge.py capture /tmp/frame.jpg
    python3.13 camera_bridge.py capture_raw /tmp/frame.raw 640 480
    
Usage as module (Python 3.13 only):
    from camera_bridge import CameraBridge
    bridge = CameraBridge()
    frame = bridge.capture_frame()
"""

import sys
import os
import json
import time
import tempfile
import subprocess
from pathlib import Path

# Check if we can import picamera2 (only works on Python 3.13 with libcamera)
PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    Picamera2 = None


class CameraBridge:
    """
    Bridge class for camera operations
    Uses picamera2 directly if available, otherwise uses subprocess to Python 3.13
    """
    
    def __init__(self, width=640, height=480):
        """Initialize camera bridge"""
        self.width = width
        self.height = height
        self.camera = None
        self.initialized = False
        self.use_subprocess = False
        
        if PICAMERA2_AVAILABLE:
            self._init_direct()
        else:
            self._init_subprocess()
    
    def _init_direct(self):
        """Initialize camera directly using picamera2"""
        try:
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": (self.width, self.height)},
                buffer_count=3
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(1)  # Warm-up time
            self.initialized = True
            self.use_subprocess = False
            print("Camera bridge initialized (direct mode)")
        except Exception as e:
            print(f"Error initializing camera directly: {e}")
            self.initialized = False
    
    def _init_subprocess(self):
        """Initialize camera via subprocess"""
        # Check if python3.13 is available
        try:
            result = subprocess.run(
                ['python3.13', '-c', 'from picamera2 import Picamera2; print("OK")'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and 'OK' in result.stdout:
                self.use_subprocess = True
                self.initialized = True
                print("Camera bridge initialized (subprocess mode via python3.13)")
            else:
                print(f"python3.13 picamera2 check failed: {result.stderr}")
                self.initialized = False
        except FileNotFoundError:
            print("python3.13 not found, camera disabled")
            self.initialized = False
        except subprocess.TimeoutExpired:
            print("Camera check timed out")
            self.initialized = False
        except Exception as e:
            print(f"Error checking python3.13: {e}")
            self.initialized = False
    
    def capture_frame(self):
        """
        Capture a frame from the camera
        
        Returns:
            numpy array (RGB) or None on error
        """
        if not self.initialized:
            return None
        
        try:
            if self.use_subprocess:
                return self._capture_subprocess()
            else:
                return self._capture_direct()
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None
    
    def _capture_direct(self):
        """Capture frame directly using picamera2"""
        try:
            import numpy as np
            frame = self.camera.capture_array("main")
            # Convert BGR to RGB if needed
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                # RGBA to RGB
                frame = frame[:, :, :3]
            return frame
        except Exception as e:
            print(f"Direct capture error: {e}")
            return None
    
    def _capture_subprocess(self):
        """Capture frame via subprocess to python3.13"""
        try:
            import numpy as np
            
            # Create temp file for frame data
            with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
                temp_path = f.name
            
            # Get the path to this script
            script_path = os.path.abspath(__file__)
            
            # Call python3.13 to capture frame
            result = subprocess.run(
                ['python3.13', script_path, 'capture_raw', temp_path, str(self.width), str(self.height)],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                print(f"Subprocess capture failed: {result.stderr}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
            
            # Read the raw frame data
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    data = f.read()
                os.remove(temp_path)
                
                if len(data) > 0:
                    # Reshape to image
                    frame = np.frombuffer(data, dtype=np.uint8)
                    frame = frame.reshape((self.height, self.width, 3))
                    return frame
            
            return None
            
        except subprocess.TimeoutExpired:
            print("Capture subprocess timed out")
            return None
        except Exception as e:
            print(f"Subprocess capture error: {e}")
            return None
    
    def capture_to_file(self, filepath):
        """
        Capture a frame and save to file
        
        Args:
            filepath: Path to save the image
            
        Returns:
            bool: True on success
        """
        if not self.initialized:
            return False
        
        try:
            if self.use_subprocess:
                script_path = os.path.abspath(__file__)
                result = subprocess.run(
                    ['python3.13', script_path, 'capture', filepath],
                    capture_output=True, text=True, timeout=10
                )
                return result.returncode == 0
            else:
                from PIL import Image
                frame = self._capture_direct()
                if frame is not None:
                    img = Image.fromarray(frame)
                    img.save(filepath)
                    return True
                return False
        except Exception as e:
            print(f"Error saving frame: {e}")
            return False
    
    def cleanup(self):
        """Clean up camera resources"""
        if self.camera and not self.use_subprocess:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass
        self.initialized = False


def main():
    """Command-line interface for camera bridge (used by subprocess mode)"""
    if len(sys.argv) < 2:
        print("Usage: camera_bridge.py <command> [args]")
        print("Commands:")
        print("  capture <filepath>              - Capture and save JPEG")
        print("  capture_raw <filepath> <w> <h>  - Capture raw RGB data")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'capture':
        if len(sys.argv) < 3:
            print("Error: filepath required")
            sys.exit(1)
        
        filepath = sys.argv[2]
        
        try:
            camera = Picamera2()
            config = camera.create_still_configuration(main={"size": (640, 480)})
            camera.configure(config)
            camera.start()
            time.sleep(0.5)
            camera.capture_file(filepath)
            camera.stop()
            camera.close()
            print(f"Captured to {filepath}")
            sys.exit(0)
        except Exception as e:
            print(f"Capture error: {e}")
            sys.exit(1)
    
    elif command == 'capture_raw':
        if len(sys.argv) < 5:
            print("Error: filepath, width, height required")
            sys.exit(1)
        
        filepath = sys.argv[2]
        width = int(sys.argv[3])
        height = int(sys.argv[4])
        
        try:
            camera = Picamera2()
            config = camera.create_preview_configuration(main={"size": (width, height)})
            camera.configure(config)
            camera.start()
            time.sleep(0.5)
            frame = camera.capture_array("main")
            camera.stop()
            camera.close()
            
            # Ensure RGB format
            if len(frame.shape) == 3 and frame.shape[2] == 4:
                frame = frame[:, :, :3]
            
            # Save raw data
            with open(filepath, 'wb') as f:
                f.write(frame.tobytes())
            
            print(f"Captured raw {width}x{height} to {filepath}")
            sys.exit(0)
        except Exception as e:
            print(f"Capture raw error: {e}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
