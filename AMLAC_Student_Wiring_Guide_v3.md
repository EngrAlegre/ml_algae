# AMLAC Robot - Student Wiring Guide v3.0
## Step-by-Step Instructions for Easy Understanding

---

## 🎯 AMLAC ROBOT - STUDENT WIRING GUIDE

**Version:** 3.0 (December 2025)  
**For:** AMLAC Robot on Raspberry Pi 5  
**Student Level:** Beginner - Easy to follow, no experience needed  

---

## 🎯 PROJECT OVERVIEW

The **AMLAC Robot** detects algae in water and collects it automatically:
- **Paddle wheels** - move the robot forward and backward
- **Conveyor belt** - collects the algae
- **Sensors** - detect water color, distance, weight, water level, GPS location
- **Camera** - takes pictures to detect algae using AI
- **Display** - shows what's happening on a small screen

**What You Will Build:** A complete water filtration robot controlled by a Raspberry Pi 5!

---

## 📋 PARTS YOU WILL NEED

### Main Control & Power
- 1× Raspberry Pi 5 (4GB) - brain of the robot
- 1× 12V Battery (20000 mAh Alephy) - power source
- 1× HW-688 5V Voltage Regulator - converts 12V to 5V for safe power

### Motors & Motor Drivers
- 2× 12V DC Motors, 37 RPM (for paddle wheels - left and right)
- 1× 12V DC Motor, 188 RPM (for conveyor belt)
- 2× L298N Motor Drivers (controls the 3 motors)

### Sensors (These measure things)
- 1× TCS34725 RGB Color Sensor - detects green algae color
- 1× MPU6050 IMU Sensor - detects tilt and movement
- 1× JSN-SR04T Ultrasonic Sensor - measures distance to obstacles
- 1× NEO-6M GPS Module - records location
- 1× HX711 with Load Cell - measures how much algae collected
- 1× Float Switch - detects if there is water

### Display & Camera
- 1× LCD 16×2 I2C Display - shows robot status
- 1× Raspberry Pi Camera V2 - takes pictures for AI

### Wiring & Connecting Tools
- **50-60 Female-to-Female Jumper Wires (20 cm)** - ALL connections use these
- **Wire Strippers** - tool to remove plastic from wires
- **Electrical Tape (black)** - secure twisted connections
- **Multimeter** - test wires for safety

---

## 🔌 QUICK PIN MAP

| Connection | From Pi | To Devices | Wires to Twist |
|-----------|---------|-----------|----------------|
| **I2C SDA (GPIO2)** | Pin 3 | TCS34725, MPU6050, LCD | **4 BLUE wires** |
| **I2C SCL (GPIO3)** | Pin 5 | TCS34725, MPU6050, LCD | **4 YELLOW wires** |
| **+5V Power** | Pin 2 or 4 | All 6 sensors | **7 RED wires** |
| **GND (Ground)** | Pin 6,9,14... | Everything ⚠️ MOST IMPORTANT! | **10-12 BLACK wires** |

---

## ⚠️ BEFORE YOU START - SAFETY RULES

**STOP! Read these rules carefully:**

1. **Never plug Raspberry Pi into power while wiring** - Always disconnect first!
2. **Always check wires are the right color BEFORE connecting** - Color matters!
3. **Double-check GND (ground) connections** - This is MOST important!
4. **Use wire strippers gently** - Don't break or crush the wire
5. **Keep wires organized and not tangled** - This prevents mistakes
6. **Ask your teacher if you are unsure** - Don't guess about electrical connections!

---

# 🛠️ BUILDING STEPS (FOLLOW IN ORDER!)

---

## STEP 1: Prepare Your Wires

### What you need:
- 50-60 female-to-female jumper wires
- Wire strippers

### How to do it:

**Step 1.1:** Get a pile of jumper wires and organize them

