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

try:
    from picamera2 import Picamera2
except ImportError:
    print("Warning: picamera2 not available")
    Picamera2 = None

from config import (
    MODEL_PATH,
    LABELS_PATH,
    ML_INPUT_SIZE,
    ML_CONFIDENCE_THRESHOLD,
    DEBUG_MODE,
    SIMULATE_SENSORS
)


class AlgaeDetector:
    """
    ML-based algae detection using TensorFlow Lite model
    Trained with MobileNetV3 architecture
    """
    
    def __init__(self):
        """Initialize ML model and camera"""
        self.initialized = False
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        self.camera = None
        
        # Load labels
        if not self._load_labels():
            print("Error: Could not load labels")
            return
        
        # Load TFLite model
        if not self._load_model():
            print("Error: Could not load ML model")
            return
        
        # Initialize camera
        if not SIMULATE_SENSORS:
            self._init_camera()
        
        self.initialized = True
        if DEBUG_MODE:
            print("ML inference module initialized")
    
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
        """Initialize Raspberry Pi camera"""
        try:
            if Picamera2 is None:
                print("Warning: picamera2 not available, camera disabled")
                return False
            
            self.camera = Picamera2()
            
            # Configure camera for still capture
            config = self.camera.create_still_configuration(
                main={"size": (640, 480)},
                buffer_count=2
            )
            self.camera.configure(config)
            self.camera.start()
            
            # Let camera warm up
            time.sleep(2)
            
            if DEBUG_MODE:
                print("Camera initialized")
            
            return True
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None
            return False
    
    def _preprocess_image(self, image):
        """
        Preprocess image for model input
        
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
            
            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32)
            
            # Normalize to [0, 1] range
            img_array = img_array / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def capture_frame(self):
        """
        Capture a frame from the camera
        
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
            # Capture frame as numpy array
            frame = self.camera.capture_array()
            
            # Convert to PIL Image
            image = Image.fromarray(frame)
            
            return image
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error capturing frame: {e}")
            return None
    
    def detect(self, image=None):
        """
        Detect algae in image
        
        Args:
            image: PIL Image or numpy array (if None, captures from camera)
            
        Returns:
            dict: {
                'is_algae': bool,
                'confidence': float (0-1),
                'label': str,
                'all_scores': list of (label, score) tuples
            }
        """
        if not self.initialized:
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'Error',
                'all_scores': []
            }
        
        # Capture image if not provided
        if image is None:
            image = self.capture_frame()
            if image is None:
                return {
                    'is_algae': False,
                    'confidence': 0.0,
                    'label': 'No Image',
                    'all_scores': []
                }
        
        try:
            # Preprocess image
            input_data = self._preprocess_image(image)
            if input_data is None:
                return {
                    'is_algae': False,
                    'confidence': 0.0,
                    'label': 'Preprocessing Error',
                    'all_scores': []
                }
            
            # Run inference
            start_time = time.time()
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            inference_time = time.time() - start_time
            
            # Get predictions
            scores = output_data[0]
            
            # Get top prediction
            top_index = np.argmax(scores)
            top_score = float(scores[top_index])
            top_label = self.labels[top_index] if top_index < len(self.labels) else f"Class {top_index}"
            
            # Check if it's algae (assuming index 0 is "Algae")
            is_algae = (top_index == 0 and top_score >= ML_CONFIDENCE_THRESHOLD)
            
            # Get all scores
            all_scores = [(self.labels[i] if i < len(self.labels) else f"Class {i}", float(scores[i])) 
                          for i in range(len(scores))]
            
            if DEBUG_MODE:
                print(f"Inference time: {inference_time*1000:.1f}ms")
                print(f"Prediction: {top_label} ({top_score*100:.1f}%)")
            
            return {
                'is_algae': is_algae,
                'confidence': top_score,
                'label': top_label,
                'all_scores': all_scores
            }
            
        except Exception as e:
            print(f"Error during inference: {e}")
            return {
                'is_algae': False,
                'confidence': 0.0,
                'label': 'Inference Error',
                'all_scores': []
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

