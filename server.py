from flask import Flask, request, jsonify
import numpy as np
from tensorflow import keras
import joblib
from datetime import datetime

app = Flask(__name__)

MODEL_DIR = 'model'

print("Loading model...")
model = keras.models.load_model(f'{MODEL_DIR}/traffic_model.h5')
scaler = joblib.load(f'{MODEL_DIR}/scaler.pkl')
label_encoder = joblib.load(f'{MODEL_DIR}/label_encoder.pkl')
model_config = joblib.load(f'{MODEL_DIR}/config.pkl')

print(f"Model loaded: {model_config['model_type']}")
print(f"Features: {model_config['feature_names']}")
print(f"Classes: {label_encoder.classes_}")
print(f"Test Accuracy: {model_config['test_accuracy']:.4f}")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        vehicle_counts = data['counts']
        current_hour = data.get('hour', datetime.now().hour)
        current_day = data.get('day_of_week', datetime.now().weekday())
        
        if len(vehicle_counts) != 12:
            return jsonify({'error': 'Expected 12 vehicle counts'}), 400
        
        avg_count = np.mean(vehicle_counts)
        
        is_morning_rush = 1 if 7 <= current_hour <= 9 else 0
        is_evening_rush = 1 if 16 <= current_hour <= 19 else 0
        is_night = 1 if current_hour >= 22 or current_hour < 4 else 0
        is_weekend = 1 if current_day >= 5 else 0
        
        features = np.array([[
            avg_count,
            current_hour,
            current_day,
            is_morning_rush,
            is_evening_rush,
            is_night,
            is_weekend
        ]])
        
        features_scaled = scaler.transform(features)
        
        predictions = model.predict(features_scaled, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class] * 100)
        prediction = label_encoder.inverse_transform([predicted_class])[0]
        should_open = prediction in ['heavy', 'high']
        
        print(f"Prediction: {prediction} ({confidence:.1f}%) | Gate: {'OPEN' if should_open else 'CLOSED'}")
        
        return jsonify({
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'open_lane': should_open,
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'avg_count': float(round(avg_count, 1)),
                'min_count': int(np.min(vehicle_counts)),
                'max_count': int(np.max(vehicle_counts)),
                'hour': current_hour,
                'day_of_week': current_day,
                'is_morning_rush': bool(is_morning_rush),
                'is_evening_rush': bool(is_evening_rush),
                'is_weekend': bool(is_weekend)
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_type': model_config['model_type'],
        'classes': label_encoder.classes_.tolist(),
        'features': model_config['feature_names'],
        'test_accuracy': model_config['test_accuracy']
    })

if __name__ == '__main__':
    print(f"\nTraffic Prediction Server")
    print(f"Model Type: {model_config['model_type']}")
    print(f"Classes: {', '.join(label_encoder.classes_)}")
    print(f"Test Accuracy: {model_config['test_accuracy']:.2%}")
    print(f"\nServer running on http://0.0.0.0:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)