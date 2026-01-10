# Hardware Documentation

This document explains the ESP32 code and hardware setup from basics to advanced details.

## Part 1: Hardware Basics

### What is ESP32?

ESP32 is a small, powerful microcontroller with built-in WiFi and Bluetooth.

Think of it as a tiny computer that controls hardware, reads sensors, controls outputs, and connects to internet via WiFi.

Why ESP32 for this project:

- Built-in WiFi (easy server communication)
- Enough memory for our code (520 KB RAM)
- Fast processor (240 MHz dual-core)
- Many GPIO pins for sensors/outputs
- Cheap ($5-10)

### Components You Need

| Component          | Quantity | Purpose               |
| ------------------ | -------- | --------------------- |
| ESP32 Dev Board    | 1        | Main controller       |
| IR Sensors         | 2        | Count vehicles in/out |
| Servo Motor (SG90) | 1        | Control gate          |
| 16x2 LCD Display   | 1        | Show traffic info     |
| Buzzer             | 1        | Audio alerts          |
| LEDs               | 4        | Visual alerts         |
| 220Ω Resistors     | 4        | Protect LEDs          |
| Breadboard         | 1        | Connections           |
| Jumper Wires       | ~30      | Wiring                |
| 5V Power Supply    | 1        | Power servo           |

Total cost: $20-30

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

IR Sensors:

- Have 3 pins: VCC (3.3V), GND, Signal
- Signal is HIGH when nothing detected
- Signal goes LOW when object detected
- Adjust sensitivity with onboard potentiometer

Servo Motor:

