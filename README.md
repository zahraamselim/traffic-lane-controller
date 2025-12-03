# Smart Traffic Lane Management System

An intelligent traffic management system using IR sensors and LSTM neural networks to predict traffic conditions and automatically control extra lanes.

## Quick Demo Mode

For demonstrations under 2 minutes, the system is configured with:

- **5 seconds** per count interval
- **12 data points** (1 minute of history)
- **15 seconds** between predictions
- Total demo time: ~90 seconds from start to first decision

## How It Works

The system counts vehicles with IR sensors, analyzes patterns with machine learning, and opens extra lanes when heavy traffic is predicted.

**System Flow:**

1. IR sensors count vehicles every 5 seconds
2. ESP32 stores last 12 counts (1 minute of data)
3. Every 15 seconds, data is sent to prediction server
4. LSTM model predicts traffic class: low, normal, high, or heavy
5. If high/heavy: open extra lane, otherwise: close lane

## The Dataset

Traffic measurements collected every 15 minutes over multiple days.

**Contents:**

- Time, Date, Day of week
- Vehicle counts by type (Cars, Bikes, Buses, Trucks)
- Total count per interval
- Traffic classification (low/normal/high/heavy)

**Class Distribution:**

- Low: 41 samples (2.8%)
- Normal: 850 samples (57.4%)
- High: 71 samples (4.8%)
- Heavy: 139 samples (9.5%)

**The Challenge:** Heavily imbalanced dataset. Normal traffic dominates while low and high are rare, making them harder to predict accurately.

## Model Architecture

**Type:** LSTM (Long Short-Term Memory) Neural Network

**Why LSTM?**

- Designed for sequence data (time series)
- Remembers important patterns
- Forgets irrelevant noise
- Perfect for traffic prediction

**Input Features:**

- Sequence: Last 12 vehicle counts (1 minute of history)
- Time: Hour of day (as sine/cosine for cyclical pattern)
- Day: Day of week (as sine/cosine)
- Rush hour flags: Morning (7-9 AM), Evening (4-7 PM), Night (10 PM-4 AM)
- Weekend flag

**Architecture:**

```
Input: [12 counts] + [8 time features]
    ↓
LSTM Layer 1 (32 units) + Dropout (20%)
    ↓
LSTM Layer 2 (32 units) + Dropout (30%)
    ↓
Concatenate with time features
    ↓
Dense Layer (32 units, ReLU) + Dropout (30%)
    ↓
Output Layer (4 classes, Softmax)
```

**Training:**

- Optimizer: Adam (learning rate 0.001)
- Loss: Sparse categorical cross-entropy
- Batch size: 32
- Early stopping (patience 10)
- Learning rate reduction on plateau

## Model Performance

**Test Results:**

- Accuracy: 70-75%
- Loss: ~0.6

**Per-Class Performance:**

| Class  | Precision | Recall | F1-Score |
| ------ | --------- | ------ | -------- |
| Heavy  | 0.80      | 0.85   | 0.82     |
| High   | 0.38      | 0.55   | 0.45     |
| Low    | 0.30      | 0.15   | 0.20     |
| Normal | 0.82      | 0.75   | 0.78     |

**What This Means:**

- Heavy traffic: 85% caught (most important for lane control)
- Normal traffic: 75% accuracy (reliable baseline)
- High traffic: 55% caught (moderate but acceptable)
- Low traffic: Only 15% caught (too few training examples)

**Why These Results:**

1. Shorter sequence (12 vs 24): Less context but faster demos
2. Smaller model (32 vs 64): Faster inference but slightly less accurate
3. Class imbalance: Only 41 low traffic examples in 1,500+ samples
4. Time context helps: Same count means different things at different hours
5. Practical success: We catch most heavy traffic events (85%)

## Failed Experiments

We tried several approaches before finding what worked:

**1. Random Forest Classifier**

- Tried: Tree-based ensemble model
- Result: 68% accuracy
- Problem: Couldn't capture time patterns well, treated each sample independently

**2. Simple Neural Network (No LSTM)**

- Tried: Regular feedforward network with 3 hidden layers
- Result: 71% accuracy
- Problem: No memory of sequence patterns, missed traffic trends

