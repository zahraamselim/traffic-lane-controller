# Server Documentation

This document explains the Flask server from basics to advanced details.

## Part 1: Server Basics

### What is a Server?

A server is a program that waits for requests and sends back responses.

**Restaurant Analogy**:
- **Kitchen (Server)**: Waits for orders, prepares food, sends it out
- **Customer (ESP32)**: Places order, waits, receives food
- **Menu (API)**: List of what you can order

**Our Server**:
- Waits for ESP32 to send vehicle count data
- Processes data through ML model
- Sends back traffic prediction

### Why Do We Need a Server?

ESP32 is too small to run the neural network (only 520 KB RAM). Solution: ESP32 counts vehicles, server runs ML model.

**Communication Flow**:
```
ESP32 → WiFi → Server → ML Model → Server → WiFi → ESP32
```

### What is Flask?

Flask is a Python toolkit for building servers easily.

**Without Flask** (100+ lines of socket code)
**With Flask** (5 lines):
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

**Method**: POST (sending data to process)
**URL**: `http://192.168.1.100:5000/predict`
**Body**:
```json
{
  "counts": [5, 7, 6, 8, 7, 6, 5, 7, 8, 6, 7, 6],
  "hour": 17,
  "day_of_week": 4
}
```

### HTTP Response (Server sends back)

**Status Code**: 200 (success), 400 (bad data), 500 (error)
**Body**:
```json
{
  "prediction": "Heavy",
  "confidence": 65.0,
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

All 4 files must be from the same training session!

### The /predict Endpoint (Step by Step)

#### Step 1: Receive Data
```python
data = request.json
vehicle_counts = data['counts']  # List of 12 counts
current_hour = data.get('hour', datetime.now().hour)
current_day = data.get('day_of_week', datetime.now().weekday())
```

#### Step 2: Validate
```python
if len(vehicle_counts) != 12:
    return jsonify({'error': 'Expected 12 vehicle counts'}), 400
```

#### Step 3: Calculate Average
```python
avg_count = np.mean(vehicle_counts)
# [5, 7, 6, 8, 7, 6, 5, 7, 8, 6, 7, 6] → 6.5
```

#### Step 4: Create Time Features
```python
is_morning_rush = 1 if 7 <= current_hour <= 9 else 0
is_evening_rush = 1 if 16 <= current_hour <= 19 else 0
is_night = 1 if current_hour >= 22 or current_hour < 4 else 0
is_weekend = 1 if current_day >= 5 else 0
```

#### Step 5: Prepare Features Array
```python
features = np.array([[
    avg_count,
    current_hour,
    current_day,
    is_morning_rush,
    is_evening_rush,
    is_night,
    is_weekend
]])
# Shape: (1, 7) = 1 sample with 7 features
```

#### Step 6: Scale Features
```python
features_scaled = scaler.transform(features)
# Before: [28.0, 17, 4, 0, 1, 0, 0]
# After:  [2.31, 0.94, -0.15, 0, 1.42, -0.87, -0.94]
```

**Critical**: Use `transform()`, NOT `fit_transform()`!

#### Step 7: Predict
```python
predictions = model.predict(features_scaled, verbose=0)
# Output: [[0.05, 0.10, 0.70, 0.15]]
#          normal moderate heavy high

