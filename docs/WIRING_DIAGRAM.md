# AMLAC Robot - Wiring Diagram

Complete pin connections for Raspberry Pi 5

---

## 🔌 Power Distribution

```
12V Battery (20000mAh)
    ├─→ L298N Motor Driver #1 (12V input)
    ├─→ L298N Motor Driver #2 (12V input)
    └─→ HW-688 Voltage Regulator
            └─→ 5V output → Raspberry Pi 5 (USB-C or GPIO pins 2/4)
```

---

## 🎮 Motor Connections

### L298N Motor Driver #1 (Paddle Wheels)

**Power:**
- 12V → From battery
- GND → Common ground
- 5V → Not used (Pi has own power)

**Left Motor (78 RPM):**
- OUT1, OUT2 → Left paddle wheel motor
- IN1 → GPIO 17
- IN2 → GPIO 27
- ENA (PWM) → GPIO 18

**Right Motor (78 RPM):**
- OUT3, OUT4 → Right paddle wheel motor
- IN3 → GPIO 22
- IN4 → GPIO 23
- ENB (PWM) → GPIO 13

### L298N Motor Driver #2 (Conveyor)

**Power:**
- 12V → From battery
- GND → Common ground

**Conveyor Motor (188 RPM):**
- OUT1, OUT2 → Conveyor belt motor
- IN1 → GPIO 24
- IN2 → GPIO 25
- ENA (PWM) → GPIO 12

---

## 📡 I2C Devices (Bus 1)

**I2C Bus Pins:**
- SDA → GPIO 2 (Pin 3)
- SCL → GPIO 3 (Pin 5)
- 3.3V → Pin 1 or 17
- GND → Any ground pin

### TCS34725 RGB Color Sensor
```
VIN → 3.3V (Pin 1)
GND → GND
SDA → GPIO 2 (Pin 3)
SCL → GPIO 3 (Pin 5)
I2C Address: 0x29
```

### MPU6050 IMU
```
VCC → 3.3V (Pin 1)
GND → GND
SDA → GPIO 2 (Pin 3)
SCL → GPIO 3 (Pin 5)
I2C Address: 0x68
```

### 16x2 LCD with I2C Backpack
```
VCC → 5V (Pin 2 or 4)
GND → GND
SDA → GPIO 2 (Pin 3)
SCL → GPIO 3 (Pin 5)
I2C Address: 0x27
```

**Note:** All I2C devices share the same SDA/SCL lines.

---

## 📏 Ultrasonic Sensor (JSN-SR04T)

```
VCC → 5V (Pin 2 or 4)
TRIG → GPIO 20 (Pin 38)
ECHO → GPIO 21 (Pin 40)
GND → GND (Pin 39)
```

---

## 🛰️ GPS Module (NEO-6M)

```
VCC → 5V (Pin 2 or 4)
GND → GND
TX (GPS) → RX (GPIO 15, Pin 10) - UART0
RX (GPS) → TX (GPIO 14, Pin 8) - UART0
```

**Note:** Disable serial console in `raspi-config` before using UART.

---

## ⚖️ Load Cell (HX711)

```
VCC → 5V (Pin 2 or 4)
GND → GND
DT (Data) → GPIO 8 (Pin 24)
SCK (Clock) → GPIO 7 (Pin 26)

Load Cell Wires:
Red → E+
Black → E-
White → A-
Green → A+
```

---

## 💧 Float Switch

```
Signal → GPIO 11 (Pin 23)
GND → GND

Note: Use internal pull-up resistor
      LOW = Water present
      HIGH = No water
```

---

## 📷 Camera Module V2

```
Connect to CSI camera port (between HDMI ports)
Ribbon cable: Blue side faces USB ports
```

---

## 📊 Complete GPIO Pin Map

| GPIO | Pin | Function | Device |
|------|-----|----------|--------|
| 2 | 3 | SDA | I2C Bus (TCS34725, MPU6050, LCD) |
| 3 | 5 | SCL | I2C Bus (TCS34725, MPU6050, LCD) |
| 7 | 26 | OUT | HX711 Clock |
| 8 | 24 | IN | HX711 Data |
| 11 | 23 | IN | Float Switch |
| 12 | 32 | PWM | Conveyor Speed |
| 13 | 33 | PWM | Right Motor Speed |
| 14 | 8 | TX | GPS RX |
| 15 | 10 | RX | GPS TX |
| 17 | 11 | OUT | Left Motor IN1 |
| 18 | 12 | PWM | Left Motor Speed |
| 20 | 38 | OUT | Ultrasonic TRIG |
| 21 | 40 | IN | Ultrasonic ECHO |
| 22 | 15 | OUT | Right Motor IN1 |
| 23 | 16 | OUT | Right Motor IN2 |
| 24 | 18 | OUT | Conveyor IN1 |
| 25 | 22 | OUT | Conveyor IN2 |
| 27 | 13 | OUT | Left Motor IN2 |

---

## 🔋 Power Requirements