- Needs separate 5V power (ESP32 can't provide enough current)
- 0° = gate closed
- 90° = gate open
- Don't power from ESP32 3.3V pin (will damage ESP32)

LCD Display:

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
int currentCount = 0;   // Current number of vehicles in zone
bool gateOpen = false;  // Current gate state
```

### Timing System

```cpp
const unsigned long DECISION_INTERVAL = 30000;  // Make decision every 30 seconds
```

How it works:

- Continuously count vehicles entering/exiting
- Every 30 seconds: Send current count to server for prediction
- Count persists (tracks actual vehicles in zone)

## Part 3: Setup Function

### WiFi Configuration

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";
```

What to change:

- YOUR_WIFI_SSID: Your WiFi network name
- YOUR_WIFI_PASSWORD: Your WiFi password
- YOUR_SERVER_IP: Your computer's local IP (from ipconfig)

Example:

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

  lastDecision = millis();
}
```

## Part 4: Main Loop

### Loop Structure

```cpp
void loop() {
  unsigned long now = millis();  // Current time in milliseconds

  // 1. Read IR sensors and count vehicles
  // 2. Make decision every 30 seconds
  // 3. Update display every 500ms

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
  lastInTime = now;

  Serial.print("Vehicle IN. Count: ");
  Serial.println(currentCount);

  tone(BUZZER_PIN, 1500);  // High beep
  delay(100);
  noTone(BUZZER_PIN);
}
```

How it works:

- IR sensor normally HIGH (nothing detected)
- When vehicle passes, goes LOW
- Detect transition: HIGH → LOW = vehicle detected
- `now - lastInTime > 300`: Debounce (ignore for 300ms to prevent double-counting)
- `currentCount++`: Increment total vehicles in zone
- Beep to confirm detection

Vehicle Exiting (same logic but decrements count):

```cpp
if (outState == LOW && lastOutState == HIGH && (now - lastOutTime > 300)) {
  if (currentCount > 0) currentCount--;

  Serial.print("Vehicle OUT. Count: ");
  Serial.println(currentCount);

  tone(BUZZER_PIN, 800);  // Lower beep
  delay(100);
  noTone(BUZZER_PIN);
}
```

### Making Decisions

```cpp
if (now - lastDecision >= DECISION_INTERVAL) {  // Every 30 seconds
  makeDecision();
  lastDecision = now;
}
```

Note: Count does NOT reset. It tracks the actual number of vehicles currently in the zone.

## Part 5: Decision Function

### Creating JSON Request

```cpp
void makeDecision() {
  Serial.println("Making decision");
  Serial.print("Current count: ");
  Serial.println(currentCount);

  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<128> doc;
  JsonArray counts = doc.createNestedArray("counts");
  counts.add(currentCount);

  String jsonData;
  serializeJson(doc, jsonData);
```

Creates JSON:

```json
{
  "counts": [10]
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

Error Handling:

```cpp
  } else {
    Serial.print("Server error: ");
    Serial.println(httpCode);
    lcd.clear();
    lcd.print("Server Error");
  }

  http.end();  // Always close connection
}
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
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], HIGH);
    }
    tone(BUZZER_PIN, 1000);
    delay(300);

    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], LOW);
    }
    noTone(BUZZER_PIN);
    delay(300);
  }

  lcd.clear();
  lcd.print("Opening Gate");

  for(int pos = 0; pos <= 90; pos++) {
    servo.write(pos);
    delay(15);
  }

  gateOpen = true;
}
```

Closing Gate (same but reverse servo):

```cpp
void closeGate() {
  // ... same LED/buzzer pattern ...

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

  lcd.print("Count: ");
  lcd.print(currentCount);

  lcd.setCursor(0, 1);
  lcd.print("Gate: ");
  lcd.print(gateOpen ? "OPEN" : "CLOSED");

  unsigned long timeToNext = DECISION_INTERVAL - (now - lastDecision);
  lcd.setCursor(12, 1);
  lcd.print(timeToNext / 1000);
  lcd.print("s");
}
```

Display shows:

```
Count: 12
Gate: OPEN    5s
```

## Part 7: Understanding the Code Flow

### Complete Cycle (30 seconds)

Seconds 0-30:

- Continuously count vehicles entering/exiting
- currentCount tracks net vehicles in zone
- Display updates every 500ms showing count and countdown

At 30 seconds:

- Send current count to server
- Server scales count by 14.5x (10 toy cars becomes 145)
- Get prediction based on scaled count
- Open/close gate if needed
- Start next 30-second cycle

### Why This Approach?

Simple and effective:

- No complex circular buffers
- Tracks actual vehicle occupancy
- One value sent = minimal data transfer
- 30-second interval = good balance between responsiveness and stability

### Server Scaling

Server multiplies count by 14.5 because:

- Model trained on real traffic data (100-300 vehicles)
- Toy car demo has much lower counts (5-15)
- Scale factor bridges the gap: 10 toy cars × 14.5 = 145 vehicles (triggers "high" traffic)

## Part 8: Defense Questions

Q: Why use ESP32 instead of Arduino?
A: ESP32 has built-in WiFi, more memory, faster processor, and costs about the same. Arduino would need separate WiFi module.

Q: How does vehicle counting work?
A: IR sensors detect when beam is broken. We detect HIGH→LOW transition and debounce for 300ms to prevent double-counting. Entry increments, exit decrements.

Q: Why doesn't count reset after each decision?
A: We're tracking actual vehicle occupancy in the zone, not throughput. Count represents current traffic density, which is what matters for gate control.

Q: What happens if WiFi disconnects?
A: System keeps counting vehicles locally. When decision time comes, it checks WiFi status and shows error if disconnected. Counts preserved until reconnection.

Q: Why separate power for servo?
A: Servo draws high current (up to 1A). ESP32's 3.3V pin can only provide ~50mA. Separate 5V prevents ESP32 brownout/reset.

Q: How accurate is vehicle counting?
A: Depends on sensor placement and speed. With proper setup and debouncing, 95%+ accuracy. Two sensors (in/out) helps track net count.

Q: Why 30 seconds instead of real-time?
A: Balance between responsiveness and stability. Too frequent = noisy predictions. Too slow = delayed response. 30 seconds gives good traffic snapshot.

Q: Can you run this without the server?
A: Not currently - the ML model is on server. Could convert model to TensorFlow Lite and run on ESP32, but would need significant code changes.