**Step 1.2:** Separate wires by color:
- Take 4 BLUE wires for GPIO2 (SDA) connections
- Take 4 YELLOW wires for GPIO3 (SCL) connections  
- Take 7 RED wires for +5V power connections
- Take 12 BLACK wires for GND (ground) connections
- Keep other colors for individual sensor connections

**Step 1.3:** Label your wire bundles with small pieces of tape:
- Blue wires: Write "GPIO2 SDA"
- Yellow wires: Write "GPIO3 SCL"
- Red wires: Write "+5V"
- Black wires: Write "GND"

✅ **Result:** Your wires are organized and ready!

---

## STEP 2: Strip the Wires (Remove Plastic Covering)

### What you need:
- Wire strippers
- The wire bundles you prepared in Step 1

### How to do it:

**FOR GPIO2 (BLUE) AND GPIO3 (YELLOW) WIRES:**

Step 1: Take one blue wire
Step 2: Put the end (about 1.5-2 cm) into the wire stripper
Step 3: Squeeze the stripper gently and twist
Step 4: Pull the stripper off - the plastic should come off
Step 5: Look at the end - you should see bare copper wire
Step 6: Repeat for all 4 blue wires
Step 7: Do the same process for all 4 yellow wires

**FOR +5V (RED) AND GND (BLACK) WIRES:**

Same process - strip 1.5-2 cm from each wire end:
- Red wires: 7 wires stripped
- Black wires: 12 wires stripped

✅ **Result:** Each wire has bare copper showing at the end

---

## STEP 3: Twist GPIO2 (SDA) Connection - 4 Blue Wires

### What you need:
- 4 stripped blue wires
- Electrical tape

### Where these wires go:

From Raspberry Pi GPIO2 (Pin 3) TO:
- TCS34725 SDA
- MPU6050 SDA
- LCD SDA

= 4 wires total

### How to twist them:

**METHOD 1: Hand Twist (Easy)**

1. Hold all 4 blue wire ends in one hand
   - Make them parallel (pointing the same direction)
   - All ends should be even

2. Use your other hand to twist clockwise (rotate to the right)
   - Twist slowly and carefully
   - Don't pull too hard

3. Keep twisting until the wires are tightly wrapped around each other
   - You need about 5-8 full rotations
   - The wires should be difficult to pull apart

4. Test the twist - try to pull one wire out
   - It should NOT move at all
   - If it moves, twist more!

5. Wrap with electrical tape:
   - Start wrapping 1 cm before the twist
   - Wrap the tape around 2-3 times
   - Overlap the tape by 50% as you wrap (half old, half new)
   - End the tape 1 cm after the twist
   - The tape should completely cover the twisted part

**METHOD 2: Drill Twist (Stronger - Ask Teacher First)**

1. Hold all 4 wires together, parallel
2. Put the wire ends into the drill chuck (like holding a pencil)
3. Set the drill to slow speed (200 RPM)
4. Start the drill - it will twist the wires for you
5. Stop after 3-5 seconds
6. Carefully remove the wires from the drill
7. Wrap with electrical tape (same as above)

✅ **Result:** All 4 blue wires permanently connected together

---

## STEP 4: Twist GPIO3 (SCL) Connection - 4 Yellow Wires

### What you need:
- 4 stripped yellow wires
- Electrical tape

### Where these wires go:

From Raspberry Pi GPIO3 (Pin 5) TO:
- TCS34725 SCL
- MPU6050 SCL
- LCD SCL

= 4 wires total

### How to do it:
**Same as STEP 3 above, but use yellow wires instead of blue wires**

✅ **Result:** All 4 yellow wires permanently connected together

---

## STEP 5: Twist +5V Power Bus - 7 Red Wires

### What you need:
- 7 stripped red wires
- Electrical tape

### Where these wires go:

From Raspberry Pi +5V (Pin 2 or Pin 4) TO:
- TCS34725 VCC (power)
- MPU6050 VCC (power)
- LCD VCC (power)
- NEO-6M GPS VCC (power)
- HX711 VCC (power)
- JSN-SR04T VCC (power)
- Extra wire (backup power)

