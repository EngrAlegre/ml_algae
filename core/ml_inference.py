"""
ML Inference Module for AMLAC Robot
Handles algae detection using TensorFlow Lite model
"""

import os
import time
import numpy as np
from PIL import Image

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        print("Warning: TFLite runtime not available")
        tflite = None

# Try direct picamera2 import first, then fall back to camera bridge
Picamera2 = None
CameraBridge = None

try:
    from picamera2 import Picamera2
except ImportError as e:
    error_msg = str(e).lower()
    if '_libcamera' in error_msg or 'libcamera' in error_msg:
        print("Note: picamera2 not directly available (libcamera compiled for different Python)")
        print("  Attempting to use camera bridge via subprocess...")
    
    # Try to use camera bridge as fallback
    try:
        from core.camera_bridge import CameraBridge
        print("  ✅ Camera bridge available (will use python3.13 subprocess)")
    except ImportError:
        try:
            # Fallback for direct execution
            from camera_bridge import CameraBridge
            print("  ✅ Camera bridge available (will use python3.13 subprocess)")
        except ImportError:
            print("Warning: picamera2 and camera bridge both unavailable")
            CameraBridge = None

from config import (
    MODEL_PATH,
    LABELS_PATH,
    ML_INPUT_SIZE,
    ML_CONFIDENCE_THRESHOLD,
    ML_INFERENCE_INTERVAL,
    ML_CONFIRMATION_FRAMES,
    SAVE_DETECTION_IMAGES,
    DETECTION_IMAGES_DIR,
    DEBUG_MODE,
    SIMULATE_SENSORS
)