predicted_class = np.argmax(predictions[0])  # Index of max value = 2
confidence = float(predictions[0][predicted_class] * 100)  # 70.0
prediction = label_encoder.inverse_transform([predicted_class])[0]  # "heavy"
should_open = prediction in ['heavy', 'high']  # True
```

#### Step 8: Return Response
```python
return jsonify({
    'prediction': prediction,
    'confidence': round(confidence, 2),
    'open_lane': should_open,
    'timestamp': datetime.now().isoformat(),
    'stats': { ... }
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

## Part 4: Testing

### Test 1: Start Server
```bash
python server.py
```

**Expected**:
```
Loading model...
Model loaded: SimpleNN
Test Accuracy: 89.47%
Server running on http://0.0.0.0:5000
```

### Test 2: Check Health
Browser: `http://localhost:5000/health`

Or command line:
```bash
curl http://localhost:5000/health
```

### Test 3: Send Test Prediction

Create `test_server.py`:
```python
import requests
import json

url = "http://localhost:5000/predict"
data = {
    "counts": [25, 27, 26, 28, 30, 29, 27, 28, 26, 27, 29, 28],
    "hour": 17,
    "day_of_week": 4
}

response = requests.post(url, json=data)
print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2))
```

Run:
```bash
pip install requests
python test_server.py
```

**Expected**: Status 200, prediction "heavy", open_lane true

## Part 5: Common Problems

### Problem: "ModuleNotFoundError: No module named 'flask'"
**Solution**:
```bash
pip install -r requirements.txt
```

### Problem: "FileNotFoundError: traffic_model.h5"
**Solution**: Check folder structure:
```
project/
├── server.py
└── model/
    ├── traffic_model.h5
    ├── scaler.pkl
    ├── label_encoder.pkl
    └── config.pkl
```

### Problem: "Address already in use"
**Solution**: Change port in server.py:
```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

### Problem: ESP32 Can't Connect
**Check**:
1. Computer's IP address (use `ipconfig`)
2. ESP32 and computer on same WiFi network
3. Windows Firewall not blocking Python
4. Server actually running (check console)

### Problem: Server Crashes on Prediction
**Debug**: Add print statements:
```python
def predict():
    data = request.json
    print("Received:", data)  # See what was sent
    # ... rest of code
```

## Part 6: Key Concepts

### Flask Routes
```python
@app.route('/predict', methods=['POST'])
```
This decorator connects URL `/predict` to function `predict()`

### Request Object
```python
data = request.json          # Get JSON data
hour = request.args.get('h') # Get URL parameter (?h=17)
ip = request.remote_addr     # Get client IP
```

### Response Options
```python
return jsonify({'key': 'value'})              # Simple response
return jsonify({'error': 'Bad'}), 400         # With status code
```

### Why Normalize Features?
Model trained on scaled data. Raw data → wrong predictions.
Scaler ensures new data scaled same way as training data.

### Response Time
- Total: ~80ms
- Network: ~40ms (biggest factor)
- Model prediction: ~10ms (very fast)
- Data processing: ~30ms

## Part 7: Defense Questions

**Q: What does the server do?**
A: Receives vehicle counts from ESP32, runs ML model, sends back whether to open gate. Acts as bridge between lightweight ESP32 and heavy ML model.

**Q: Why Flask?**
A: Lightweight, simple, perfect for 2 endpoints. Other frameworks like Django are overkill.

**Q: How does ESP32 communicate?**
A: HTTP POST requests with JSON data. Server responds with JSON containing prediction and gate decision.

**Q: What if server crashes?**
A: ESP32 has retry logic. Server has try-catch blocks. Could add auto-restart scripts for production.

**Q: Why so much data in response?**
A: Extra stats help debugging. Production version could be minimal. Shows we thought about monitoring.

**Q: How fast is it?**
A: 50-100ms total. Model prediction only 10ms. Network is the bottleneck.

**Q: Can multiple ESP32s connect?**
A: Yes. Flask handles requests sequentially but predictions are fast enough. For many simultaneous connections, use production server like Gunicorn.

## Part 8: Going Further

### Production Deployment
Instead of Flask's built-in server, use Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

`-w 4` = 4 worker processes for handling multiple requests

### Model Optimization
Convert to TensorFlow Lite for faster inference and smaller size (~1 MB instead of ~12 MB).

### Add Security
- API keys for authentication
- Rate limiting to prevent spam
- Input validation for reasonable ranges

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Prediction: {prediction}")
```

Better than print statements: timestamps, log levels, can save to file.

### Memory Usage
- Model: ~50 MB
- Flask: ~30 MB
- Python: ~20 MB
- **Total: ~100 MB** (very lightweight!)

Can run on Raspberry Pi or old laptops.