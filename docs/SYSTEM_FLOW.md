# AMLAC Robot System Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AMLAC ROBOT SYSTEM                             │
│                    Automated Machine Learning Algae Collector               │
└─────────────────────────────────────────────────────────────────────────────┘

                                 ┌─────────────┐
                                 │   main.py   │
                                 │  (Entry)    │
                                 └──────┬──────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
           ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
           │  INITIALIZE   │   │  MAIN LOOP    │   │   SHUTDOWN    │
           │  ALL SYSTEMS  │   │  (Running)    │   │   (Cleanup)   │
           └───────────────┘   └───────────────┘   └───────────────┘
```

---

## 1. INITIALIZATION PHASE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STARTUP SEQUENCE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Load Config  │ ◄── config.py (GPIO pins, settings, thresholds)
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐     ┌─────────────────────────────────────────┐
    │   Motors     │────►│ MotorController (lgpio)                 │
    │              │     │ • Left paddle wheel (GPIO 17,27,18)     │
    └──────┬───────┘     │ • Right paddle wheel (GPIO 22,23,13)    │
           │             │ • Conveyor belt (GPIO 24,25,12)         │
           │             └─────────────────────────────────────────┘
           ▼
    ┌──────────────┐     ┌─────────────────────────────────────────┐
    │   Sensors    │────►│ I2C Sensors (Direct I2C / smbus2)       │
    │              │     │ • Color Sensor TCS34725 (0x29)          │
    │              │     │ • IMU MPU6050 (0x68)                    │
    │              │     │ • LCD Display (0x27)                    │
    └──────┬───────┘     ├─────────────────────────────────────────┤
           │             │ GPIO Sensors (lgpio)                    │
           │             │ • Ultrasonic JSN-SR04T (GPIO 20,21)     │
           │             │ • Load Cell HX711 (GPIO 8,7)            │
           │             │ • Float Switch (GPIO 11)                │
           │             ├─────────────────────────────────────────┤
           │             │ Serial Sensor                           │
           │             │ • GPS NEO-6M (/dev/ttyAMA0)             │
           │             └─────────────────────────────────────────┘
           ▼
    ┌──────────────┐     ┌─────────────────────────────────────────┐
    │ ML Detector  │────►│ AlgaeDetector                           │
    │              │     │ • Load labels.txt                       │
    │              │     │ • Load model.tflite (TFLite)            │
    │              │     │ • Init Camera Bridge (Python 3.13)      │
    └──────┬───────┘     └─────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐     ┌─────────────────────────────────────────┐
    │   Loggers    │────►│ • CSV Logger (logs/amlac_log_DATE.csv)  │
    │              │     │ • Firebase Logger (Firestore)           │
    └──────┬───────┘     └─────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐     ┌─────────────────────────────────────────┐
    │   Display    │────►│ LCD 16x2 I2C Display                    │
    │              │     │ Shows: Status, GPS, Algae %, Weight     │
    └──────┬───────┘     └─────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │ Show Status  │ ──► Hardware Status Table (OK / NOT CONNECTED)
    └──────────────┘
```

---

## 2. MAIN LOOP (Every ~2 seconds)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAIN CONTROL LOOP                              │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌─────────────────────────────────────────────────────────┐
         │                    SENSOR READINGS                      │
         └─────────────────────────────────────────────────────────┘
                                    │
    ┌───────────┬───────────┬───────┴───────┬───────────┬──────────┐
    ▼           ▼           ▼               ▼           ▼          ▼
┌───────┐  ┌───────┐  ┌──────────┐   ┌──────────┐  ┌───────┐  ┌───────┐
│ Color │  │  IMU  │  │Ultrasonic│   │   GPS    │  │ Load  │  │ Float │
│  RGB  │  │ Tilt  │  │ Distance │   │ Lat/Lon  │  │ Cell  │  │Switch │
└───┬───┘  └───┬───┘  └────┬─────┘   └────┬─────┘  └───┬───┘  └───┬───┘
    │          │           │              │            │          │
    └──────────┴───────────┴──────┬───────┴────────────┴──────────┘
                                  │
                                  ▼
         ┌─────────────────────────────────────────────────────────┐
         │                   CAMERA + ML INFERENCE                 │
         └─────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            ┌──────────────┐            ┌──────────────┐
            │ Capture Frame│            │  Preprocess  │
            │ (640x480)    │───────────►│  (224x224)   │
            └──────────────┘            └──────┬───────┘
                                               │
                                               ▼
                                       ┌──────────────┐
                                       │ TFLite Model │
                                       │ MobileNetV3  │
                                       └──────┬───────┘
                                               │
                                               ▼
                                       ┌──────────────┐
                                       │   Output:    │
                                       │ • Algae: 85% │
                                       │ • No Algae:  │
                                       │   15%        │
                                       └──────┬───────┘
                                               │
                                               ▼
                                   ┌────────────────────┐
                                   │ CONFIRMATION CHECK │
                                   │ (2+ frames needed) │
                                   └─────────┬──────────┘
                                             │
                         ┌───────────────────┴───────────────────┐
                         ▼                                       ▼
                 ┌───────────────┐                       ┌───────────────┐
                 │ ALGAE = YES   │                       │ ALGAE = NO    │
                 │ (Confirmed)   │                       │ (Keep moving) │
                 └───────┬───────┘                       └───────┬───────┘
                         │                                       │
         ┌───────────────┴───────────────┐                       │
         ▼                               ▼                       │
