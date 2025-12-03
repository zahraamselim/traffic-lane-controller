from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import joblib
from datetime import datetime

app = Flask(__name__)

class TrafficLSTM(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.lstm = nn.LSTM(input_size, 256, num_layers=2, batch_first=True, dropout=0.3)
        self.dropout = nn.Dropout(0.4)
        self.fc1 = nn.Linear(256, 128)
        self.bn1 = nn.BatchNorm1d(128)
        self.relu = nn.ReLU()
        self.dropout2 = nn.Dropout(0.4)
        self.fc2 = nn.Linear(128, 4)
    
    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.dropout(out)
        out = self.fc1(out)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.dropout2(out)
        return self.fc2(out)

scaler = joblib.load('scaler.pkl')
le = joblib.load('label_encoder.pkl')
features = joblib.load('features.pkl')
config = joblib.load('config.pkl')

model = TrafficLSTM(input_size=config['input_size'])
model.load_state_dict(torch.load('traffic_model.pth', map_location='cpu'))
model.eval()

print("Server loaded successfully")

def prepare_features(totals, current_hour, current_day_of_week):
    totals = np.array(totals)
    
    hour_sin = np.sin(2 * np.pi * current_hour / 24)
    hour_cos = np.cos(2 * np.pi * current_hour / 24)
    is_peak_morning = 1.0 if 7 <= current_hour <= 9 else 0.0
    is_peak_evening = 1.0 if 16 <= current_hour <= 19 else 0.0
    is_night = 1.0 if current_hour >= 22 or current_hour <= 5 else 0.0
    is_weekend = 1.0 if current_day_of_week >= 5 else 0.0
    
    ma2 = np.convolve(totals, np.ones(2)/2, mode='valid')
    ma2 = np.pad(ma2, (1, 0), constant_values=totals[0])
    std2 = pd.Series(totals).rolling(2, min_periods=1).std().fillna(0).values
    
    ma4 = np.convolve(totals, np.ones(4)/4, mode='valid')
    ma4 = np.pad(ma4, (3, 0), constant_values=totals[0])
    std4 = pd.Series(totals).rolling(4, min_periods=1).std().fillna(0).values
    
    ma8 = np.convolve(totals, np.ones(8)/8, mode='valid')
    ma8 = np.pad(ma8, (7, 0), constant_values=totals[0])
    std8 = pd.Series(totals).rolling(8, min_periods=1).std().fillna(0).values
    
    diff1 = np.diff(totals, prepend=totals[0])
    diff4 = np.concatenate([[0,0,0,0], totals[4:] - totals[:-4]])
    
    lag1 = np.roll(totals, 1)
    lag1[0] = totals[0]
    lag2 = np.roll(totals, 2)
    lag2[:2] = totals[0]
    lag4 = np.roll(totals, 4)
    lag4[:4] = totals[0]
    
    data = []
    for i in range(len(totals)):
        row = [
            totals[i], hour_sin, hour_cos,
            is_peak_morning, is_peak_evening, is_night, is_weekend,
            ma2[i], std2[i], ma4[i], std4[i], ma8[i], std8[i],
            diff1[i], diff4[i], lag1[i], lag2[i], lag4[i]
        ]
        data.append(row)
    
    return np.array(data, dtype=np.float32)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        vehicle_counts = data['counts']
        current_hour = data.get('hour', datetime.now().hour)
        current_day = data.get('day_of_week', datetime.now().weekday())
        
        if len(vehicle_counts) != 16:
            return jsonify({'error': 'Need exactly 16 vehicle counts'}), 400
        
        features_array = prepare_features(vehicle_counts, current_hour, current_day)
        scaled = scaler.transform(features_array)
        tensor = torch.FloatTensor(scaled).unsqueeze(0)
        
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]
            pred_idx = torch.argmax(outputs).item()
        
        prediction = le.inverse_transform([pred_idx])[0]
        confidence = probs[pred_idx].item() * 100
        
        should_open_lane = prediction in ['heavy', 'high']
        
        return jsonify({
            'prediction': prediction,
            'confidence': round(confidence, 2),
            'open_lane': should_open_lane,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'model_loaded': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)