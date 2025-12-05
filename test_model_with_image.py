"""
Test AMLAC Model with Single Image
Quick script to test the trained model on a specific image
"""

import os
import sys
import numpy as np
from PIL import Image

# Try to import TFLite
try:
    import tflite_runtime.interpreter as tflite
    print("Using tflite_runtime")
except ImportError:
    try:
        import tensorflow.lite as tflite
        print("Using tensorflow.lite")
    except ImportError:
        print("ERROR: Neither tflite_runtime nor tensorflow is installed!")
        print("Install with: pip install tflite-runtime")
        sys.exit(1)

# Configuration
MODEL_PATH = "Model/model.tflite"
LABELS_PATH = "Model/labels.txt"
IMAGE_PATH = "swimming-pool-surface-with-reflections_1232-1273.avif"
INPUT_SIZE = (224, 224)


def load_labels(labels_path):
    """Load class labels from file"""
    labels = []
    try:
        with open(labels_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Format: "0 Algae" or just "Algae"
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        labels.append(parts[1])
                    else:
                        labels.append(line)
        return labels
    except Exception as e:
        print(f"Error loading labels: {e}")
        return ['Algae', 'No Algae']  # Default labels


def preprocess_image(image_path, input_size):
    """
    Preprocess image for model input
    
    Args:
        image_path: Path to image file
        input_size: Target size (width, height)
        
    Returns:
        Preprocessed numpy array
    """
    try:
        # Load image
        image = Image.open(image_path)
        print(f"Original image size: {image.size}")
        print(f"Original image mode: {image.mode}")
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            print("Converted to RGB")
        
        # Resize to model input size
        image = image.resize(input_size, Image.BILINEAR)
        print(f"Resized to: {input_size}")
        
        # Convert to numpy array (UINT8 for this model)
        img_array = np.array(image, dtype=np.uint8)
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        print(f"Final array shape: {img_array.shape}")
        print(f"Array value range: [{img_array.min():.3f}, {img_array.max():.3f}]")
        
        return img_array
        
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None


def softmax(x):
    """Apply softmax to convert logits to probabilities"""
    exp_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
    return exp_x / exp_x.sum()


def run_inference(model_path, image_array):
    """
    Run inference on preprocessed image
    
    Args:
        model_path: Path to TFLite model
        image_array: Preprocessed image array
        
    Returns:
        Prediction scores (probabilities)
    """
    try:
        # Load TFLite model
        print(f"\nLoading model from: {model_path}")
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        
        # Get input and output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"Input shape: {input_details[0]['shape']}")
        print(f"Input type: {input_details[0]['dtype']}")
        print(f"Output shape: {output_details[0]['shape']}")
        
        # Run inference
        print("\nRunning inference...")
        interpreter.set_tensor(input_details[0]['index'], image_array)
        interpreter.invoke()
        
        # Get output
        output_data = interpreter.get_tensor(output_details[0]['index'])
        raw_output = output_data[0]
        
        print(f"Raw output: {raw_output}")
        print(f"Output dtype: {output_data.dtype}")
        
        # Check if output is quantized (uint8)
        if output_data.dtype == np.uint8:
            # Dequantize if needed
            output_scale = output_details[0].get('quantization_parameters', {}).get('scales')
            output_zero_point = output_details[0].get('quantization_parameters', {}).get('zero_points')
            
            if output_scale is not None and len(output_scale) > 0:
                print(f"Dequantizing output (scale={output_scale[0]}, zero_point={output_zero_point[0]})")
                logits = (raw_output.astype(np.float32) - output_zero_point[0]) * output_scale[0]
            else:
                # Simple dequantization: map [0, 255] to [0, 1]
                logits = raw_output.astype(np.float32) / 255.0
                print(f"Simple dequantization applied")
        else:
            logits = raw_output.astype(np.float32)
        
        print(f"Dequantized logits: {logits}")
        
        # Check if output is already probabilities (sum close to 1)
        if np.abs(logits.sum() - 1.0) < 0.1:
            print("Output appears to be probabilities already")
            scores = logits
        else:
            # Apply softmax to get probabilities
            print("Applying softmax to convert logits to probabilities")
            scores = softmax(logits)
        
        return scores
        
    except Exception as e:
        print(f"Error during inference: {e}")
        return None


def main():
    """Main test function"""
    print("=" * 60)
    print("  AMLAC Model - Single Image Test")
    print("=" * 60)
    
    # Check if files exist
    if not os.path.exists(MODEL_PATH):
        print(f"\nERROR: Model file not found: {MODEL_PATH}")
        return
    
    if not os.path.exists(LABELS_PATH):
        print(f"\nWARNING: Labels file not found: {LABELS_PATH}")
        print("Using default labels")
    
    if not os.path.exists(IMAGE_PATH):
        print(f"\nERROR: Image file not found: {IMAGE_PATH}")
        return
    
    print(f"\nModel: {MODEL_PATH}")
    print(f"Image: {IMAGE_PATH}")
    print(f"Labels: {LABELS_PATH}")
    
    # Load labels
    print("\n" + "-" * 60)
    print("Loading labels...")
    labels = load_labels(LABELS_PATH)
    print(f"Classes: {labels}")
    
    # Preprocess image
    print("\n" + "-" * 60)
    print("Preprocessing image...")
    image_array = preprocess_image(IMAGE_PATH, INPUT_SIZE)
    
    if image_array is None:
        print("Failed to preprocess image")
        return
    
    # Run inference
    print("\n" + "-" * 60)
    scores = run_inference(MODEL_PATH, image_array)
    
    if scores is None:
        print("Inference failed")
        return
    
    # Display results
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    
    print(f"\nImage: {IMAGE_PATH}")
    print("\nPrediction Scores:")
    for i, score in enumerate(scores):
        label = labels[i] if i < len(labels) else f"Class {i}"
        percentage = score * 100
        bar_length = int(percentage / 2)  # Scale to 50 chars max
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"  {label:15s} [{bar}] {percentage:6.2f}%")
    
    # Get top prediction
    top_index = np.argmax(scores)
    top_score = scores[top_index]
    top_label = labels[top_index] if top_index < len(labels) else f"Class {top_index}"
    
    print("\n" + "-" * 60)
    print(f"🎯 PREDICTION: {top_label}")
    print(f"   Confidence: {top_score * 100:.2f}%")
    print("-" * 60)
    
    # Interpretation
    if top_label.lower() == 'algae' or top_index == 0:
        print("\n✅ ALGAE DETECTED!")
        if top_score >= 0.7:
            print("   High confidence - Robot would collect")
        elif top_score >= 0.5:
            print("   Medium confidence - May need verification")
        else:
            print("   Low confidence - Robot would skip")
    else:
        print("\n❌ NO ALGAE DETECTED")
        print("   Robot would continue patrol")
    
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

