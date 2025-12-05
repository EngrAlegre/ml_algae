# AMLAC Robot - Quick Start Guide

Get your AMLAC robot up and running in minutes!

---

## 🚀 Quick Setup (5 Steps)

### 1. Hardware Setup
Connect all components according to the pin diagram in README.md:
- Motors to L298N drivers
- Sensors to GPIO/I2C pins
- Power supply (12V battery + 5V regulator)
- Camera module

### 2. Enable Interfaces
```bash
sudo raspi-config
```
Enable: **I2C**, **Serial Port** (no login shell), **Camera**

Reboot:
```bash
sudo reboot
```

### 3. Install Software
```bash
cd robot_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Test System
```bash
python3 test_system.py
```
Fix any failed tests before proceeding.

### 5. Run Robot
```bash
python3 main.py
```

---

## 🎮 Basic Controls

### Start Robot
```bash
cd robot_system
source venv/bin/activate
python3 main.py
```

### Stop Robot
Press **Ctrl+C** for graceful shutdown

### View Logs
```bash
# Real-time CSV logs
tail -f logs/amlac_log_*.csv

# Error logs
cat logs/errors.log
```

---

## ⚙️ Quick Configuration

Edit `config.py` to adjust:

```python
# Motor speeds (0-255)
PADDLE_DEFAULT_SPEED = 128
CONVEYOR_DEFAULT_SPEED = 153

# ML confidence threshold (0-1)
ML_CONFIDENCE_THRESHOLD = 0.7

# Loop timing (seconds)
MAIN_LOOP_INTERVAL = 2.0
COLLECTION_DURATION = 8.0

# Safety distances (cm)
OBSTACLE_WARNING_DISTANCE = 30

# Debug mode
DEBUG_MODE = False  # Set True for verbose output
SIMULATE_SENSORS = False  # Set True to test without hardware
```

---

## 🧪 Testing Without Hardware

Want to test the code without connecting hardware?

1. Edit `config.py`:
```python
SIMULATE_SENSORS = True
```

2. Run:
```bash
python3 main.py
```

The system will use simulated sensor data!

---

## 🔍 Troubleshooting Quick Fixes

### "RPi.GPIO not available"
```bash
pip install RPi.GPIO
```

### "I2C devices not detected"
```bash
sudo raspi-config  # Enable I2C
i2cdetect -y 1     # Check devices
```

### "Camera not working"
```bash
sudo raspi-config  # Enable Camera
libcamera-hello    # Test camera
```

### "Model not found"
Ensure model files are in `robot_system/models/`:
- `model.tflite`
- `labels.txt`

### Motors not moving
- Check 12V power to L298N
- Verify GPIO pin connections
- Test: `python3 motors.py`

---

## 📊 Understanding the Display

The LCD rotates through 5 modes every 4 seconds:

1. **Algae Status**: Detection result and confidence
2. **GPS**: Current coordinates
3. **Weight**: Collected algae weight
4. **Distance**: Obstacle distance
5. **Status**: System status and water level

---

## 🎯 Behavior Overview

### Patrol Mode (No Algae)
- Moves forward slowly
- Scans for algae every 2 seconds
- Avoids obstacles

### Collection Mode (Algae Detected)
- Approaches algae location
- Starts conveyor belt
- Collects for 8 seconds
- Returns to patrol

### Safety Stop
- Triggers if obstacle too close (<30cm)
- Triggers if no water detected
- Backs up and turns to avoid

---

## 📁 File Structure

```
robot_system/
├── main.py              # ← Start here
├── config.py           # ← Configure here
├── test_system.py      # ← Test here
├── requirements.txt    # ← Install dependencies
├── README.md           # ← Full documentation
├── models/
│   ├── model.tflite   # Your ML model
│   └── labels.txt     # Class labels
└── logs/
    └── amlac_log_*.csv  # Telemetry logs
```

---

## 🔄 Auto-Start on Boot (Optional)

Create systemd service:
```bash
sudo nano /etc/systemd/system/amlac.service
```

Add:
```ini
[Unit]
Description=AMLAC Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot_system
ExecStart=/home/pi/robot_system/venv/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable amlac.service
sudo systemctl start amlac.service
```

---

## 📞 Need Help?

1. Check **README.md** for detailed documentation
2. Run `python3 test_system.py` to diagnose issues
3. Enable `DEBUG_MODE = True` in config.py
4. Check logs in `logs/` directory

---

## ✅ Pre-Flight Checklist

Before each run:
- [ ] Battery charged (12V)
- [ ] All sensors connected
- [ ] Camera working
- [ ] I2C devices detected (`i2cdetect -y 1`)
- [ ] Model files in place
- [ ] Test passed (`python3 test_system.py`)
- [ ] Water present (if testing collection)

---

**Ready to collect algae! 🌊🤖**

For full documentation, see **README.md**