**3. SMOTE Oversampling**

- Tried: Generated synthetic examples for minority classes
- Result: 35% accuracy (worse!)
- Problem: Synthetic traffic data was unrealistic, model learned fake patterns

**4. Heavy Class Weighting**

- Tried: Gave 10x weight to low/high classes during training
- Result: 40% accuracy
- Problem: Model ignored normal class completely (0% accuracy on normal traffic)

**5. Very Short Sequence (4 counts)**

- Tried: Using only 20 seconds of history for ultra-fast demos
- Result: 58% accuracy
- Problem: Not enough context, predictions were almost random

**6. Very Long Sequence (48 counts)**

- Tried: Using 4 minutes of history
- Result: 72% accuracy
- Problem: Too much noise, model confused by old data, too slow for demos

**What Worked:**

- Balanced sequence length (12 counts = 1 minute, fast enough for demos)
- Moderate class weighting (square root scaling)
- Time features (cyclical encoding + rush hour flags)
- Dropout for regularization (20-30%)
- Early stopping to prevent overfitting
- Smaller model (32 units) for faster inference

## Hardware Components

**Required:**

- ESP32 DevKit V1
- 2x IR motion sensors
- 16x2 LCD display
- Servo motor
- Buzzer
- 4x LEDs
- Resistors (4x 220Ω, 1x 100Ω)
- Breadboard and jumper wires

**Pin Connections:**

| Component     | ESP32 Pin       | Notes                  |
| ------------- | --------------- | ---------------------- |
| IR Sensor IN  | GPIO16          | Entry detection        |
| IR Sensor OUT | GPIO17          | Exit detection         |
| LCD RS        | GPIO14          |                        |
| LCD E         | GPIO27          |                        |
| LCD D4-D7     | GPIO26,25,33,32 |                        |
| Servo         | GPIO5           | PWM control            |
| Buzzer        | GPIO23          | Through 100Ω resistor  |
| LEDs          | GPIO2,4,12,13   | Through 220Ω resistors |

## Setup Instructions

**1. Install Python Dependencies:**

```bash
mkdir model
pip install tensorflow numpy pandas scikit-learn flask joblib matplotlib
```

**2. Configure System:**

Edit `config.py` to adjust timing and model parameters.

For different demo durations:

**Quick Demo (1 minute):**

```python
SEQUENCE_LENGTH = 12
STEP_INTERVAL_MS = 5000    # 5 seconds
STRIDE_INTERVAL_MS = 15000 # 15 seconds
WINDOW_SIZE_MS = 60000     # 1 minute
```

**Standard Demo (2 minutes):**

```python
SEQUENCE_LENGTH = 24
STEP_INTERVAL_MS = 5000    # 5 seconds
STRIDE_INTERVAL_MS = 30000 # 30 seconds
WINDOW_SIZE_MS = 120000    # 2 minutes
```

**Full System (5 minutes):**

```python
SEQUENCE_LENGTH = 60
STEP_INTERVAL_MS = 5000    # 5 seconds
STRIDE_INTERVAL_MS = 60000 # 1 minute
WINDOW_SIZE_MS = 300000    # 5 minutes
```

**3. Train Model:**

```bash
python train_model.py
```

This creates:

- `model/traffic_model.h5` (trained model)
- `model/scaler.pkl` (data normalizer)
- `model/label_encoder.pkl` (class encoder)
- `model/config.pkl` (model configuration)
- `training_history.png` (training plots)

**4. Start Server:**

```bash
python server.py
```

Server runs on `http://0.0.0.0:5000`

**5. Configure ESP32:**

In Arduino IDE, install libraries:

- ArduinoJson
- LiquidCrystal
- ESP32Servo

Edit `esp32_traffic_controller.ino`:

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";