class AlgaeDetector:
    """
    ML-based algae detection using TensorFlow Lite model
    Trained with MobileNetV3 architecture
    
    Camera operates as continuous sensor (video stream mode)
    Processes frames at high FPS with confirmation mechanism
    """
    
    def __init__(self):
        """Initialize ML model and camera as continuous sensor"""
        self.initialized = False
        self.camera_initialized = False
        self.model_initialized = False
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        self.camera = None
        
        # Confirmation mechanism: track last N detections
        self.detection_history = []  # List of recent detection results
        self.confirmed_algae = False  # True when algae confirmed in multiple frames
        
        # Load labels
        if not self._load_labels():
            print("Warning: Could not load labels, using defaults")
            self.labels = ['Algae', 'No Algae']
        
        # Load TFLite model (skip if simulating)
        if SIMULATE_SENSORS:
            print("ML inference module running in simulation mode")
            self.initialized = True
            self.camera_initialized = True
            self.model_initialized = True
            return
        
        # Try to load model (don't fail if unavailable)
        if self._load_model():
            self.model_initialized = True
        else:
            print("Warning: ML model not loaded - detection unavailable")
        
        # Initialize camera as continuous sensor (don't fail if unavailable)
        if self._init_camera():
            self.camera_initialized = True
        else:
            print("Warning: Camera not initialized - using simulated images")
            
        # Create detection images directory if needed
        if SAVE_DETECTION_IMAGES:
            os.makedirs(DETECTION_IMAGES_DIR, exist_ok=True)
        
        # System is initialized if either model or camera works
        # We can still run with partial functionality
        self.initialized = self.model_initialized
        
        if DEBUG_MODE:
            status = "OK" if self.initialized else "LIMITED"
            print(f"ML inference module status: {status}")
            print(f"  Model loaded: {self.model_initialized}")
            print(f"  Camera ready: {self.camera_initialized}")
            if self.initialized:
                print(f"  Processing rate: ~{1.0/ML_INFERENCE_INTERVAL:.1f} FPS")
                print(f"  Confirmation frames: {ML_CONFIRMATION_FRAMES}")
                print(f"  Save detection images: {SAVE_DETECTION_IMAGES}")
    
    def _load_labels(self):
        """Load class labels from labels.txt"""
        try:
            if not os.path.exists(LABELS_PATH):
                print(f"Warning: Labels file not found at {LABELS_PATH}")
                # Use default labels
                self.labels = ['Algae', 'No Algae']
                return True
            
            with open(LABELS_PATH, 'r') as f:
                # Format: "0 Algae\n1 No Algae\n"
                for line in f:
                    line = line.strip()
                    if line:
                        # Extract label (skip index number)
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            self.labels.append(parts[1])
                        else:
                            self.labels.append(line)
            
            if DEBUG_MODE:
                print(f"Loaded labels: {self.labels}")
            
            return len(self.labels) > 0
            
        except Exception as e:
            print(f"Error loading labels: {e}")
            return False
    
    def _load_model(self):
        """Load TensorFlow Lite model"""
        try:
            if not os.path.exists(MODEL_PATH):
                print(f"Error: Model file not found at {MODEL_PATH}")
                return False
            
            if tflite is None:
                print("Error: TFLite runtime not available")
                return False
            
            # Load TFLite model
            self.interpreter = tflite.Interpreter(model_path=MODEL_PATH)
            self.interpreter.allocate_tensors()
            
            # Get input and output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            if DEBUG_MODE:
                print(f"Model loaded successfully")
                print(f"Input shape: {self.input_details[0]['shape']}")
                print(f"Output shape: {self.output_details[0]['shape']}")
            
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def _init_camera(self):
        """Initialize Raspberry Pi camera for continuous video streaming (sensor mode)"""
        try:
            # Try direct picamera2 first
            if Picamera2 is not None:
                self.camera = Picamera2()
                
                # Configure camera for continuous video preview (sensor mode)
                # This enables real-time frame capture without gaps
                config = self.camera.create_preview_configuration(
                    main={"size": (640, 480)},
                    buffer_count=3  # Multiple buffers for smooth streaming
                )
                self.camera.configure(config)
                self.camera.start()
                
                # Let camera warm up
                time.sleep(2)
                
                if DEBUG_MODE:
                    print("Camera initialized in continuous video mode (direct picamera2)")
                
                return True
            
            # Fall back to camera bridge (subprocess to Python 3.13)
            elif CameraBridge is not None:
                self.camera = CameraBridge(width=640, height=480)
                if self.camera.initialized:
                    if DEBUG_MODE:
                        print("Camera initialized via camera bridge (python3.13 subprocess)")
                    return True
                else:
                    print("Warning: Camera bridge failed to initialize")
                    self.camera = None
                    return False
            else:
                print("Warning: No camera backend available (picamera2 and bridge both unavailable)")
                return False
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None
            return False
    
    def _preprocess_image(self, image):
        """
        Preprocess image for model input
        Automatically detects if model expects UINT8 or FLOAT32
        
        Args:
            image: PIL Image or numpy array
            
        Returns:
            numpy array ready for inference
        """
        try:
            # Convert to PIL Image if needed
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Resize to model input size
            image = image.resize(ML_INPUT_SIZE, Image.BILINEAR)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Check what data type the model expects
            input_dtype = self.input_details[0]['dtype']
            
            if input_dtype == np.uint8:
                # Model expects UINT8 (0-255) - quantized model
                img_array = np.array(image, dtype=np.uint8)
            else:
                # Model expects FLOAT32 (0.0-1.0) - non-quantized model
                img_array = np.array(image, dtype=np.float32)
                img_array = img_array / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def capture_frame(self):
        """
        Capture latest frame from continuous video stream (sensor mode)
        Gets the most recent frame from the video buffer - no gaps
        
        Returns:
            PIL Image or None
        """
        if SIMULATE_SENSORS:
            # Create a fake green image (simulating algae)
            img = Image.new('RGB', ML_INPUT_SIZE, color=(80, 150, 70))
            return img
        
        if self.camera is None:
            return None
        
        try:
            # Check if using camera bridge or direct picamera2
            if CameraBridge is not None and isinstance(self.camera, CameraBridge):
                # Using camera bridge (subprocess mode)
                frame = self.camera.capture_frame()
                if frame is not None:
                    image = Image.fromarray(frame)
                    return image
                return None
            else:
                # Using direct picamera2
                # Get the latest frame from continuous video stream
                # This gets the most recent frame from the video buffer
                frame = self.camera.capture_array("main")
                
                # Convert to PIL Image
                image = Image.fromarray(frame)
                
                return image
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error capturing frame: {e}")
            return None
    
    def detect(self, image=None):
        """
        Detect algae in image with confirmation mechanism
        Camera operates as continuous sensor - processes latest frame from stream
        
        Args:
            image: PIL Image or numpy array (if None, captures latest frame from camera)
            
        Returns:
            dict: {
                'is_algae': bool,  # Confirmed detection (after confirmation frames)
                'confidence': float (0-1),
                'label': str,
                'all_scores': list of (label, score) tuples,
                'raw_detection': bool,  # Current frame detection (before confirmation)
                'confirmation_count': int  # How many consecutive detections
            }
        """
        if not self.initialized:
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'Error',
                'all_scores': [],
                'raw_detection': False,
                'confirmation_count': 0
            }
        
        # Capture latest frame from continuous stream if not provided
        if image is None:
            image = self.capture_frame()
            if image is None:
                return {
                    'is_algae': False,
                    'confidence': 0.0,
                    'label': 'No Image',
                    'all_scores': [],
                    'raw_detection': False,
                    'confirmation_count': 0
                }
        
        try:
            # Preprocess image
            input_data = self._preprocess_image(image)
            if input_data is None:
                return {
                    'is_algae': False,
                    'confidence': 0.0,
                    'label': 'Preprocessing Error',
                    'all_scores': [],
                    'raw_detection': False,
                    'confirmation_count': 0
                }
            
            # Run inference
            start_time = time.time()
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            inference_time = time.time() - start_time
            
            # Get predictions and normalize if quantized
            scores = output_data[0].astype(np.float32)
            
            # Check if output is quantized (UINT8) and scale to 0-1
            output_dtype = self.output_details[0]['dtype']
            if output_dtype == np.uint8:
                # Quantized output: scale from 0-255 to 0-1
                scores = scores / 255.0
            
            # Get top prediction
            top_index = np.argmax(scores)
            top_score = float(scores[top_index])
            top_label = self.labels[top_index] if top_index < len(self.labels) else f"Class {top_index}"
            
            # Check if it's algae (raw detection for current frame)
            raw_is_algae = (top_index == 0 and top_score >= ML_CONFIDENCE_THRESHOLD)
            
            # Update detection history for confirmation
            self.detection_history.append(raw_is_algae)
            # Keep only last N frames for confirmation
            if len(self.detection_history) > ML_CONFIRMATION_FRAMES:
                self.detection_history.pop(0)
            
            # Check confirmation: require N consecutive detections
            confirmation_count = 0
            if len(self.detection_history) >= ML_CONFIRMATION_FRAMES:
                # Count how many recent frames detected algae
                confirmation_count = sum(self.detection_history[-ML_CONFIRMATION_FRAMES:])
                self.confirmed_algae = (confirmation_count >= ML_CONFIRMATION_FRAMES)
            else:
                # Not enough frames yet, use raw detection
                self.confirmed_algae = raw_is_algae
                confirmation_count = sum(self.detection_history)
            
            # Save image if algae detected and saving is enabled
            if raw_is_algae and SAVE_DETECTION_IMAGES and image is not None:
                try:
                    timestamp = time.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
                    filename = f"algae_{timestamp}_conf{top_score*100:.0f}.jpg"
                    filepath = os.path.join(DETECTION_IMAGES_DIR, filename)
                    image.save(filepath)
                    if DEBUG_MODE:
                        print(f"Saved detection image: {filename}")
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"Error saving detection image: {e}")
            
            # Get all scores
            all_scores = [(self.labels[i] if i < len(self.labels) else f"Class {i}", float(scores[i])) 
                          for i in range(len(scores))]
            
            if DEBUG_MODE:
                print(f"Inference time: {inference_time*1000:.1f}ms")
                print(f"Prediction: {top_label} ({top_score*100:.1f}%)")
                print(f"Raw detection: {raw_is_algae}, Confirmed: {self.confirmed_algae} ({confirmation_count}/{ML_CONFIRMATION_FRAMES})")
            
            return {
                'is_algae': self.confirmed_algae,  # Confirmed detection
                'confidence': top_score,
                'label': top_label,
                'all_scores': all_scores,
                'raw_detection': raw_is_algae,  # Current frame detection
                'confirmation_count': confirmation_count
            }
            
        except Exception as e:
            print(f"Error during inference: {e}")
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'Inference Error',
                'all_scores': [],
                'raw_detection': False,
                'confirmation_count': 0
            }
    
    def detect_from_file(self, image_path):
        """
        Detect algae from image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            dict: Detection results (same as detect())
        """
        try:
            image = Image.open(image_path)
            return self.detect(image)
        except Exception as e:
            print(f"Error loading image from {image_path}: {e}")
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'File Error',
                'all_scores': []
            }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.camera:
                # Handle both direct picamera2 and camera bridge
                if CameraBridge is not None and isinstance(self.camera, CameraBridge):
                    self.camera.cleanup()
                else:
                    self.camera.stop()
                    self.camera.close()
            
            if DEBUG_MODE:
                print("ML inference cleanup complete")
                
        except Exception as e:
            print(f"Error during ML cleanup: {e}")


# Test function for standalone testing
if __name__ == "__main__":
    print("Testing ML Inference Module...\n")
    
    # Initialize detector
    detector = AlgaeDetector()
    
    if detector.initialized:
        print("Detector initialized successfully\n")
        
        # Test with camera capture
        print("Capturing and analyzing frame...")
        result = detector.detect()
        
        print(f"\nResults:")
        print(f"  Is Algae: {result['is_algae']}")
        print(f"  Label: {result['label']}")
        print(f"  Confidence: {result['confidence']*100:.2f}%")
        print(f"\n  All scores:")
        for label, score in result['all_scores']:
            print(f"    {label}: {score*100:.2f}%")
        
        # Test multiple frames
        print("\n\nTesting 5 consecutive frames...")
        for i in range(5):
            result = detector.detect()
            print(f"  Frame {i+1}: {result['label']} ({result['confidence']*100:.1f}%)")
            time.sleep(0.5)
    
    else:
        print("Failed to initialize detector")
    
    # Cleanup
    detector.cleanup()
    print("\nTest complete!")

