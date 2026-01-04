# AMLAC Robot - Project Structure

## 📁 Directory Organization

```
robot_system/
├── main.py                    # Main robot controller entry point
├── config.py                  # Global configuration and constants
├── utils.py                   # Utility functions and helpers
├── requirements.txt           # Python dependencies
├── __init__.py               # Package initialization
├── README_STRUCTURE.md        # This file
│
├── core/                      # Core system modules
│   ├── __init__.py
│   ├── motors.py             # Motor control (paddle wheels + conveyor)
│   ├── ml_inference.py       # ML algae detection (TFLite)
│   ├── data_logger.py        # CSV telemetry logging
│   └── display.py            # LCD display control
│
├── sensors/                   # Sensor modules
│   ├── __init__.py
│   └── sensors.py            # All 6 sensor classes
│       ├── ColorSensor (TCS34725)
│       ├── UltrasonicSensor (JSN-SR04T)
│       ├── IMUSensor (MPU6050)
│       ├── GPSSensor (NEO-6M)
│       ├── LoadCellSensor (HX711)
│       └── FloatSwitch
│
├── tests/                     # Test modules
│   ├── __init__.py
│   └── test_system.py        # Comprehensive system tests
│
├── docs/                      # Documentation
│   ├── README.md             # Complete documentation
│   ├── QUICKSTART.md         # Quick start guide
│   └── WIRING_DIAGRAM.md     # Hardware wiring guide
│
├── models/                    # ML models
│   ├── model.tflite          # Trained algae detection model
│   └── labels.txt            # Class labels
│
├── logs/                      # Auto-generated logs
│   └── amlac_log_*.csv       # Daily telemetry logs
│
└── example_log.csv            # Sample CSV output format
```

---

## 🚀 Quick Start

### Running the Robot
```bash
cd robot_system
python main.py
```

### Running Tests
```bash
cd robot_system
python tests/test_system.py
```

Or from the tests directory:
```bash
cd robot_system/tests
python test_system.py
```

---

## 📦 Module Organization

### Core Modules (`core/`)
Contains the main functional components of the robot:
- **motors.py**: Controls L298N motor drivers for movement and collection
- **ml_inference.py**: TensorFlow Lite inference for algae detection
- **data_logger.py**: CSV logging with automatic rotation
- **display.py**: 16x2 LCD I2C display management

### Sensors (`sensors/`)
All sensor reading and management:
- **sensors.py**: Unified sensor module with 6 sensor classes
  - Color detection (TCS34725)
  - Distance measurement (JSN-SR04T)
  - IMU data (MPU6050)
  - GPS positioning (NEO-6M)
  - Weight measurement (HX711)
  - Water level detection (Float Switch)

### Tests (`tests/`)
Testing and validation:
- **test_system.py**: Comprehensive test suite for all modules

### Documentation (`docs/`)
Complete project documentation:
- **README.md**: Full system documentation
- **QUICKSTART.md**: 5-step quick start guide
- **WIRING_DIAGRAM.md**: Hardware connections and pin mappings

---

## 🔧 Import Examples

### From main.py (root level):
```python
from core.motors import MotorController
from sensors.sensors import ColorSensor, UltrasonicSensor
from core.ml_inference import AlgaeDetector
```

### From tests (tests/ directory):
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.motors import MotorController
from sensors.sensors import ColorSensor
```

### As a package:
```python
from robot_system import AMLACRobot, MotorController
from robot_system.sensors import ColorSensor
```

---

## 📝 Configuration

All configuration is centralized in `config.py`:
- GPIO pin mappings
- I2C addresses
- Motor speeds
- ML thresholds
- Timing intervals
- Safety settings

---

## 🧪 Testing

Run the comprehensive test suite:
```bash
python tests/test_system.py
```

Tests include:
- Module imports
- Configuration validation
- Motor controller
- All 6 sensors
- ML inference
- Data logging
- LCD display
- Utility functions
- System integration

---

## 📊 Data Logging

Logs are automatically saved to `logs/` directory:
- Format: `amlac_log_YYYYMMDD.csv`
- Daily rotation
- 3-day retention (configurable)
- 14 columns of telemetry data

---

## 🔍 File Descriptions

| File | Purpose |
|------|---------|
| `main.py` | Main robot controller with autonomous behavior |
| `config.py` | All configuration constants and settings |
| `utils.py` | Helper functions (timers, validators, formatters) |
| `core/motors.py` | L298N motor control (3 motors) |
| `core/ml_inference.py` | TFLite algae detection |
| `core/data_logger.py` | CSV telemetry logging |
| `core/display.py` | 16x2 LCD I2C display |
| `sensors/sensors.py` | All 6 sensor classes |
| `tests/test_system.py` | Comprehensive test suite |
| `docs/README.md` | Complete documentation |
| `docs/QUICKSTART.md` | Quick start guide |
| `docs/WIRING_DIAGRAM.md` | Hardware wiring guide |

---

## 🎯 Design Principles

1. **Modular**: Each component is self-contained
2. **Organized**: Clear directory structure
3. **Testable**: Each module can be tested independently
4. **Documented**: Comprehensive documentation
5. **Configurable**: All settings in config.py
6. **Maintainable**: Clean code with docstrings

---

## 📚 For More Information

- **Full Documentation**: See `docs/README.md`
- **Quick Setup**: See `docs/QUICKSTART.md`
- **Hardware Setup**: See `docs/WIRING_DIAGRAM.md`
- **Testing**: Run `python tests/test_system.py`

---

**AMLAC Robot v1.0.0** - Automated Machine Learning Algae Collector

