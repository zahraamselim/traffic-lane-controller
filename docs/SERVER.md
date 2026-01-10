# Server Documentation

This document explains the Flask server from basics to advanced details.

## Part 1: Server Basics

### What is a Server?

A server is a program that waits for requests and sends back responses.

Restaurant Analogy:

- Kitchen (Server): Waits for orders, prepares food, sends it out
- Customer (ESP32): Places order, waits, receives food
- Menu (API): List of what you can order

Our Server:

- Waits for ESP32 to send vehicle count
- Processes through ML model
- Sends back traffic prediction

### Why Do We Need a Server?

ESP32 is too small to run the neural network (only 520 KB RAM). Solution: ESP32 counts vehicles, server runs ML model.

Communication Flow:

```
ESP32 → WiFi → Server → ML Model → Server → WiFi → ESP32
```

### What is Flask?

Flask is a Python toolkit for building servers easily.

Without Flask (100+ lines of socket code)
With Flask (5 lines):

```python
from flask import Flask
app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    return result
```

### Our API Endpoints

1. `/predict` - Get traffic prediction (POST)
2. `/health` - Check if server is working (GET)

## Part 2: HTTP Basics

### HTTP Request (ESP32 sends)

Method: POST (sending data to process)
URL: `http://192.168.1.100:5000/predict`
Body:

```json
{
  "counts": [10]
}
```

### HTTP Response (Server sends back)

Status Code: 200 (success), 400 (bad data), 500 (error)
Body:

```json
{
  "prediction": "high",
  "confidence": 85.0,
  "open_lane": true
}
```

## Part 3: Code Walkthrough

### Loading the Model

```python
model = keras.models.load_model('model/traffic_model.h5')  # The neural network
scaler = joblib.load('model/scaler.pkl')                   # Normalizes data
label_encoder = joblib.load('model/label_encoder.pkl')     # Converts numbers to words
config = joblib.load('model/config.pkl')                   # Model info
```

All 4 files must be from the same training session.

### The /predict Endpoint (Step by Step)

#### Step 1: Receive Data

```python
data = request.json
vehicle_counts = data['counts']  # List with 1 count value
```

#### Step 2: Validate

```python
if len(vehicle_counts) != 1:
    return jsonify({'error': 'Expected 1 vehicle count'}), 400
```

#### Step 3: Extract and Scale Count

```python
total_count = vehicle_counts[0]
scaled_total = total_count * 14.5
# 10 toy cars × 14.5 = 145 (scaled to match training data range)
```

#### Step 4: Set Demo Time Features

```python
current_hour = 17   # Friday 5 PM (rush hour)
current_day = 4     # Friday (0=Monday, 4=Friday)
```

Fixed time ensures consistent predictions for demo purposes.

#### Step 5: Create Time Features

```python
is_morning_rush = 1 if 7 <= current_hour <= 9 else 0
is_evening_rush = 1 if 16 <= current_hour <= 19 else 0
is_night = 1 if current_hour >= 22 or current_hour < 4 else 0
is_weekend = 1 if current_day >= 5 else 0
```

#### Step 6: Prepare Features Array

```python
features = np.array([[
    scaled_total,
    current_hour,
    current_day,
    is_morning_rush,
    is_evening_rush,
    is_night,
    is_weekend
]])
# Shape: (1, 7) = 1 sample with 7 features
```

#### Step 7: Scale Features

```python
features_scaled = scaler.transform(features)
# Before: [145.0, 17, 4, 0, 1, 0, 0]
# After:  [normalized values based on training data statistics]
```

Critical: Use `transform()`, NOT `fit_transform()`.

#### Step 8: Predict

```python
predictions = model.predict(features_scaled, verbose=0)
# Output: [[0.05, 0.10, 0.20, 0.65]]
#          normal moderate heavy high

predicted_class = np.argmax(predictions[0])  # Index of max value = 3
confidence = float(predictions[0][predicted_class] * 100)  # 65.0
prediction = label_encoder.inverse_transform([predicted_class])[0]  # "high"
should_open = prediction in ['heavy', 'high']  # True
```

#### Step 9: Return Response

```python
return jsonify({
    'prediction': prediction,
    'confidence': round(confidence, 2),
    'open_lane': should_open,
    'timestamp': datetime.now().isoformat(),
    'stats': {
        'raw_count': int(total_count),
        'scaled_count': float(round(scaled_total, 1)),
        'hour': current_hour,
        'day_of_week': current_day,
        'is_morning_rush': bool(is_morning_rush),
        'is_evening_rush': bool(is_evening_rush),
        'is_weekend': bool(is_weekend)
    }
})
```

### Error Handling

```python
except Exception as e:
    import traceback
    print(f"Error: {traceback.format_exc()}")
    return jsonify({'error': str(e)}), 500
```

