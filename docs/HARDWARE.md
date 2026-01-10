# Hardware Documentation

This document explains the ESP32 code and hardware setup from basics to advanced details.

## Part 1: Hardware Basics

### What is ESP32?

**ESP32** is a small, powerful microcontroller with built-in WiFi and Bluetooth.

**Think of it as**:
- A tiny computer that controls hardware
- Can read sensors (IR sensors, buttons)
- Can control outputs (servos, LEDs, buzzers)
- Can connect to internet via WiFi

**Why ESP32 for this project**:
- Built-in WiFi (easy server communication)
- Enough memory for our code (~520 KB RAM)
- Fast processor (240 MHz dual-core)
- Many GPIO pins for sensors/outputs
- Cheap ($5-10)

### Components You Need

| Component | Quantity | Purpose |
|-----------|----------|---------|
| ESP32 Dev Board | 1 | Main controller |
| IR Sensors | 2 | Count vehicles in/out |
| Servo Motor (SG90) | 1 | Control gate |
| 16x2 LCD Display | 1 | Show traffic info |
| Buzzer | 1 | Audio alerts |
| LEDs | 4 | Visual alerts |
| 220Ω Resistors | 4 | Protect LEDs |
| Breadboard | 1 | Connections |
| Jumper Wires | ~30 | Wiring |
| 5V Power Supply | 1 | Power servo |

**Total cost**: ~$20-30

### Pin Connections

```
ESP32 PIN → COMPONENT

IR Sensors:
  GPIO 34 → IR Sensor IN (signal pin)
  GPIO 35 → IR Sensor OUT (signal pin)
  3.3V → Both IR sensors (VCC)
  GND → Both IR sensors (GND)

Servo Motor:
  GPIO 13 → Servo signal (orange/yellow wire)
  5V → Servo VCC (red wire)
  GND → Servo GND (brown/black wire)

Buzzer:
  GPIO 12 → Buzzer positive
  GND → Buzzer negative

LEDs (with 220Ω resistors):
  GPIO 14 → LED 1 (anode/long leg) → Resistor → GND
  GPIO 27 → LED 2 (anode) → Resistor → GND
  GPIO 26 → LED 3 (anode) → Resistor → GND
  GPIO 25 → LED 4 (anode) → Resistor → GND

LCD Display:
  GPIO 19 → RS (Register Select)
  GPIO 23 → E (Enable)
  GPIO 18 → D4 (Data 4)
  GPIO 17 → D5 (Data 5)
  GPIO 16 → D6 (Data 6)
  GPIO 15 → D7 (Data 7)
  5V → VCC
  GND → GND
  Potentiometer → V0 (contrast control)
```

### Important Notes

**IR Sensors**:
- Have 3 pins: VCC (3.3V), GND, Signal
- Signal is HIGH when nothing detected
- Signal goes LOW when object detected
- Adjust sensitivity with onboard potentiometer