= 7 wires total

### How to twist them:

**Same as STEP 3, but with 7 red wires**

Note: This bundle will be thicker because it has more wires. You need more twisting (maybe 8-10 rotations) to make it tight.

✅ **Result:** All 7 red wires permanently connected together

---

## STEP 6: Twist GND (Ground) - 10-12 Black Wires

### ⚠️ THIS IS THE MOST IMPORTANT CONNECTION! ⚠️

If this connection is loose or broken, the robot will NOT work!

### What you need:
- 12 stripped black wires
- Electrical tape (or heat shrink tube is even better)

### Where these wires go:

From Raspberry Pi GND (Pins 6, 9, 14, 20, 25, 30, 34, 39) TO:
- TCS34725 GND
- MPU6050 GND
- LCD GND
- NEO-6M GND
- HX711 GND
- JSN-SR04T GND
- Float Switch GND
- L298N #1 GND
- L298N #2 GND
- Battery GND (negative terminal)
- Plus 2 extra backup wires

= 10-12 wires total

### How to twist them:

**Step 1:** Strip all 12 black wires (1.5-2 cm each)

**Step 2:** TWIST VERY TIGHTLY:
- Hold all 12 wire ends together in one hand
- Use other hand to twist clockwise
- Twist HARD and count: 8, 9, 10 full rotations
- Use drill method if possible for a stronger twist (200 RPM, 5 seconds)

**Step 3:** TEST - Try to pull each wire:
- Grab each individual wire and try to pull it out
- No wire should move at all
- If any wire moves, twist the bundle more!

**Step 4:** Wrap with electrical tape:
- Use 3-4 layers of tape (more layers = more protection)
- OR use heat shrink tube (better - more professional)
- Make sure the entire twisted part is covered

**Step 5:** Double-check:
- This is the most important connection!
- If this connection is loose, the robot won't work!
- Test it one more time - try to pull each wire

✅ **Result:** All 12 black wires permanently connected together

---

## STEP 7: Connect Motor Control Wires (Individual)

### ⚠️ These wires go ONE by ONE (not twisted)

### Motor Driver #1 (Controls Paddle Wheels) - 6 wires:

| Connection | From Pi GPIO | Color | Function |
|-----------|------------|-------|----------|
| L298N #1 IN1 | GPIO17 | Orange | Left paddle direction |
| L298N #1 IN2 | GPIO27 | Orange | Left paddle direction |
| L298N #1 ENA | GPIO18 | Orange | Left paddle speed |
| L298N #1 IN3 | GPIO22 | Purple | Right paddle direction |
| L298N #1 IN4 | GPIO23 | Purple | Right paddle direction |
| L298N #1 ENB | GPIO13 | Purple | Right paddle speed |

### How to connect:

1. Get 6 individual wires (use colors shown in table above)
2. Strip both ends of each wire (1-1.5 cm)
3. Take the first wire:
   - One end plugs into Raspberry Pi GPIO17 pin
   - Other end plugs into L298N #1 IN1 pin
4. Check that it's tight and not loose
5. Move to the next wire
6. Repeat for all 6 wires

### Motor Driver #2 (Controls Conveyor Belt) - 3 wires:

| Connection | From Pi GPIO | Color | Function |
|-----------|------------|-------|----------|
| L298N #2 IN1 | GPIO24 | Green | Conveyor direction |
| L298N #2 IN2 | GPIO25 | Green | Conveyor direction |
| L298N #2 ENA | GPIO12 | Green | Conveyor speed |

### How to connect:
Same as above, but only 3 wires

✅ **Result:** Motor drivers are connected to Raspberry Pi

---

## STEP 8: Connect Individual Sensor Wires

### ⚠️ These also go ONE by ONE (not twisted)

### GPS Module (NEO-6M) - 2 wires:

| Connection | From Pi GPIO | Color | Function |
|-----------|------------|-------|----------|
| GPS RX | GPIO15 (Pin 10) | Blue | Receive GPS data |
| GPS TX | GPIO14 (Pin 8) | Green | Send to GPS |