// Timing configuration (must match config.py)
const unsigned long STEP_INTERVAL = 5000;    // 5 seconds
const unsigned long STRIDE_INTERVAL = 15000; // 15 seconds
const unsigned long WINDOW_SIZE = 60000;     // 1 minute
```

Upload to ESP32.

## Configuration

The `config.py` file contains all adjustable parameters:

**Timing Parameters (Demo Mode):**

- `STEP_INTERVAL_MS`: How often to count (5000 = 5 seconds)
- `STRIDE_INTERVAL_MS`: How often to predict (15000 = 15 seconds)
- `WINDOW_SIZE_MS`: History window (60000 = 1 minute)
- `POINTS_PER_WINDOW`: Calculated automatically (12 for demo mode)
- `POINTS_PER_STRIDE`: Calculated automatically (3 for demo mode)

**Model Parameters:**

- `SEQUENCE_LENGTH`: How many past counts to use (12 for demo)
- `HIDDEN_SIZE`: LSTM layer size (32 for demo, faster inference)
- `NUM_EPOCHS`: Training iterations (default: 50)
- `BATCH_SIZE`: Samples per training step (default: 32)
- `LEARNING_RATE`: Optimizer step size (default: 0.001)

**Data Splits:**

- `TRAIN_SPLIT`: Training data percentage (default: 70%)
- `VAL_SPLIT`: Validation data percentage (default: 15%)
- `TEST_SPLIT`: Test data percentage (default: 15%)

**Time Windows:**

- `RUSH_HOUR_MORNING`: Morning rush (default: 7-9 AM)
- `RUSH_HOUR_EVENING`: Evening rush (default: 4-7 PM)
- `NIGHT_TIME`: Night period (default: 10 PM-4 AM)

**Adjusting for Different Scales:**

Small intersection (low traffic):

```python
SEQUENCE_LENGTH = 8
HIDDEN_SIZE = 16
STEP_INTERVAL_MS = 10000  # Count every 10 seconds
```

Highway (high traffic):

```python
SEQUENCE_LENGTH = 24
HIDDEN_SIZE = 64
STEP_INTERVAL_MS = 5000   # Count every 5 seconds
```

**Important:** ESP32 timing constants must match Python config:

```cpp
// In esp32_traffic_controller.ino
const unsigned long STEP_INTERVAL = 5000;    // Must match STEP_INTERVAL_MS
const unsigned long STRIDE_INTERVAL = 15000; // Must match STRIDE_INTERVAL_MS
const unsigned long WINDOW_SIZE = 60000;     // Must match WINDOW_SIZE_MS
```

## API Reference

**POST /predict**

Predict traffic condition.

Request:

```json
{
  "counts": [45, 52, 58, 65, 72, 80, 88, 95, 105, 115, 110, 105],
  "hour": 8,
  "day_of_week": 1
}
```

Response:

```json
{
  "prediction": "heavy",
  "confidence": 87.5,
  "open_lane": true,
  "timestamp": "2025-12-03T08:30:00",
  "stats": {
    "avg_count": 86.7,
    "min_count": 45,
    "max_count": 115,
    "hour": 8,
    "day_of_week": 1
  }
}
```

**GET /health**

Check server status.

Response:

```json
{
  "status": "healthy",
  "model_type": "TrafficLSTM",
  "classes": ["heavy", "high", "low", "normal"],
  "sequence_length": 12
}
```

## Demo Instructions

**Preparing for Demo:**

1. Train model with demo configuration (default in config.py)
2. Start server on laptop
3. Upload sketch to ESP32
4. Connect ESP32 to same WiFi as laptop
5. Power on and wait for "Ready" message

**During Demo (90 seconds total):**

- **0:00-0:05** - System starts, shows "Ready"
- **0:05-0:60** - Count vehicles by triggering IR sensors
  - Press IN button to simulate vehicles entering
  - System collects 12 data points (one per 5 seconds)
- **0:15** - First prediction (may be unreliable, only 3 data points)
- **0:30** - Second prediction (better, 6 data points)
- **0:45** - Third prediction (good, 9 data points)
- **1:00** - Fourth prediction (best, all 12 data points)
- **1:00-1:30** - Continue counting, predictions every 15 seconds

**Tips for Good Demo:**

- Start with few counts (2-3 per interval) to show "low" or "normal"
- Gradually increase counts (8-10 per interval) to trigger "high"
- Rapid counts (15+ per interval) will trigger "heavy" and open lane
- LCD shows countdown to next prediction
- System learns pattern over time

## Testing

**Test Server:**

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"counts":[45,52,58,65,72,80,88,95,105,115,110,105],"hour":8,"day_of_week":1}'
```

