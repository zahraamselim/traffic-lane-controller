# Smart Traffic Lane Management System

An intelligent traffic management system that uses IR sensors and machine learning to predict traffic conditions and automatically open/close extra lanes.

## Overview

This project uses an ESP32 microcontroller with IR sensors to count vehicles, sends the data to a server running an LSTM neural network model, and controls a motorized lane based on predicted traffic conditions.

## The Dataset

### Source

The dataset contains traffic measurements collected every 15 minutes over multiple days in October-November 2023.

### What's Inside

- **Time**: Timestamp of each measurement (15-minute intervals)
- **Date**: Day of the month
- **Day of the week**: Monday through Sunday
- **Vehicle counts**: Cars, Bikes, Buses, Trucks
- **Total**: Total vehicles counted in that interval
- **Traffic Situation**: Classification into 4 categories

### Traffic Categories

1. **Low** (41 samples, 2.8%): Very few vehicles, typically late night
2. **Normal** (850 samples, 57.4%): Regular traffic flow
3. **High** (71 samples, 4.8%): Increased traffic, nearing congestion
4. **Heavy** (139 samples, 9.5%): Congested, needs extra lane

### The Challenge

The dataset is heavily imbalanced. "Normal" traffic makes up over half the data, while "low" and "high" are rare. This makes it difficult for the model to learn these minority classes.

## How the Model Works

### Input

The model receives:

- Last 16 vehicle counts (4 hours of history)
- Current hour of day
- Day of week

### Feature Engineering

Since we only have vehicle counts from IR sensors, we create additional features:

- **Time features**: Hour encoded as sine/cosine to capture daily cycles
- **Peak indicators**: Morning rush (7-9 AM), evening rush (4-7 PM), night time
- **Rolling statistics**: Moving averages and standard deviations over 2, 4, and 8 intervals
- **Trend features**: Rate of change between intervals
- **Lag features**: Previous interval counts

### Model Architecture

- **Type**: LSTM (Long Short-Term Memory) neural network
- **Layers**:
  - 2 LSTM layers with 256 units each
  - Dropout layers (40%) to prevent overfitting
  - Batch normalization for stable training
  - 2 fully connected layers (256 → 128 → 4 outputs)
- **Parameters**: ~700,000 trainable parameters

### Training Process

- **Split**: 85% training, 15% testing
- **Loss function**: Cross-entropy with class weights to handle imbalance
- **Optimizer**: Adam with learning rate 0.0005
- **Epochs**: Up to 250 with early stopping (patience 40)
- **Metric**: F1 score for balanced evaluation across all classes

## Model Performance

### Final Results

- **Overall Accuracy**: 74.5%
- **Macro F1 Score**: 0.60

### Per-Class Performance

| Class  | Precision | Recall | F1-Score | Support |
| ------ | --------- | ------ | -------- | ------- |
| Heavy  | 0.84      | 0.88   | 0.86     | 105     |
| High   | 0.41      | 0.60   | 0.49     | 58      |
| Low    | 0.33      | 0.17   | 0.23     | 23      |
| Normal | 0.85      | 0.78   | 0.81     | 258     |

### What the Results Mean

**Good Performance**:

- Heavy traffic: 88% recall means we catch most congestion events
- Normal traffic: 78% recall with 85% precision is very reliable
- The model makes correct decisions for the majority of cases

**Challenges**:

- Low traffic: Only 17% recall due to very few examples (23 samples)
- High traffic: 60% recall is moderate but acceptable

### Why These Results Make Sense

1. **Class Imbalance**: With only 41 "low" examples total in 1,500+ samples, the model has very little data to learn from

2. **Overlap in Data**: Vehicle counts alone don't perfectly separate classes. A count of 80 vehicles might be "normal" in rush hour but "high" at midday

3. **Practical Impact**: For a traffic system, missing "heavy" traffic (12% miss rate) is the critical metric, and we're doing well at 88%

## Development Journey

### Attempt 1: Basic LSTM

- Started with simple 2-layer LSTM
- Result: 72% accuracy
- Issue: Poor performance on "high" and "low" classes

### Attempt 2: SMOTE Oversampling

- Used synthetic data generation to balance classes
- Result: 35% accuracy
- Issue: Synthetic data was unrealistic, model collapsed

### Attempt 3: Weighted Sampling

- Forced equal sampling during training
- Result: 35% accuracy
- Issue: Model ignored "normal" class completely (0% accuracy)

### Attempt 4: Focal Loss

- Used focal loss to focus on hard examples
- Result: 43% accuracy
- Issue: Still struggled with class balance

### Final Solution: Balanced Approach

- Moderate class weighting (square root scaling)
- Longer sequence length (16 intervals)
- More features (18 total)
- Deeper network with regularization
- Result: 75% accuracy with good balance

### Key Lessons Learned

1. Aggressive techniques (SMOTE, heavy sampling) can backfire
2. Feature engineering matters more than model complexity
3. For imbalanced data, F1 score is better than accuracy
4. Practical performance (catching heavy traffic) matters most