**How to connect:**
1. Get 2 wires (blue and green)
2. Strip both ends
3. Blue wire: One end → Pi GPIO15, Other end → GPS RX
4. Green wire: One end → Pi GPIO14, Other end → GPS TX
5. Check both connections are tight

---

### Load Cell Amplifier (HX711) - 2 wires:

| Connection | From Pi GPIO | Color | Function |
|-----------|------------|-------|----------|
| HX711 CLK | GPIO7 (Pin 26) | White | Clock signal |
| HX711 DATA | GPIO8 (Pin 24) | Gray | Data signal |

**How to connect:**
Same process as GPS above

---

### Distance Sensor (JSN-SR04T) - 2 wires:

| Connection | From Pi GPIO | Color | Function |
|-----------|------------|-------|----------|
| JSN Trigger | GPIO20 (Pin 38) | Brown | Send trigger pulse |
| JSN Echo | GPIO21 (Pin 40) | Brown | Receive echo back |

**How to connect:**
Same process as GPS above

---

### Float Switch (Water Level) - 1 wire:

| Connection | From Pi GPIO | Color | Function |
|-----------|------------|-------|----------|
| Float NO | GPIO11 (Pin 23) | Pink | Water detection |

**How to connect:**
Same process, but only 1 wire

✅ **Result:** All sensors are connected to Raspberry Pi

---

## STEP 9: Connect the 12V Power (Thick Wires)

### What you need:
- 2 thick red wires (16 AWG gauge) - for +12V
- 2 thick black wires (16 AWG gauge) - for GND

### How to connect:

**From 12V Battery:**

Plus terminal (+12V RED):
- Wire 1 → L298N #1 VIN pin
- Wire 2 → L298N #2 VIN pin
- Wire 3 → HW-688 Regulator INPUT +12V

Minus terminal (GND BLACK):
- Wire 1 → L298N #1 GND (connect to your black twist bundle)
- Wire 2 → L298N #2 GND (connect to your black twist bundle)
- Wire 3 → HW-688 Regulator INPUT GND (connect to your black twist bundle)

### Safety Tips:
- Use XT60 connectors or Anderson connectors (easier and safer)
- DO NOT touch bare 12V wires to each other
- DO NOT connect 12V directly to Raspberry Pi - you will break it!

✅ **Result:** Motor power is connected

---

## STEP 10: Connect 5V Regulator Output

### What you need:
- Your twisted +5V red wires bundle (from STEP 5)
- Your twisted GND black wires bundle (from STEP 6)

### How to connect:

From HW-688 Regulator OUTPUT:
- +5V (red output) → Your RED wires twist bundle (7 wires)
- GND (black output) → Your BLACK wires twist bundle (10-12 wires)

**What happens:** The regulator takes 12V and safely converts it to 5V, then sends it to all the sensors!

✅ **Result:** Sensors have safe 5V power

---

## STEP 11: Connect Camera & LCD Display

### Raspberry Pi Camera:

Connect to Camera Port on Pi (NOT GPIO pins):

1. The camera ribbon cable goes into the special camera port (not the GPIO pins)
2. Gently pull the plastic clip UP (towards the Pi)
3. Slide the ribbon cable in fully (shiny side down)
4. Push the plastic clip DOWN firmly

### LCD Display (I2C):

Connect to your twisted GPIO2/3 bundles:

- LCD SDA → Blue GPIO2 twist (from STEP 3)
- LCD SCL → Yellow GPIO3 twist (from STEP 4)
- LCD VCC → Red +5V twist (from STEP 5)
- LCD GND → Black GND twist (from STEP 6)

✅ **Result:** All connections complete!

---

# ✅ TESTING YOUR WIRING

## Do This BEFORE Plugging In!

---

## Test 1: Check All Twisted Connections (Physical Check)

For each twist point (GPIO2, GPIO3, +5V, GND):