| Component | Voltage | Current | Notes |
|-----------|---------|---------|-------|
| Raspberry Pi 5 | 5V | 3-5A | Via USB-C or GPIO |
| Paddle Motors (2×) | 12V | ~2A each | Via L298N |
| Conveyor Motor | 12V | ~1A | Via L298N |
| TCS34725 | 3.3V | ~5mA | From Pi |
| MPU6050 | 3.3V | ~3.9mA | From Pi |
| GPS NEO-6M | 5V | ~50mA | From Pi |
| HX711 | 5V | ~10mA | From Pi |
| LCD Display | 5V | ~50mA | From Pi |
| Ultrasonic | 5V | ~15mA | From Pi |
| **Total** | - | **~10A peak** | 12V battery |

**Recommended Battery:** 12V, 20Ah (20000mAh) for ~4-6 hours runtime

---

## 🛠️ Assembly Tips

### 1. Common Ground
**CRITICAL:** Connect all grounds together:
- Battery GND
- Raspberry Pi GND
- Both L298N GND
- All sensor GND

### 2. Power Sequence
1. Connect battery to voltage regulator
2. Connect 5V output to Raspberry Pi
3. Connect 12V to motor drivers
4. Power on Pi first, then enable motors

### 3. I2C Pull-up Resistors
- Raspberry Pi has built-in pull-ups
- No external resistors needed for I2C
- If issues: Add 4.7kΩ resistors to SDA/SCL

### 4. Motor Driver Jumpers
- Remove 5V enable jumper on L298N
- Keep ENA/ENB jumpers for PWM control

### 5. UART Configuration
```bash
sudo raspi-config
→ Interface Options
→ Serial Port
→ Login shell: NO
→ Serial port hardware: YES
```

### 6. I2C Speed (Optional)
For faster I2C (400kHz):
```bash
sudo nano /boot/config.txt
# Add: dtparam=i2c_arm=on,i2c_arm_baudrate=400000
```

---

## 🧪 Testing Connections

### Test I2C Devices
```bash
i2cdetect -y 1
```
Should show:
- 0x27 (LCD)
- 0x29 (TCS34725)
- 0x68 (MPU6050)

### Test GPIO
```bash
# Test output pin (e.g., GPIO 17)
gpio -g mode 17 out
gpio -g write 17 1
gpio -g write 17 0

# Test input pin (e.g., GPIO 21)
gpio -g mode 21 in
gpio -g read 21
```

### Test UART (GPS)
```bash
cat /dev/serial0
# Should see NMEA sentences like:
# $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

### Test Camera
```bash
libcamera-hello -t 5000
# Should show camera preview for 5 seconds
```

---

## ⚠️ Safety Warnings

1. **Never hot-plug motors** - Stop all motors before connecting/disconnecting
2. **Check polarity** - Reverse polarity can damage components
3. **Fuse the battery** - Use 10A fuse on 12V line
4. **Waterproofing** - Use waterproof enclosure for electronics
5. **Heat dissipation** - L298N drivers get hot, ensure ventilation
6. **Emergency stop** - Have physical power switch accessible

---

## 🔍 Troubleshooting Wiring Issues

### Motors not spinning
- Check 12V power to L298N
- Verify IN1/IN2/ENA connections
- Test with `python3 motors.py`

### I2C device not detected
- Check SDA/SCL connections (not swapped)
- Verify 3.3V/5V power
- Check ground connection
- Try: `sudo i2cdetect -y 1`

### GPS not working
- Disable serial console in raspi-config
- Check TX/RX not swapped
- Wait 5-10 minutes for GPS fix (outdoors)
- Test: `cat /dev/serial0`

### Ultrasonic reading 0
- Check 5V power
- Verify TRIG/ECHO connections
- Ensure ECHO is 5V tolerant or use voltage divider

### Load cell reading incorrect
- Check wiring colors (may vary by manufacturer)
- Calibrate: adjust HX711_CALIBRATION_FACTOR
- Ensure stable mounting

---

## 📐 Physical Layout Suggestion

```
Top View of Robot (50×40 cm):

    [Camera]
    [TCS34725]
    [Ultrasonic]
    
[Left Motor]  [Raspberry Pi 5]  [Right Motor]
              [L298N #1]
              [L298N #2]
              [Battery]
              [HW-688]
              
    [Conveyor Motor]
    [Load Cell]
    [Float Switch]
    
[GPS Antenna on top]
[LCD Display on side panel]
```

---

## ✅ Final Checklist

Before powering on:
- [ ] All grounds connected together
- [ ] 12V battery charged and fused
- [ ] 5V regulator output verified
- [ ] No short circuits (multimeter test)
- [ ] All GPIO connections correct
- [ ] I2C devices on same bus
- [ ] Camera ribbon cable secure
- [ ] Motors free to rotate
- [ ] Emergency stop accessible

---

**Ready to wire! 🔌⚡**

For software setup, see **QUICKSTART.md** or **README.md**

