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
        print("NEW PREDICTION REQUEST")
        
        data = request.json
        vehicle_counts = data['counts']
        
        print(f"Received counts: {vehicle_counts}")
        
        if len(vehicle_counts) != 1:
            print(f"ERROR: Expected 1 count, got {len(vehicle_counts)}")
            return jsonify({'error': 'Expected 1 vehicle count'}), 400
        
        total_count = vehicle_counts[0]
        scaled_total = total_count * 14.5
        current_hour = 17
        current_day = 4
        
        print(f"\nData Processing:")
        print(f"  Raw count: {total_count}")
        print(f"  Scaled count (14.5x): {scaled_total:.1f}")
        print(f"  Time: Friday 5:00 PM")
        
        is_morning_rush = 1 if 7 <= current_hour <= 9 else 0
        is_evening_rush = 1 if 16 <= current_hour <= 19 else 0
        is_night = 1 if current_hour >= 22 or current_hour < 4 else 0
        is_weekend = 1 if current_day >= 5 else 0
        
        print(f"\nTime Features:")
        print(f"  Morning rush: {'Yes' if is_morning_rush else 'No'}")
        print(f"  Evening rush: {'Yes' if is_evening_rush else 'No'}")
        print(f"  Night time: {'Yes' if is_night else 'No'}")
        print(f"  Weekend: {'Yes' if is_weekend else 'No'}")
        
        features = np.array([[
            scaled_total,
            current_hour,
            current_day,
            is_morning_rush,
            is_evening_rush,
            is_night,
            is_weekend
        ]])
        
        features_scaled = scaler.transform(features)
        
        print(f"\nRunning model prediction...")
        
        predictions = model.predict(features_scaled, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class] * 100)
        prediction = label_encoder.inverse_transform([predicted_class])[0]
        should_open = prediction in ['heavy', 'high']
        
        print(f"\nPrediction Results:")
        print(f"  Traffic Level: {prediction.upper()}")
        print(f"  Confidence: {confidence:.1f}%")
        print(f"  Gate Action: {'OPEN' if should_open else 'KEEP CLOSED'}")
        
        print(f"\nAll Class Probabilities:")
        for i, class_name in enumerate(label_encoder.classes_):
            prob = predictions[0][i] * 100
            print(f"  {class_name:10s} {prob:5.1f}%")
        
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
    print(f"\nDemo Settings:")
    print(f"  Prediction interval: 30 seconds")
    print(f"  Scale factor: 14.5x")
    print(f"  Fixed time: Friday 5 PM (rush hour)")
    print(f"  10 toy cars in 30 seconds will trigger high traffic")
    print(f"\nServer running on http://0.0.0.0:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)