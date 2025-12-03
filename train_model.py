import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import warnings
import config

warnings.filterwarnings('ignore')
np.random.seed(42)
tf.random.set_seed(42)

print("Loading data...")
df = pd.read_csv(config.DATA_FILE)
df['Hour'] = pd.to_datetime(df['Time'], format='%I:%M:%S %p').dt.hour
day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
           'Friday': 4, 'Saturday': 5, 'Sunday': 6}
df['DayNum'] = df['Day of the week'].map(day_map)
print(f"Loaded {len(df)} records with classes: {df['Traffic Situation'].unique()}")

def create_time_features(hour, day_of_week):
    return {
        'hour_sin': np.sin(2 * np.pi * hour / 24),
        'hour_cos': np.cos(2 * np.pi * hour / 24),
        'day_sin': np.sin(2 * np.pi * day_of_week / 7),
        'day_cos': np.cos(2 * np.pi * day_of_week / 7),
        'is_morning_rush': ((hour >= config.RUSH_HOUR_MORNING[0]) & 
                           (hour <= config.RUSH_HOUR_MORNING[1])).astype(float),
        'is_evening_rush': ((hour >= config.RUSH_HOUR_EVENING[0]) & 
                           (hour <= config.RUSH_HOUR_EVENING[1])).astype(float),
        'is_night': ((hour >= config.NIGHT_TIME[0]) | 
                    (hour < config.NIGHT_TIME[1])).astype(float),
        'is_weekend': (day_of_week >= 5).astype(float)
    }

time_features = create_time_features(df['Hour'].values, df['DayNum'].values)
for key, value in time_features.items():
    df[key] = value

def create_sequences(data, seq_length):
    sequences, time_feats, labels = [], [], []
    for i in range(len(data) - seq_length):
        sequences.append(data.iloc[i:i+seq_length]['Total'].values)
        next_point = data.iloc[i+seq_length]
        time_feats.append([next_point['hour_sin'], next_point['hour_cos'],
                          next_point['day_sin'], next_point['day_cos'],
                          next_point['is_morning_rush'], next_point['is_evening_rush'],
                          next_point['is_night'], next_point['is_weekend']])
        labels.append(next_point['Traffic Situation'])
    return np.array(sequences), np.array(time_feats), np.array(labels)

print(f"Creating sequences with window size {config.SEQUENCE_LENGTH}...")
X_seq, X_time, y = create_sequences(df, config.SEQUENCE_LENGTH)
print(f"Created {len(X_seq)} sequences")

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
print("\nLabel encoding:")
for i, label in enumerate(label_encoder.classes_):
    print(f"  {label}: {i}")

X_seq_temp, X_seq_test, X_time_temp, X_time_test, y_temp, y_test = train_test_split(
    X_seq, X_time, y_encoded, test_size=config.TEST_SPLIT, random_state=42, stratify=y_encoded
)
X_seq_train, X_seq_val, X_time_train, X_time_val, y_train, y_val = train_test_split(
    X_seq_temp, X_time_temp, y_temp, 
    test_size=config.VAL_SPLIT/(config.TRAIN_SPLIT + config.VAL_SPLIT), 
    random_state=42, stratify=y_temp
)

scaler = StandardScaler()
X_seq_train = scaler.fit_transform(X_seq_train).reshape(-1, config.SEQUENCE_LENGTH, 1)
X_seq_val = scaler.transform(X_seq_val).reshape(-1, config.SEQUENCE_LENGTH, 1)
X_seq_test = scaler.transform(X_seq_test).reshape(-1, config.SEQUENCE_LENGTH, 1)

print(f"\nDataset split: Train={len(X_seq_train)}, Val={len(X_seq_val)}, Test={len(X_seq_test)}")

sequence_input = keras.Input(shape=(config.SEQUENCE_LENGTH, 1), name='sequence_input')
time_input = keras.Input(shape=(config.TIME_FEATURES,), name='time_input')

x = keras.layers.LSTM(config.HIDDEN_SIZE, return_sequences=True)(sequence_input)
x = keras.layers.Dropout(0.2)(x)
x = keras.layers.LSTM(config.HIDDEN_SIZE)(x)
x = keras.layers.Dropout(0.3)(x)
x = keras.layers.concatenate([x, time_input])
x = keras.layers.Dense(32, activation='relu')(x)
x = keras.layers.Dropout(0.3)(x)
output = keras.layers.Dense(len(label_encoder.classes_), activation='softmax')(x)

model = keras.Model(inputs=[sequence_input, time_input], outputs=output)
model.compile(optimizer=keras.optimizers.Adam(learning_rate=config.LEARNING_RATE),
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

print("\nModel architecture:")
model.summary()

callbacks = [
    keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
    keras.callbacks.ModelCheckpoint(f'{config.MODEL_DIR}/traffic_model.h5', 
                                   monitor='val_accuracy', save_best_only=True)
]

print("\nTraining started...")
history = model.fit([X_seq_train, X_time_train], y_train,
                   validation_data=([X_seq_val, X_time_val], y_val),
                   epochs=config.NUM_EPOCHS,
                   batch_size=config.BATCH_SIZE,
                   callbacks=callbacks,
                   verbose=1)

model = keras.models.load_model(f'{config.MODEL_DIR}/traffic_model.h5')
test_loss, test_acc = model.evaluate([X_seq_test, X_time_test], y_test, verbose=0)
print(f"\nTest results: Loss={test_loss:.4f}, Accuracy={test_acc:.4f}")

y_pred = np.argmax(model.predict([X_seq_test, X_time_test], verbose=0), axis=1)
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

joblib.dump(scaler, f'{config.MODEL_DIR}/scaler.pkl')
joblib.dump(label_encoder, f'{config.MODEL_DIR}/label_encoder.pkl')
joblib.dump({
    'sequence_length': config.SEQUENCE_LENGTH,
    'time_features': config.TIME_FEATURES,
    'hidden_size': config.HIDDEN_SIZE,
    'num_classes': len(label_encoder.classes_),
    'model_type': 'TrafficLSTM'
}, f'{config.MODEL_DIR}/config.pkl')

print(f"\nModel saved to {config.MODEL_DIR}/")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(history.history['loss'], label='Train')
ax1.plot(history.history['val_loss'], label='Validation')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.set_title('Loss')
ax1.legend()
ax1.grid(True)

ax2.plot(history.history['accuracy'], label='Train')
ax2.plot(history.history['val_accuracy'], label='Validation')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy')
ax2.set_title('Accuracy')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig('training_history.png', dpi=300)
print("Training plots saved to training_history.png")