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

#### Option A: Using Virtual Environment (Recommended)

A virtual environment keeps your project dependencies isolated from other Python projects.

1. Open Command Prompt or PowerShell in the project folder

2. If using PowerShell, you may need to enable script execution first (one time only):

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

3. Create virtual environment:

```
python -m venv venv
```

4. Activate virtual environment:

```
venv\Scripts\activate
```

You should see `(venv)` at the beginning of your command prompt line.

5. Install dependencies:

```
pip install -r requirements.txt
```

6. Start the server:

```
python server.py
```

7. To deactivate virtual environment later (when you're done):

```
deactivate
```

**Next time you want to run the server:**

```
venv\Scripts\activate
python server.py
```

#### Option B: Global Installation (Not Recommended)

1. Open Command Prompt in the project folder

2. Install Python dependencies:

```
pip install -r requirements.txt
```

3. Start the server:

```
python server.py
```

#### Verify Server is Running

You should see:

```
Loading model...
Model loaded: SimpleNN
Features: ['Total', 'Hour', 'DayNum', 'is_morning_rush', 'is_evening_rush', 'is_night', 'is_weekend']
Classes: ['heavy' 'high' 'normal' 'moderate']
Test Accuracy: 0.XXXX

Traffic Prediction Server
Model Type: SimpleNN
Classes: heavy, high, normal, moderate
Test Accuracy: XX.XX%

Demo Settings:
  Prediction interval: 30 seconds
  Scale factor: 14.5x
  Fixed time: Friday 5 PM (rush hour)
  10 toy cars in 30 seconds will trigger high traffic

Server running on http://0.0.0.0:5000
```

Keep this window open while using the system.

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
Making prediction every 30 seconds
```

5. Wave your hand over the IR sensors
6. Watch the LCD and Serial Monitor for predictions

## How It Works

1. **Data Collection**: ESP32 continuously counts vehicles using IR sensors
2. **Vehicle Tracking**: Entry sensor increments count, exit sensor decrements
3. **Prediction**: Every 30 seconds, sends current count to server via WiFi
4. **Scaling**: Server multiplies count by 14.5x to match training data range
5. **Classification**: ML model analyzes scaled data and predicts traffic level
6. **Action**: If traffic is heavy or high, opens the extra lane

## Traffic Classes

The model classifies traffic into 4 levels:

- **Normal**: Low traffic (lane closed)
- **Moderate**: Medium traffic (lane closed, monitoring)
- **Heavy**: High traffic (lane opens)
- **High**: Very high traffic (lane stays open)

## Demo Mode

The system is configured for toy car demonstrations:

- Server uses fixed time: Friday 5 PM (rush hour)
- Count scaled by 14.5x (10 toy cars = 145 scaled vehicles)
- 10 toy cars in 30 seconds triggers "high" traffic prediction
- Gate opens automatically

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
└── venv/                 # Virtual environment (after setup)
```

## Troubleshooting

### Server Issues

**Problem**: "ModuleNotFoundError"
**Solution**: Make sure virtual environment is activated and run `pip install -r requirements.txt`

**Problem**: "Address already in use"
**Solution**: Another program is using port 5000. Either close it or change the port in server.py

**Problem**: Can't access from ESP32
**Solution**:

- Check Windows Firewall settings
- Make sure both devices on same WiFi network
- Verify IP address with `ipconfig`

### ESP32 Issues

**Problem**: WiFi won't connect
**Solution**:

- Check SSID and password (case-sensitive)
- ESP32 only supports 2.4GHz WiFi, not 5GHz
- Move closer to router

**Problem**: Can't reach server
**Solution**:

- Server must be running
- Check server IP address in sketch
- Test server health: open browser to `http://localhost:5000/health`

**Problem**: IR sensors not detecting
**Solution**:

- Check wiring (VCC, GND, Signal pins)
- Adjust sensitivity potentiometer on sensor
- Verify sensor LED lights up when triggered

## Getting Help

Check the documentation files:

- `docs/HARDWARE.md` - Circuit diagrams and wiring
- `docs/SERVER.md` - Server configuration and testing
- `docs/MODEL.md` - Understanding the ML model

## Project Demo

When everything works correctly:

1. LCD displays current vehicle count and countdown
2. Every 30 seconds, prediction appears on screen
3. If heavy/high traffic detected:
   - LEDs flash 5 times
   - Buzzer beeps with LEDs
   - Servo rotates to open gate
   - LCD shows "Opening Gate"
4. Serial Monitor logs all activity

## Quick Start Commands

```bash
# First time setup (PowerShell users run this first)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Create and setup virtual environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run server (after first time)
venv\Scripts\activate
python server.py

# Test server
curl http://localhost:5000/health

# Deactivate when done
deactivate
```

## License

MIT License - Free for educational use
