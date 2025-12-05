# AMLAC Robot System
## Automated Machine Learning Algae Collector

Complete Python system for autonomous algae detection and collection using Raspberry Pi 5.

---

## 📋 Table of Contents
- [Overview](#overview)
- [Hardware Requirements](#hardware-requirements)
- [Pin Connections](#pin-connections)
- [Software Installation](#software-installation)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [System Architecture](#system-architecture)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The AMLAC robot is an autonomous water-based robot that:
- Detects algae-covered water using machine learning (MobileNetV3 model)
- Navigates using paddle wheels
- Collects algae with a conveyor belt system
- Logs telemetry data (GPS, sensors, ML results) to CSV
- Displays status on 16x2 LCD screen

### Key Features
- **ML-based Detection**: TensorFlow Lite model for real-time algae classification
- **Multi-sensor Integration**: GPS, color sensor, ultrasonic, IMU, load cell, float switch
- **Autonomous Navigation**: Obstacle avoidance and patrol behavior
- **Data Logging**: Automatic CSV logging with daily rotation
- **Safety Systems**: Water level detection, obstacle avoidance, watchdog timer
- **Modular Design**: Easy to test, modify, and extend

---

## 🔧 Hardware Requirements

### Main Components
- **Raspberry Pi 5** (4GB RAM, 64-bit OS)
- **Raspberry Pi Camera V2** (8MP)
- **12V Battery Pack** (Alephy 20000mAh or similar)
- **HW-688 5V Voltage Regulator**

### Motors & Drivers
- **2× 12V DC Geared Motors** (78 RPM) - Paddle wheels
- **1× 6-12V DC Geared Motor** (188 RPM) - Conveyor belt
- **2× L298N Motor Drivers**

### Sensors
- **TCS34725** - RGB Color Sensor (I2C)
- **JSN-SR04T** - Waterproof Ultrasonic Distance Sensor
- **MPU6050** - IMU (Accelerometer/Gyroscope) (I2C)
- **NEO-6M** - GPS Module (UART)
- **HX711** - Load Cell Amplifier
- **Float Switch** - Water Level Detection

### Display
- **16x2 LCD Display** with I2C backpack

### Miscellaneous
- Jumper wires
- Breadboard or PCB
- Power cables
- Waterproof enclosure (50×40×40 cm acrylic)

---

## 🔌 Pin Connections

### Motor Connections (L298N #1 - Paddle Wheels)
```
Left Motor:
  IN1 → GPIO 17
  IN2 → GPIO 18
  PWM → GPIO 12 (PWM0)

Right Motor:
  IN1 → GPIO 22
  IN2 → GPIO 23
  PWM → GPIO 13 (PWM1)
```

### Motor Connections (L298N #2 - Conveyor)
```
Conveyor Motor:
  IN1 → GPIO 24
  IN2 → GPIO 25
  PWM → GPIO 19
```

### Sensor Connections

#### I2C Devices (SDA → GPIO 2, SCL → GPIO 3)
```
TCS34725 Color Sensor → I2C Address 0x29
MPU6050 IMU           → I2C Address 0x68
16x2 LCD Display      → I2C Address 0x27
```

#### Ultrasonic Sensor (JSN-SR04T)
```
TRIGGER → GPIO 5
ECHO    → GPIO 6
VCC     → 5V
GND     → GND
```

#### GPS Module (NEO-6M)
```
TX  → RX (GPIO 15, /dev/serial0)
RX  → TX (GPIO 14, /dev/serial0)
VCC → 5V
GND → GND
```

#### Load Cell (HX711)
```
DATA  → GPIO 20
CLOCK → GPIO 16
VCC   → 5V
GND   → GND
```

#### Float Switch
```
Signal → GPIO 21 (with pull-up resistor)
GND    → GND
```

### Power Distribution
```
12V Battery → L298N Motor Drivers
12V Battery → HW-688 Regulator → 5V → Raspberry Pi
5V from Pi  → Sensors (TCS34725, MPU6050, HX711, Float Switch)
5V from Pi  → GPS Module
5V from Pi  → LCD Display
```

---

## 💻 Software Installation

### 1. Update Raspberry Pi OS
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Enable Required Interfaces
```bash
sudo raspi-config
```
Enable:
- **I2C** (Interface Options → I2C → Yes)
- **Serial Port** (Interface Options → Serial → Login shell: No, Serial port: Yes)
- **Camera** (Interface Options → Camera → Yes)

Reboot:
```bash
sudo reboot
```

### 3. Install System Dependencies
```bash
sudo apt install -y python3-pip python3-venv i2c-tools
sudo apt install -y libatlas-base-dev libopenjp2-7 libtiff5
sudo apt install -y python3-picamera2
```

### 4. Create Virtual Environment
```bash
cd robot_system
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Python Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Setup Instructions

### 1. Copy Model Files
Copy your trained TensorFlow Lite model to the models directory:
```bash
cp /path/to/your/model.tflite robot_system/models/
cp /path/to/your/labels.txt robot_system/models/
```

### 2. Test I2C Devices
```bash
i2cdetect -y 1
```
You should see:
- `0x27` (LCD Display)
- `0x29` (TCS34725 Color Sensor)
- `0x68` (MPU6050 IMU)

### 3. Test Individual Modules
Test each module independently:

```bash
# Test motors
python3 motors.py

# Test sensors
python3 sensors.py

# Test ML inference
python3 ml_inference.py

# Test data logger
python3 data_logger.py

# Test display
python3 display.py
```

### 4. Calibrate Load Cell
Edit `config.py` and adjust `HX711_CALIBRATION_FACTOR`:
```python
# Start with default value, then calibrate with known weight
HX711_CALIBRATION_FACTOR = 2280  # Adjust based on calibration
```

### 5. Configure Settings
Edit `config.py` to adjust:
- Motor speeds
- Sensor thresholds
- ML confidence threshold
- Timing intervals
- Safety settings

---

## 🎮 Usage

### Running the Robot

#### Basic Usage
```bash
cd robot_system
source venv/bin/activate
python3 main.py
```

#### Run in Background (with logs)
```bash
nohup python3 main.py > output.log 2>&1 &
```

#### Auto-start on Boot
Create a systemd service:
```bash
sudo nano /etc/systemd/system/amlac.service
```

Add:
```ini
[Unit]
Description=AMLAC Robot Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot_system
ExecStart=/home/pi/robot_system/venv/bin/python3 /home/pi/robot_system/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable amlac.service
sudo systemctl start amlac.service
sudo systemctl status amlac.service
```

### Stopping the Robot
- Press **Ctrl+C** for graceful shutdown
- Or: `sudo systemctl stop amlac.service`

### Viewing Logs
```bash
# View CSV logs
ls -lh logs/
cat logs/amlac_log_YYYYMMDD.csv

# View error logs
cat logs/errors.log

# View system logs (if using systemd)
sudo journalctl -u amlac.service -f
```

---

## 🏗️ System Architecture

### Module Overview

```
robot_system/
├── main.py              # Main orchestration loop
├── config.py           # Configuration and constants
├── motors.py           # Motor control (L298N drivers)
├── sensors.py          # All sensor classes
├── ml_inference.py     # TFLite algae detection
├── data_logger.py      # CSV telemetry logging
├── display.py          # LCD display control
├── utils.py            # Helper functions
├── models/             # ML model files
│   ├── model.tflite
│   └── labels.txt
└── logs/               # CSV and error logs
```

### Main Control Loop

1. **Initialize** all subsystems (motors, sensors, ML, logger, display)
2. **Read sensors** (color, distance, GPS, weight, water level, IMU)
3. **Check safety** (water level, obstacle distance)
4. **Run ML inference** on camera frame
5. **Execute behavior**:
   - If algae detected → approach and collect
   - If no algae → patrol mode
   - If obstacle → avoid
6. **Log telemetry** to CSV
7. **Update display** with current status
8. **Sleep** until next cycle (default: 2 seconds)
9. **Repeat** until shutdown signal

### State Machine

```
initializing → ready → running ⇄ collecting
                         ↓
                    safety_stop → running
                         ↓
                      error → running
                         ↓
                     shutdown
```

---

## ⚙️ Configuration

### Key Settings in `config.py`

#### Motor Speeds
```python
PADDLE_DEFAULT_SPEED = 128      # 0-255 (50% PWM)
CONVEYOR_DEFAULT_SPEED = 153    # 0-255 (60% PWM)
```

#### ML Settings
```python
ML_CONFIDENCE_THRESHOLD = 0.7   # Minimum confidence to act (0-1)
ML_INPUT_SIZE = (224, 224)      # Model input size
```

#### Timing
```python
MAIN_LOOP_INTERVAL = 2.0        # Seconds between cycles
COLLECTION_DURATION = 8.0       # Seconds to run conveyor
PATROL_MOVE_DURATION = 3.0      # Seconds to move during patrol
```

#### Safety
```python
OBSTACLE_WARNING_DISTANCE = 30  # cm (stop if closer)
ENABLE_WATER_LEVEL_CHECK = True
ENABLE_OBSTACLE_AVOIDANCE = True
```

#### Debug Mode
```python
DEBUG_MODE = False              # Enable verbose logging
SIMULATE_SENSORS = False        # Use fake sensor data for testing
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "RPi.GPIO not available"
**Solution**: Install GPIO library
```bash
pip install RPi.GPIO
```

#### 2. "smbus2 not available"
**Solution**: Install I2C library
```bash
pip install smbus2
```

#### 3. I2C devices not detected
**Solution**: 
- Check wiring (SDA → GPIO 2, SCL → GPIO 3)
- Enable I2C: `sudo raspi-config`
- Test: `i2cdetect -y 1`

#### 4. Camera not working
**Solution**:
- Enable camera: `sudo raspi-config`
- Install picamera2: `sudo apt install python3-picamera2`
- Test: `libcamera-hello`

#### 5. GPS not reading
**Solution**:
- Disable serial console: `sudo raspi-config` → Serial → No to login shell
- Check connection: `cat /dev/serial0` (should see NMEA sentences)
- Wait for GPS fix (may take 5-10 minutes outdoors)

#### 6. Motors not moving
**Solution**:
- Check L298N power (12V connected)
- Check GPIO connections
- Test with `python3 motors.py`
- Verify PWM pins are correct

#### 7. Load cell reading zero
**Solution**:
- Calibrate: adjust `HX711_CALIBRATION_FACTOR` in config.py
- Check wiring (DATA → GPIO 20, CLOCK → GPIO 16)
- Test with known weight

#### 8. ML model not loading
**Solution**:
- Verify model files exist in `models/` directory
- Install TFLite: `pip install tflite-runtime`
- Check model format (must be .tflite)

### Testing Individual Components

```bash
# Test motors only
python3 motors.py

# Test specific sensor
python3 -c "from sensors import ColorSensor; s = ColorSensor(); print(s.read())"

# Test ML inference
python3 ml_inference.py

# Test with simulated sensors (no hardware needed)
# Edit config.py: SIMULATE_SENSORS = True
python3 main.py
```

### Performance Optimization

- **Reduce loop interval** for faster response: `MAIN_LOOP_INTERVAL = 1.0`
- **Increase ML confidence** for fewer false positives: `ML_CONFIDENCE_THRESHOLD = 0.8`
- **Adjust motor speeds** for better navigation
- **Disable debug mode** for production: `DEBUG_MODE = False`

---

## 📊 CSV Log Format

Logs are saved in `logs/amlac_log_YYYYMMDD.csv`:

| Column | Description |
|--------|-------------|
| timestamp | ISO 8601 timestamp |
| gps_latitude | Latitude in decimal degrees |
| gps_longitude | Longitude in decimal degrees |
| gps_altitude | Altitude in meters |
| color_r | Red channel (0-255) |
| color_g | Green channel (0-255) |
| color_b | Blue channel (0-255) |
| distance_cm | Ultrasonic distance in cm |
| weight_kg | Load cell weight in kg |
| water_level | Boolean (True/False) |
| ml_result | ML prediction label |
| ml_confidence | ML confidence (0-1) |
| motor_state | Current motor state |
| system_status | System status message |

---

## 📝 License

This project is provided as-is for educational and research purposes.

---

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review individual module test outputs
3. Check hardware connections against pin diagrams
4. Enable `DEBUG_MODE` in config.py for verbose logging

---

## 🔄 Version History

- **v1.0.0** - Initial release
  - Complete system integration
  - All sensors supported
  - ML inference with TFLite
  - CSV logging and LCD display
  - Safety features and error handling

---

**AMLAC Robot** - Automated Machine Learning Algae Collector  
Built with Python on Raspberry Pi 5