┌─────────────────┐            ┌─────────────────┐               │
│ Slow down /     │            │ Start Conveyor  │               │
│ Approach algae  │            │ (Collect algae) │               │
└─────────────────┘            └─────────────────┘               │
                                                                 │
                    ┌────────────────────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────────────────────────────────────────┐
         │                    OBSTACLE CHECK                       │
         └─────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐
          │ Distance < 30cm │             │ Distance >= 30cm│
          │ (Obstacle!)     │             │ (Clear)         │
          └────────┬────────┘             └────────┬────────┘
                   │                               │
                   ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐
          │ STOP / TURN     │             │ MOVE FORWARD    │
          └─────────────────┘             └─────────────────┘

                                    │
                                    ▼
         ┌─────────────────────────────────────────────────────────┐
         │                      UPDATE OUTPUTS                     │
         └─────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │ LCD Display │          │  CSV Log    │          │  Firebase   │
    │ (Rotate     │          │ (One row    │          │ (Real-time  │
    │  screens)   │          │  per loop)  │          │  sync)      │
    └─────────────┘          └─────────────┘          └─────────────┘

                                    │
                                    ▼
                            ┌─────────────┐
                            │ LOOP AGAIN  │
                            │ (2 sec)     │
                            └─────────────┘
```

---

## 3. SHUTDOWN PHASE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SHUTDOWN (Ctrl+C)                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Signal SIGINT│ ◄── User presses Ctrl+C
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Stop Motors  │ ──► PWM = 0, Direction pins = LOW
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Flush Logs   │ ──► Write remaining data to CSV / Firebase
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Cleanup      │ ──► Close I2C, GPIO, Serial, Camera
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ LCD Message  │ ──► "AMLAC Shutdown"
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Print Summary│ ──► Total loops, Total algae detected
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    EXIT      │
    └──────────────┘
```

---

## Data Flow Summary

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SENSORS   │───►│  PROCESSING │───►│  DECISIONS  │───►│   OUTPUTS   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

  • Camera          • ML Inference     • Move/Stop        • Motors
  • Color           • Confirmation     • Turn             • LCD
  • Ultrasonic      • Obstacle check   • Collect algae    • CSV Log
  • IMU             • Data fusion      • Avoid obstacle   • Firebase
  • GPS                                                   • Conveyor
  • Load Cell
  • Float Switch
```

---

## File Structure (Clean)

```
robot_system/
├── main.py                 # Entry point
├── config.py               # All settings and pin mappings
├── requirements.txt        # Python dependencies
├── serviceAccountKey.json  # Firebase credentials (not in git)
│
├── core/                   # Core modules
│   ├── motors.py           # Motor control (lgpio)
│   ├── ml_inference.py     # ML model + camera
│   ├── camera_bridge.py    # Camera via Python 3.13 subprocess
│   ├── display.py          # LCD control
│   ├── data_logger.py      # CSV logging
│   ├── firebase_logger.py  # Firebase sync
│   └── i2c_direct.py       # Direct I2C (bypass smbus2)
│
├── sensors/                # Sensor modules
│   └── sensors.py          # All 6 sensors
│
├── models/                 # ML model files
│   ├── model.tflite        # TensorFlow Lite model
│   └── labels.txt          # Class labels
│
├── logs/                   # CSV log files (auto-created)
│
├── docs/                   # Documentation
│   ├── README.md           # Main documentation
│   ├── QUICKSTART.md       # Quick setup guide
│   ├── WIRING_DIAGRAM.md   # Hardware wiring
│   └── SYSTEM_FLOW.md      # This file
│
├── web/                    # React dashboard (optional)
│   ├── src/
│   └── public/
│
└── tests/                  # Unit tests
    └── test_system.py
```
