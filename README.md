# Smart Traffic Lane Control System

An IoT-based traffic management system that uses machine learning to automatically control an extra lane based on real-time traffic conditions.

## System Overview

The system consists of three main components:

1. **ESP32 Hardware**: Collects vehicle count data using IR sensors
2. **Python Server**: Runs ML model to predict traffic levels
3. **ML Model**: Classifies traffic and decides when to open/close extra lane

## Features

- Real-time vehicle counting with IR sensors
- Machine learning-based traffic classification
- Automatic lane gate control
- Visual feedback with LEDs and LCD display
- Audio alerts with buzzer
- WiFi connectivity for predictions

## What You Need

### Software (Windows)

- Windows 10 or 11
- Python 3.8 or higher
- Arduino IDE 2.0 or higher

### Hardware

- ESP32 development board
- IR sensors (2x)
- Servo motor (SG90 or similar)
- 16x2 LCD display
- Buzzer
- LEDs (4x)
- Resistors, jumper wires, breadboard
- 5V power supply for servo

See `docs/HARDWARE.md` for complete parts list and wiring diagram.

## Installation Guide

### Step 1: Get Your Computer's IP Address

Your ESP32 needs to know where to send data, so you need your computer's local IP address.

1. Press `Win + R`, type `cmd`, press Enter
2. Type `ipconfig` and press Enter
3. Look for your WiFi adapter section (usually "Wireless LAN adapter Wi-Fi")
4. Find the line that says "IPv4 Address"
5. Write down the number (example: `192.168.1.100`)

**Example output:**

```
Wireless LAN adapter Wi-Fi:
   Connection-specific DNS Suffix  . :
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.1.1
```

In this example, your IP is `192.168.1.100`

**Important**: This IP address is what you'll use in the sketch as `YOUR_SERVER_IP`

### Step 2: Setup the Server

1. Open Command Prompt in the project folder
2. Install Python dependencies:

```
pip install -r requirements.txt
```

3. Start the server:

```
python server.py
```

4. You should see:

```
Traffic Prediction Server
Model Type: SimpleNN
Classes: heavy, high, normal, moderate
Test Accuracy: XX.XX%

Server running on http://0.0.0.0:5000
```

5. Keep this window open

### Step 3: Configure the ESP32 Sketch

1. Open `sketch.ino` in Arduino IDE

2. Update these lines with your information:

```cpp
const char* ssid = "YOUR_WIFI_SSID";           // Your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // Your WiFi password
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";  // Your computer's IP
```

Example:

```cpp
const char* ssid = "MyHomeWiFi";
const char* password = "mypassword123";
const char* serverUrl = "http://192.168.1.100:5000/predict";
```

### Step 4: Install Arduino Libraries

In Arduino IDE, go to Tools → Manage Libraries and install:

- **WiFi** (built-in)
- **HTTPClient** (built-in)
- **ArduinoJson** by Benoit Blanchon
- **LiquidCrystal** (built-in)
- **ESP32Servo** by Kevin Harrington

### Step 5: Upload to ESP32

1. Connect ESP32 to your computer via USB
2. In Arduino IDE:
   - Tools → Board → ESP32 Arduino → ESP32 Dev Module
   - Tools → Port → Select your COM port
3. Click Upload button
4. Wait for "Done uploading"

### Step 6: Test the System

1. Open Serial Monitor (Tools → Serial Monitor)
2. Set baud rate to 115200
3. Press reset button on ESP32
4. You should see:

```
Connecting to WiFi...
WiFi connected
IP: 192.168.X.X
System ready
```

5. Wave your hand over the IR sensors
6. Watch the LCD and Serial Monitor for predictions

## How It Works

1. **Data Collection**: ESP32 counts vehicles every 5 seconds using IR sensors
2. **Data Window**: Stores 12 counts (60 seconds of traffic data)
3. **Prediction**: Every 15 seconds, sends all 12 counts to server via WiFi
4. **Classification**: ML model analyzes data and predicts traffic level
5. **Action**: If traffic is heavy or high, opens the extra lane

## Traffic Classes

The model classifies traffic into 4 levels:

- **Normal**: Low traffic (lane closed)
- **Moderate**: Medium traffic (lane closed, monitoring)
- **Heavy**: High traffic (lane opens)
- **High**: Very high traffic (lane stays open)

## Project Structure

```
traffic-system/
├── README.md              # This file
├── docs/                  # Documentation folder
│   ├── MODEL.md          # Model explanation
│   ├── SERVER.md         # Server setup details
│   └── HARDWARE.md       # Hardware assembly guide
├── model/                 # Pre-trained ML model
│   ├── traffic_model.h5
│   ├── scaler.pkl
│   ├── label_encoder.pkl
│   └── config.pkl
├── server.py              # Flask prediction server
├── requirements.txt       # Python dependencies
├── sketch.ino            # ESP32 main code
└── wokwi.json            # Wokwi simulator config
```

## Getting Help

Check the documentation files:

- `docs/HARDWARE.md` - Circuit diagrams and wiring
- `docs/SERVER.md` - Server configuration and testing
- `docs/MODEL.md` - Understanding the ML model

## Project Demo

When everything works correctly:

1. LCD displays current vehicle count
2. Every 15 seconds, prediction appears on screen
3. If heavy/high traffic detected:
   - LEDs flash 5 times
   - Buzzer beeps with LEDs
   - Servo rotates to open gate
   - LCD shows "Opening Gate"
4. Serial Monitor logs all activity

## License

MIT License - Free for educational use