1. Look at the twisted connection
   - It should look like all wires are wrapped together
   - Tape should completely cover the twist

2. Try to pull each individual wire gently
   - Grab one wire and try to yank it out
   - It should NOT move at all
   - If it moves, the twist is too loose - redo it!

3. Check the tape is covering the twisted part
   - No bare copper should be showing
   - If you see bare copper, add more tape

✅ **Pass:** All twisted wires are tight and taped

---

## Test 2: Use Multimeter to Check Connections (Most Important!)

You need a **multimeter** for this test (cheap at hardware store).

### Test GPIO2 (SDA) Connection:

1. Set multimeter to **CONTINUITY** or **OHMS** mode
2. Touch the black probe to Raspberry Pi GPIO2 pin
3. Touch the red probe to TCS34725 SDA pin
4. **Multimeter should BEEP** (that means continuity = good!)
5. Repeat for:
   - MPU6050 SDA pin (should beep)
   - LCD SDA pin (should beep)

If any don't beep, the wire is loose - go back and re-twist!

### Test GPIO3 (SCL) Connection:

Same as above, but check GPIO3 pin:
- Beep to TCS34725 SCL
- Beep to MPU6050 SCL
- Beep to LCD SCL

### Test +5V Power:

1. Set multimeter to **VOLTAGE** mode
2. Touch the black probe to GND (black twist bundle)
3. Touch the red probe to +5V twisted bundle
4. **Should read about 5.0 volts**
5. If it shows less than 4.8V, check the HW-688 regulator
6. If it shows 0V, check that the regulator is powered

### Test GND (Most Important!):

1. Set multimeter to **CONTINUITY** or **OHMS** mode
2. Touch the black probe to Raspberry Pi GND pin
3. Touch the red probe to each device GND:
   - TCS34725 GND (should beep)
   - MPU6050 GND (should beep)
   - LCD GND (should beep)
   - Motor driver L298N #1 GND (should beep)
   - Motor driver L298N #2 GND (should beep)
   - Battery GND (should beep)

**ALL should BEEP (continuity with everything!)**

If any don't beep, you found a loose connection - fix it!

✅ **Pass:** All continuity tests pass

---

## Test 3: Check for Shorts (Safety - Important!)

A "short circuit" is when +5V accidentally touches GND. This is BAD!

1. Set multimeter to **CONTINUITY** or **OHMS** mode
2. Touch one probe to +5V red wire
3. Touch other probe to GND black wire
4. **Should NOT beep** (open circuit = good!)
5. If it BEEPS, you have a SHORT CIRCUIT!
   - STOP immediately!
   - Find where red wire touched black wire by mistake
   - Use electrical tape to separate them
   - Re-test

✅ **Pass:** No short circuits found

---

# 🔍 TROUBLESHOOTING - Common Problems

| Problem | What Might Be Wrong | How to Fix |
|---------|-------------------|-----------|
| Multimeter won't beep on GPIO2 | SDA twist too loose | Go back to STEP 3 and re-twist the 4 blue wires tighter |
| Multimeter shows 0V instead of 5V | Regulator not working or not powered | Check 12V battery is connected to regulator INPUT |
| Everything loose and falling apart | Tape not holding | Use heat shrink tube instead (ask teacher) - it's permanent |
| One sensor doesn't work | Wrong GPIO pin number | Check the chart again - count pins carefully |
| Robot won't turn on at all | GND not connected properly | Go back to STEP 6 - re-twist all 12 black GND wires VERY tight |
| Raspberry Pi won't boot up | 5V power problem | Use multimeter to check HW-688 output voltage (should be ~5.0V) |
| Motors make noise but don't spin | Motor wires reversed on motor | Swap the two power wires on the motor to reverse it |
| Only one I2C sensor detected | SDA/SCL twist not tight enough | Go back to STEP 3 and STEP 4 - re-twist the blue and yellow twists |
| Camera not working | Camera ribbon not inserted fully | Pull plastic clip, re-insert ribbon, push clip down hard |
| LCD screen blank | I2C connection problem | Check multimeter beeps for GPIO2 and GPIO3 |

