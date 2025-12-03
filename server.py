from flask import Flask, request, jsonify
import numpy as np
from tensorflow import keras
import joblib
from datetime import datetime
import config

app = Flask(__name__)

print("Loading model...")
model = keras.models.load_model(f'{config.MODEL_DIR}/traffic_model.h5')
scaler = joblib.load(f'{config.MODEL_DIR}/scaler.pkl')
label_encoder = joblib.load(f'{config.MODEL_DIR}/label_encoder.pkl')
model_config = joblib.load(f'{config.MODEL_DIR}/config.pkl')
print(f"Model loaded: {model_config['sequence_length']} sequence length, Classes: {label_encoder.classes_}")

def create_time_features(hour, day_of_week):
    return np.array([
        np.sin(2 * np.pi * hour / 24),
        np.cos(2 * np.pi * hour / 24),
        np.sin(2 * np.pi * day_of_week / 7),
        np.cos(2 * np.pi * day_of_week / 7),
        1.0 if config.RUSH_HOUR_MORNING[0] <= hour <= config.RUSH_HOUR_MORNING[1] else 0.0,
        1.0 if config.RUSH_HOUR_EVENING[0] <= hour <= config.RUSH_HOUR_EVENING[1] else 0.0,
        1.0 if hour >= config.NIGHT_TIME[0] or hour < config.NIGHT_TIME[1] else 0.0,
        1.0 if day_of_week >= 5 else 0.0
    ])

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        vehicle_counts = data['counts']
        current_hour = data.get('hour', datetime.now().hour)
        current_day = data.get('day_of_week', datetime.now().weekday())
        
        if len(vehicle_counts) != model_config['sequence_length']:
            return jsonify({'error': f'Expected {model_config["sequence_length"]} counts'}), 400
        
        sequence = scaler.transform(np.array(vehicle_counts).reshape(1, -1))
        sequence = sequence.reshape(1, model_config['sequence_length'], 1)
        time_features = create_time_features(current_hour, current_day).reshape(1, -1)
        
        predictions = model.predict([sequence, time_features], verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class] * 100)  # Convert to native Python float
        prediction = label_encoder.inverse_transform([predicted_class])[0]
        should_open = prediction in ['heavy', 'high']
        
        print(f"Prediction: {prediction} ({confidence:.1f}%) | Lane: {'OPEN' if should_open else 'CLOSED'}")
        
        return jsonify({
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'open_lane': should_open,
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'avg_count': float(round(np.mean(vehicle_counts), 1)),  # Convert to native Python float
                'min_count': int(np.min(vehicle_counts)),
                'max_count': int(np.max(vehicle_counts)),
                'hour': current_hour,
                'day_of_week': current_day
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
        'sequence_length': model_config['sequence_length']
    })

if __name__ == '__main__':
    print(f"\nTraffic Prediction Server")
    print(f"Model: {model_config['model_type']}")
    print(f"Classes: {', '.join(label_encoder.classes_)}")
    print(f"\nStarting on http://0.0.0.0:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)