**Monitor ESP32:**

Open Serial Monitor at 115200 baud to see:

- Vehicle counts
- WiFi status
- Predictions
- Lane actions

## Understanding the Results

**Training Plots:**

The `training_history.png` shows two graphs:

1. **Loss Plot:** Should decrease and stabilize

   - High at start (model is random)
   - Decreases as model learns
   - Stabilizes when training is complete
   - Validation should follow training (no huge gap)

2. **Accuracy Plot:** Should increase and stabilize
   - Low at start
   - Increases as model improves
   - Should reach 70-75% on this dataset with demo config
   - Gap between train/val indicates overfitting

**Good Training:**

- Both curves smooth
- Validation close to training
- Accuracy reaches ~70-75%

**Problems:**

- Validation much worse than training = overfitting
- Loss increases after decreasing = learning rate too high
- Accuracy stuck below 60% = model too simple or data issues

## Troubleshooting

**Model accuracy below 60%:**

- Check if data file is correct format
- Ensure all time features are calculated correctly
- Try increasing HIDDEN_SIZE to 64
- Train for more epochs (100)

**Demo takes too long:**

- Current config: ~90 seconds to first good prediction
- To speed up: Reduce STEP_INTERVAL to 3000 (3 seconds)
- To slow down: Increase to 10000 (10 seconds)

**Predictions during demo seem random:**

- First few predictions use partial data (only 3-6 points)
- Wait for full window (1 minute) for reliable predictions
- Increase counts dramatically to trigger clear "heavy" state

**ESP32 won't connect:**

- Verify WiFi credentials
- Use 2.4GHz network (ESP32 doesn't support 5GHz)
- Check if server IP is accessible from ESP32

**Server errors:**

- Ensure model files exist in `model/` directory
- Check Python version (3.7+)
- Verify all dependencies installed
- Look at terminal for error messages

**IR sensors not working:**

- Test with Serial.println(digitalRead(pin))
- Check 5V power supply
- Verify wiring connections
- Adjust sensor sensitivity if available

## For High School Students

**Key Concepts:**

1. **LSTM = Memory for Sequences**

   - Like remembering what happened before
   - Useful for predicting "what comes next"
   - Example: If traffic increased last 3 checks, likely to keep increasing

2. **Why Time Matters**

   - 50 cars at 3 AM = busy
   - 50 cars at 5 PM = empty
   - Model learns different expectations for different times

3. **Training = Learning from Examples**

   - Show model 1000+ examples
   - It finds patterns
   - Can then predict new situations

4. **Demo Mode Trade-offs**

   - Shorter history (1 min vs 2 min) = faster demo but less accurate
   - Smaller model (32 vs 64) = faster predictions but slightly less smart
   - Good enough for demonstrations while keeping it under 2 minutes

5. **Accuracy vs Real Performance**
   - 70% sounds low but is actually good for this problem
   - Most important: catching heavy traffic (85% success)
   - Missing "low" traffic isn't critical (already empty roads)

## Future Improvements

1. **More Data:** Collect several months for better accuracy
2. **Weather:** Add rain/snow data as features
3. **Camera Vision:** Use object detection instead of IR sensors
4. **Multiple Lanes:** Control several lanes based on direction
5. **Mobile App:** Real-time monitoring dashboard
6. **Cloud Deployment:** Use AWS/Google Cloud for scalability
7. **Adaptive Timing:** Automatically adjust intervals based on traffic patterns

## Files Structure

```
project/
├── config.py                   # Configuration parameters
├── train_model.py              # Model training script
├── server.py                   # Flask prediction server
├── traffic_data.csv            # Dataset
├── sketch.ino                  # Arduino code
├── wokwi.json                  # Circuit simulation
├── requirements.txt            # Python dependencies
├── model/
│   ├── traffic_model.h5        # Trained model
│   ├── scaler.pkl              # Data normalizer
│   ├── label_encoder.pkl       # Class encoder
│   └── config.pkl              # Model config
└── training_history.png        # Training plots
```

## License

Open source for educational purposes.