---

# 📊 FINAL CHECKLIST - Before Plugging In!

**Before you connect the Raspberry Pi to power, check ALL of these boxes:**

## Power & Ground:
- [ ] 12V battery connected to both L298N motor drivers
- [ ] 12V battery connected to HW-688 regulator INPUT
- [ ] HW-688 regulator measures ~5V output (tested with multimeter)
- [ ] GND (black) wires twisted together VERY tightly
- [ ] No red 12V wires accidentally touching black GND wires

## GPIO Connections (Twisted Bundles):
- [ ] GPIO2 (blue) - 4 wires twisted and taped (STEP 3)
- [ ] GPIO3 (yellow) - 4 wires twisted and taped (STEP 4)
- [ ] +5V (red) - 7 wires twisted and taped (STEP 5)
- [ ] GND (black) - 12 wires twisted and taped (STEP 6)

## Individual Wires:
- [ ] Motor drivers connected to correct GPIO pins (STEP 7)
- [ ] GPS connected to GPIO14/15 (STEP 8)
- [ ] Load cell connected to GPIO7/8 (STEP 8)
- [ ] Distance sensor connected to GPIO20/21 (STEP 8)
- [ ] Float switch connected to GPIO11 (STEP 8)
- [ ] All connections are snug and not loose

## I2C Sensors (Shared SDA/SCL):
- [ ] TCS34725 connected to GPIO2/3 twisted bundle
- [ ] MPU6050 connected to GPIO2/3 twisted bundle
- [ ] LCD connected to GPIO2/3 twisted bundle

## Final Checks:
- [ ] All wires organized and not tangled
- [ ] No wires broken or damaged
- [ ] All tape/heat shrink is holding connections tight
- [ ] Multimeter tests PASSED for all connections
- [ ] No short circuits between +5V and GND
- [ ] **TEACHER HAS APPROVED YOUR WORK**

---

# 🚀 NOW YOU'RE READY!

Once you pass all the tests above, you can:

1. **Plug Raspberry Pi into power** - it should boot up
2. **Connect 12V battery** - motors and sensors get power
3. **The system should start up** - LCD display should turn on
4. **Run the Python code** to test motors and sensors

**Congratulations! You built a robot!**

---

# 📚 WHAT EACH PART DOES

### **Raspberry Pi 5**
The brain of the robot - runs the AI program that controls everything

### **Motors & Drivers:**

**L298N #1:** Controls left and right paddle wheels
- Paddle wheels push the robot forward and backward through water

**L298N #2:** Controls conveyor belt motor
- Conveyor belt collects algae as the robot moves

### **Sensors:**

**TCS34725 RGB Color Sensor:** Sees green color = algae is here
- Scans water to find green algae

**MPU6050 IMU Sensor:** Knows if robot is tilted or moving
- Measures tilt and movement to keep robot balanced

**JSN-SR04T Ultrasonic Sensor:** Measures distance so robot doesn't crash
- Detects obstacles in front of robot

**NEO-6M GPS Module:** Records where algae was found
- Saves location coordinates of collection sites

**HX711 with Load Cell:** Measures weight of collected algae
- Tells how much algae has been collected

**Float Switch:** Checks if there's water (safety sensor)
- Prevents motor from running if not in water

### **Display & Camera:**

**LCD Screen:** Shows status messages
- Displays what the robot is doing

**Camera:** Takes pictures for AI to check for algae
- AI analyzes photos to identify algae types

---

# 📞 NEED HELP?

If something doesn't work:
1. Check the Troubleshooting chart
2. Use multimeter to test connections
3. Ask your teacher
4. Don't guess about electrical connections!

---

**Document Version:** 3.0 (Student Edition)  
**Last Updated:** December 4, 2025  
**Difficulty Level:** Beginner - Follow each step carefully!  

**Remember: Safety First! Good luck building your robot! 🚀**