## Hardware Components

### Required Parts

- ESP32 DevKit V1
- 2x IR motion sensors (for vehicle detection)
- 16x2 LCD with I2C module
- Servo motor (for lane barrier)
- Buzzer
- 4x Red LEDs
- 4x 220Ω resistors (for LEDs)
- 1x 100Ω resistor (for buzzer)
- Breadboard
- Jumper wires

### Pin Connections

| Component     | ESP32 Pin | Notes                   |
| ------------- | --------- | ----------------------- |
| IR Sensor IN  | GPIO34    | Vehicle entry detection |
| IR Sensor OUT | GPIO35    | Vehicle exit detection  |
| LCD SDA       | GPIO21    | I2C data                |
| LCD SCL       | GPIO22    | I2C clock               |
| Servo         | GPIO13    | PWM control             |
| Buzzer        | GPIO12    | Through 100Ω resistor   |
| LED 1         | GPIO14    | Through 220Ω resistor   |
| LED 2         | GPIO27    | Through 220Ω resistor   |
| LED 3         | GPIO26    | Through 220Ω resistor   |
| LED 4         | GPIO25    | Through 220Ω resistor   |

## Software Setup

### 1. Server Setup

Install Python dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Place model files in the same directory as `server.py`:

- traffic_model.pth
- scaler.pkl
- label_encoder.pkl
- features.pkl
- config.pkl

Run the server:

```bash
python server.py
```

Server will start on `http://0.0.0.0:5000`

### 2. ESP32 Setup

Install Arduino IDE libraries:

- WiFi (built-in)
- HTTPClient (built-in)
- ArduinoJson
- LiquidCrystal_I2C
- ESP32Servo

Edit configuration in `esp32_traffic_controller.ino`:

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";
```

Upload to ESP32 using Arduino IDE.

## How It Works

### System Flow

1. **Vehicle Counting** (Continuous)

   - IR sensors detect vehicles entering and exiting
   - ESP32 maintains running count every 15 minutes
   - Counts are stored in a rolling buffer of 16 intervals

2. **Prediction Request** (Every 4 hours)

   - ESP32 sends 16 vehicle counts + timestamp to server
   - Server runs LSTM model inference
   - Returns prediction: low/normal/high/heavy

3. **Lane Control** (Automated)
   - If prediction is "heavy" or "high": Open extra lane
   - If prediction is "low" or "normal": Close extra lane
   - Warning system activates (LEDs + buzzer) during movement

### LCD Display

- Line 1: Current vehicle count
- Line 2: Lane status (OPEN/CLOSED)

### Safety Features

- Visual warning: 4 flashing red LEDs
- Audio warning: Buzzer sounds during lane movement
- LCD announcement: "OPENING LANE" or "CLOSING LANE"
- 5-second warning sequence before servo moves

## API Reference

### POST /predict

Predict traffic condition from vehicle counts.

**Request Body**:

```json
{
  "counts": [
    45, 52, 58, 65, 72, 80, 88, 95, 105, 115, 122, 128, 130, 132, 128, 125
  ],
  "hour": 8,
  "day_of_week": 1
}
```

**Response**:

```json
{
  "prediction": "heavy",
  "confidence": 97.7,
  "open_lane": true,
  "timestamp": "2025-12-03T10:30:00"
}
```

### GET /health

Check server status.

**Response**:

```json
{
  "status": "healthy",
  "model_loaded": true
}
```

## Testing

### Test the Server

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"counts": [45,52,58,65,72,80,88,95,105,115,122,128,130,132,128,125], "hour": 8, "day_of_week": 1}'
```

### Monitor ESP32

Open Serial Monitor (115200 baud) to see:

- Vehicle counts
- WiFi connection status
- Prediction results
- Lane control actions

## Troubleshooting

### ESP32 Won't Connect to WiFi

- Check SSID and password
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Move closer to router

### Server Returns Error

- Verify all model files are present
- Check file paths in server.py
- Ensure Python version 3.7+

### IR Sensors Not Detecting

- Check wiring connections
- Test with Serial.println(digitalRead(pin))
- Adjust sensor sensitivity if available

### Servo Not Moving

- Check power supply (servo needs 5V)
- Verify GPIO13 connection
- Test with Servo.write() in setup()

### LCD Not Displaying

- Check I2C address (0x27 or 0x3F)
- Verify SDA/SCL connections
- Adjust contrast potentiometer on I2C module

## Future Improvements

1. **Add Camera**: Vehicle type classification for better predictions
2. **Weather Integration**: Factor in rain/snow effects on traffic
3. **Multiple Lanes**: Control several lanes independently
4. **Mobile App**: Real-time monitoring dashboard
5. **Historical Analysis**: Track patterns over weeks/months

## License

This project is open source and available for educational purposes.

## Acknowledgments

Dataset source: Traffic monitoring system
Model architecture inspired by time-series forecasting research