**Servo Motor**:
- Needs separate 5V power (ESP32 can't provide enough current)
- 0° = gate closed
- 90° = gate open
- Don't power from ESP32 3.3V pin (will damage ESP32)

**LCD Display**:
- Uses 6 data pins (RS, E, D4-D7)
- 4-bit mode (saves pins)
- Needs potentiometer for contrast adjustment
- Backlight can be always on (connect to 5V via resistor)

## Part 2: Code Structure Overview

### Main Components

```cpp
#include <WiFi.h>        // WiFi connectivity
#include <HTTPClient.h>  // HTTP requests to server
#include <ArduinoJson.h> // JSON parsing
#include <LiquidCrystal.h> // LCD control
#include <ESP32Servo.h>  // Servo control
```

### Key Variables

```cpp
int traffic[12];         // Stores 12 vehicle counts (60 seconds)
byte idx = 0;           // Current index in traffic array
int currentCount = 0;   // Vehicles in current 5-second window
int totalVehicles = 0;  // Total vehicles since last decision
bool gateOpen = false;  // Current gate state
```

### Timing System

```cpp
const unsigned long STEP_INTERVAL = 5000;    // Save count every 5 seconds
const unsigned long STRIDE_INTERVAL = 15000; // Make decision every 15 seconds
const unsigned long WINDOW_SIZE = 60000;     // 60 seconds of data
const byte POINTS_PER_WINDOW = 12;          // 12 data points in window
```

**How it works**:
- Every 5 seconds: Save vehicle count to array
- Every 15 seconds: Send all 12 counts to server for prediction
- Window covers 60 seconds (12 × 5 seconds)

## Part 3: Setup Function

### WiFi Configuration

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";
```

**What to change**:
- `YOUR_WIFI_SSID`: Your WiFi network name
- `YOUR_WIFI_PASSWORD`: Your WiFi password
- `YOUR_SERVER_IP`: Your computer's local IP (from `ipconfig`)

**Example**:
```cpp
const char* ssid = "MyHomeWiFi";
const char* password = "mypassword123";
const char* serverUrl = "http://192.168.1.100:5000/predict";
```

### Initialization Steps

```cpp
void setup() {
  Serial.begin(115200);  // Start serial communication (for debugging)
  
  // Configure pins
  pinMode(IR_SENSOR_IN, INPUT);
  pinMode(IR_SENSOR_OUT, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Setup LEDs
  for(int i = 0; i < 4; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);  // Start with LEDs off
  }
  
  // Setup servo
  servo.attach(SERVO_PIN);
  servo.write(0);  // Start with gate closed
  
  // Setup LCD
  lcd.begin(16, 2);  // 16 columns, 2 rows
  lcd.print("Traffic System");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  // Initialize traffic array
  for(int i = 0; i < 12; i++) {
    traffic[i] = 0;
  }
}
```

## Part 4: Main Loop

### Loop Structure

```cpp
void loop() {
  unsigned long now = millis();  // Current time in milliseconds
  
  // 1. Read IR sensors and count vehicles
  // 2. Save count every 5 seconds
  // 3. Make decision every 15 seconds
  // 4. Update display every 500ms
  
  delay(50);  // Small delay to prevent overwhelming CPU
}
```

### Vehicle Counting

```cpp
bool inState = digitalRead(IR_SENSOR_IN);
bool outState = digitalRead(IR_SENSOR_OUT);

// Vehicle entering
if (inState == LOW && lastInState == HIGH && (now - lastInTime > 300)) {
  currentCount++;
  totalVehicles++;
  lastInTime = now;
  
  tone(BUZZER_PIN, 1500);  // High beep
  delay(100);
  noTone(BUZZER_PIN);
}
```

**How it works**:
- IR sensor normally HIGH (nothing detected)
- When vehicle passes, goes LOW
- Detect transition: HIGH → LOW = vehicle detected
- `now - lastInTime > 300`: Debounce (ignore for 300ms to prevent double-counting)
- `currentCount++`: Add to current 5-second window
- `totalVehicles++`: Add to total count
- Beep to confirm detection

**Vehicle Exiting** (same logic but decrements counts):
```cpp
if (outState == LOW && lastOutState == HIGH && (now - lastOutTime > 300)) {
  if (currentCount > 0) currentCount--;
  if (totalVehicles > 0) totalVehicles--;
  
  tone(BUZZER_PIN, 800);  // Lower beep
  delay(100);
  noTone(BUZZER_PIN);
}
```

### Saving Counts

```cpp
if (now - lastSave >= STEP_INTERVAL) {  // Every 5 seconds
  traffic[idx] = currentCount;  // Save current count
  
  Serial.print("Saved count at index ");
  Serial.print(idx);
  Serial.print(": ");
  Serial.println(currentCount);
  
  idx = (idx + 1) % 12;  // Move to next index (wraps to 0 after 11)
  currentCount = 0;      // Reset for next 5-second window
  lastSave = now;        // Update timestamp
}
```

**Circular Buffer**:
- Array has 12 slots
- `idx` points to current position
- `(idx + 1) % 12` wraps around: 0→1→2→...→11→0→1...
- Always keeps last 60 seconds of data

### Making Decisions

```cpp
if (now - lastDecision >= STRIDE_INTERVAL) {  // Every 15 seconds
  makeDecision();
  lastDecision = now;
  totalVehicles = 0;  // Reset total count
}
```

## Part 5: Decision Function

### Preparing Window Data

```cpp
void makeDecision() {
  // Create window with data in correct order
  int window[12];
  for(int i = 0; i < 12; i++) {
    byte actualIdx = (idx - 12 + i + 12) % 12;
    window[i] = traffic[actualIdx];
  }
```

**Why this math**:
- `idx` is where we'll write NEXT
- We need the LAST 12 values
- `idx - 12` would be 12 positions back
- `+ i` moves forward through the window
- `+ 12` and `% 12` handles negative wraparound

**Example**:
```
If idx = 5, we want indices: 5,6,7,8,9,10,11,0,1,2,3,4
(idx - 12 + 0 + 12) % 12 = 5
(idx - 12 + 1 + 12) % 12 = 6
...
(idx - 12 + 11 + 12) % 12 = 4
```

### Creating JSON Request

```cpp
HTTPClient http;
http.begin(serverUrl);
http.addHeader("Content-Type", "application/json");

StaticJsonDocument<512> doc;
JsonArray counts = doc.createNestedArray("counts");
for(int i = 0; i < 12; i++) {
  counts.add(window[i]);
}

String jsonData;
serializeJson(doc, jsonData);
```

**Creates JSON**:
```json
{
  "counts": [5, 7, 6, 8, 7, 6, 5, 7, 8, 6, 7, 6]
}
```

### Sending Request

```cpp
int httpCode = http.POST(jsonData);

if (httpCode == 200) {  // Success
  String response = http.getString();
  
  StaticJsonDocument<512> responseDoc;
  deserializeJson(responseDoc, response);
  
  const char* prediction = responseDoc["prediction"];
  float confidence = responseDoc["confidence"];
  bool shouldOpen = responseDoc["open_lane"];
```

**Error Handling**:
```cpp
} else {
  Serial.print("Server error: ");
  Serial.println(httpCode);
  lcd.clear();
  lcd.print("Server Error");
}

http.end();  // Always close connection
```

### Acting on Prediction

```cpp
if (shouldOpen != gateOpen) {  // State needs to change
  if (shouldOpen) {
    openGate();
  } else {
    closeGate();
  }
} else {  // Already in correct state
  lcd.clear();
  lcd.print(gateOpen ? "Keep Open" : "Keep Closed");
}
```

## Part 6: Gate Control Functions

### Opening Gate

```cpp
void openGate() {
  Serial.println("Opening gate");
  
  // Flash LEDs and beep 5 times
  for(int i = 0; i < 5; i++) {
    // Turn all LEDs on
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], HIGH);
    }
    tone(BUZZER_PIN, 1000);
    delay(300);
    
    // Turn all LEDs off
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], LOW);
    }
    noTone(BUZZER_PIN);
    delay(300);
  }
  
  // Display message
  lcd.clear();
  lcd.print("Opening Gate");
  
  // Slowly rotate servo from 0° to 90°
  for(int pos = 0; pos <= 90; pos++) {
    servo.write(pos);
    delay(15);  // Smooth movement
  }
  
  gateOpen = true;
}
```

**Closing Gate** (same but reverse servo):
```cpp
void closeGate() {
  // ... same LED/buzzer pattern ...
  
  // Rotate servo from 90° back to 0°
  for(int pos = 90; pos >= 0; pos--) {
    servo.write(pos);
    delay(15);
  }
  
  gateOpen = false;
}
```

### Display Update

```cpp
void updateDisplay(unsigned long now) {
  lcd.clear();
  
  // Line 1: Vehicle count
  lcd.print("Vehicles: ");
  lcd.print(totalVehicles);
  
  // Line 2: Gate status and countdown
  lcd.setCursor(0, 1);
  lcd.print("Gate: ");
  lcd.print(gateOpen ? "OPEN" : "CLOSED");
  
  // Countdown to next decision
  unsigned long timeToNext = STRIDE_INTERVAL - (now - lastDecision);
  lcd.setCursor(12, 1);
  lcd.print(timeToNext / 1000);
  lcd.print("s");
}
```

**Display shows**:
```
Vehicles: 12
Gate: OPEN    5s
```

## Part 7: Testing the Hardware

### Test 1: Serial Monitor

1. Upload code to ESP32
2. Open Serial Monitor (Tools → Serial Monitor)
3. Set baud rate to 115200
4. Press reset button

**Expected output**:
```
Connecting to WiFi
..
WiFi connected
IP: 192.168.1.50
System ready
```

### Test 2: IR Sensors

Wave hand over sensors, Serial Monitor should show:
```
Vehicle IN. Total: 1
Saved count at index 0: 1
Vehicle OUT. Total: 0
```

**If not detecting**:
- Check wiring (VCC, GND, signal)
- Adjust sensor potentiometer (sensitivity)
- Check if LED on sensor lights up

### Test 3: LCD Display

Should show:
```
Vehicles: 0
Gate: CLOSED  15s
```

**If blank**:
- Adjust contrast potentiometer
- Check wiring (especially RS, E, D4-D7)
- Verify 5V power connected

### Test 4: Servo

After 15 seconds, servo should move (if prediction says to open).

**If not moving**:
- Check separate 5V power supply
- Verify signal wire on GPIO 13
- Test with simple code:
```cpp
servo.write(90);
delay(1000);
servo.write(0);
```

### Test 5: LEDs and Buzzer

When gate opens/closes:
- LEDs should flash 5 times
- Buzzer should beep 5 times

**If not working**:
- Check resistors on LEDs (220Ω)
- Verify polarity (long leg = anode = positive)
- Test buzzer with simple `tone()` call

## Part 8: Common Problems

### Problem: WiFi Won't Connect

**Check**:
1. SSID and password correct (case-sensitive)
2. ESP32 and router on 2.4 GHz (ESP32 doesn't support 5 GHz)
3. Try different WiFi network
4. Move closer to router

**Debug**:
```cpp
Serial.println(WiFi.status());
// WL_CONNECTED = 3
// WL_NO_SSID_AVAIL = 1 (wrong network name)
// WL_CONNECT_FAILED = 4 (wrong password)
```

### Problem: Can't Reach Server

**Check**:
1. Server running on computer
2. Computer and ESP32 on same WiFi network
3. Server IP correct (use `ipconfig` to verify)
4. Windows Firewall not blocking port 5000

**Debug**:
```cpp
Serial.print("HTTP Code: ");
Serial.println(httpCode);
// 200 = Success
// -1 = Connection failed
// 404 = Wrong URL
// 500 = Server error
```

### Problem: Double Counting Vehicles

**Cause**: IR sensor triggered multiple times for one vehicle

**Solution**: Increase debounce delay
```cpp
if (now - lastInTime > 500) {  // Increase from 300 to 500
```

### Problem: Servo Jittery

**Cause**: Not enough power or shared power with ESP32

**Solution**:
- Use separate 5V power supply for servo
- Add 100µF capacitor across servo power pins
- Ensure common ground between ESP32 and servo power

### Problem: LCD Shows Garbage Characters

**Causes**:
1. Wrong contrast setting
2. Loose wiring
3. Wrong pin assignments

**Solutions**:
- Adjust contrast potentiometer
- Check all 6 data pin connections
- Verify RS and E pins correct

### Problem: Predictions Always Same

**Check**:
1. IR sensors actually detecting (check Serial Monitor)
2. Counts being saved to array
3. Server receiving correct data
4. Print window array before sending

**Debug**:
```cpp
Serial.print("Window: ");
for(int i = 0; i < 12; i++) {
  Serial.print(window[i]);
  if(i < 11) Serial.print(", ");
}
Serial.println();
```

## Part 9: Understanding the Code Flow

### Complete Cycle (15 seconds)

**Seconds 0-5**:
- Count vehicles: 5 vehicles detected
- Save to `traffic[0] = 5`
- Display updates every 500ms

**Seconds 5-10**:
- Count vehicles: 7 vehicles detected
- Save to `traffic[1] = 7`
- Display shows countdown

**Seconds 10-15**:
- Count vehicles: 6 vehicles detected
- Save to `traffic[2] = 6`
- Display countdown reaches 0

**At 15 seconds**:
- Collect all 12 counts from array
- Send to server
- Get prediction
- Open/close gate if needed
- Reset total count
- Start next cycle

### Memory Usage

```cpp
int traffic[12];        // 12 × 2 bytes = 24 bytes
String jsonData;        // ~100 bytes
StaticJsonDocument<512> // 512 bytes
Total: ~650 bytes (out of 520 KB available)
```

Very efficient! ESP32 has plenty of memory left.

### Timing Analysis

**Why these intervals**:
- 5 seconds: Balance between resolution and data amount
- 15 seconds: Fast enough to react, slow enough to gather data
- 60 seconds total window: Captures traffic pattern without being too old

**Can you change them?**
Yes! But adjust all three together:
```cpp
STEP_INTERVAL = 10000;    // 10 seconds
STRIDE_INTERVAL = 30000;  // 30 seconds
WINDOW_SIZE = 120000;     // 120 seconds
POINTS_PER_WINDOW = 12;   // Still 12 points
```

## Part 10: Defense Questions

**Q: Why use ESP32 instead of Arduino?**
A: ESP32 has built-in WiFi, more memory, faster processor, and costs about the same. Arduino would need separate WiFi module.

**Q: How does vehicle counting work?**
A: IR sensors detect when beam is broken. We detect HIGH→LOW transition and debounce for 300ms to prevent double-counting.

**Q: Why circular buffer for traffic array?**
A: Efficiently stores last 60 seconds of data without shifting array elements. Uses modulo operator to wrap around.

**Q: What happens if WiFi disconnects?**
A: System keeps counting vehicles locally. When decision time comes, it checks WiFi status and shows error if disconnected. Counts preserved.

**Q: Why separate power for servo?**
A: Servo draws high current (up to 1A). ESP32's 3.3V pin can only provide ~50mA. Separate 5V prevents ESP32 brownout/reset.

**Q: How accurate is vehicle counting?**
A: Depends on sensor placement and speed. With proper setup and debouncing, 95%+ accuracy. Two sensors (in/out) helps track net count.

**Q: Can you run this without the server?**
A: Not currently - the ML model is on server. Could convert model to TensorFlow Lite and run on ESP32, but would need significant code changes.

**Q: Why JSON instead of simple text?**
A: JSON is standard, easy to parse, extensible. Could add more fields later without breaking compatibility. Both Arduino and Python have good JSON libraries.

## Part 11: Going Further

### Add More Sensors
```cpp
const int EXTRA_IR = 32;
// Count vehicles on additional lanes
```

### Add Temperature Sensor
```cpp
#include <DHT.h>
// Monitor if extreme weather affects traffic
```

### Add RTC Module
```cpp
#include <RTClib.h>
// Keep accurate time even without WiFi
```

### Log to SD Card
```cpp
#include <SD.h>
// Store traffic data locally for analysis
```

### Web Dashboard
Create simple webpage served by ESP32:
```cpp
#include <WebServer.h>
WebServer server(80);
// Show real-time stats in browser
```

### OLED Display
```cpp
#include <Adafruit_SSD1306.h>
// Better graphics, shows charts
```

### Mobile App Control
Use Blynk or similar:
```cpp
#include <BlynkSimpleEsp32.h>
// Control from phone app
```

### Power Optimization
```cpp
esp_sleep_enable_timer_wakeup(15 * 1000000);  // Sleep between decisions
// Battery operation for remote deployment
```