Catches any error, prints to console, returns error 500 to ESP32.

### The /health Endpoint

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_type': model_config['model_type'],
        'classes': label_encoder.classes_.tolist(),
        'test_accuracy': model_config['test_accuracy']
    })
```

Use to check if server is running: `http://localhost:5000/health`

### Server Startup

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

- `host='0.0.0.0'`: Accept connections from any device on local network
- `port=5000`: Listen on port 5000
- `debug=False`: Production mode (more stable)

## Part 4: Scale Factor Explained

### Why 14.5x?

Training data had vehicle counts in range 0-500:

- Normal: 0-80
- Moderate: 80-120
- Heavy: 120-180
- High: 180+

Model learned "high" traffic starts around 145 vehicles.

For toy car demo with counts of 5-15, we need to scale up:

- 10 toy cars × 14.5 = 145 scaled vehicles
- This triggers "high" prediction
- Gate opens as expected

### How Scale Was Determined

1. Tested model with counts 0-500 in increments of 10
2. Found gate opens at vehicle count 145
3. Calculated scale: 145 ÷ 10 = 14.5
4. Now 10 toy cars perfectly triggers gate opening

### Adjusting Scale

If you want different sensitivity:

- More sensitive (gate opens sooner): Increase scale
  - Scale 20: 10 cars × 20 = 200 (very high traffic)
- Less sensitive (gate opens later): Decrease scale
  - Scale 10: 10 cars × 10 = 100 (moderate traffic)

Change on line 37 in server.py:

```python
scaled_total = total_count * YOUR_SCALE
```

## Part 5: System Flow Example

### Complete Request-Response Cycle

ESP32 → Server:

```json
{
  "counts": [10]
}
```

Server Processing:

1. Extract count: 10
2. Scale: 10 × 14.5 = 145
3. Add time features: [145, 17, 4, 0, 1, 0, 0]
4. Normalize with scaler
5. Run through neural network
6. Get probabilities: [0.05, 0.10, 0.20, 0.65]
7. Pick highest: "high" with 65% confidence
8. Decision: open_lane = True

Server → ESP32:

```json
{
  "prediction": "high",
  "confidence": 65.0,
  "open_lane": true,
  "timestamp": "2025-01-10T15:30:45",
  "stats": {
    "raw_count": 10,
    "scaled_count": 145.0,
    "hour": 17,
    "day_of_week": 4,
    "is_morning_rush": false,
    "is_evening_rush": true,
    "is_weekend": false
  }
}
```

ESP32 Action:

1. Parse JSON response
2. Display "HIGH 65.0%" on LCD
3. Check open_lane = true
4. Compare with current gate state
5. If different, trigger openGate()
6. Flash LEDs, beep, rotate servo

## Part 6: Key Concepts

### Flask Routes

```python
@app.route('/predict', methods=['POST'])
```

This decorator connects URL `/predict` to function `predict()`

### Request Object

```python
data = request.json          # Get JSON data
ip = request.remote_addr     # Get client IP
```

### Response Options

```python
return jsonify({'key': 'value'})              # Simple response
return jsonify({'error': 'Bad'}), 400         # With status code
```

### Why Normalize Features?

Model trained on scaled data. Raw data leads to wrong predictions.
Scaler ensures new data scaled same way as training data.

### Response Time

- Total: 50-100ms
- Network: 40-80ms (biggest factor)
- Model prediction: 10ms (very fast)
- Data processing: 5-10ms

## Part 7: Defense Questions

Q: What does the server do?
A: Receives vehicle count from ESP32, scales it by 14.5x to match training data range, runs ML model, sends back whether to open gate.

Q: Why Flask?
A: Lightweight, simple, perfect for 2 endpoints. More complex frameworks like Django are overkill for this use case.

Q: How does ESP32 communicate?
A: HTTP POST requests with JSON data every 30 seconds. Server responds with JSON containing prediction and gate decision.

Q: What if server crashes?
A: ESP32 has error handling and will show "Server Error" on LCD. Could add auto-restart scripts for production.

Q: Why so much data in response?
A: Extra stats help debugging. Shows raw and scaled counts, time features used. Production could be minimal.

Q: How fast is it?
A: 50-100ms total. Model prediction only 10ms. Network is the bottleneck, not the ML model.

Q: Can multiple ESP32s connect?
A: Yes. Flask handles requests sequentially but predictions are fast enough. For many simultaneous connections, use production server like Gunicorn.

Q: Why fixed time (Friday 5 PM)?
A: Demo purposes. Real deployment would use actual time. Fixed time ensures consistent behavior for presentations and testing.

Q: Why scale factor 14.5 specifically?
A: Calculated from model analysis. Found model predicts "high" at 145 vehicles. To make 10 toy cars trigger this: 145 ÷ 10 = 14.5.
