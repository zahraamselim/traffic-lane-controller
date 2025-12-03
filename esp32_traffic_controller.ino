#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>
#include <ESP32Servo.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";

const int IR_SENSOR_IN = 34;
const int IR_SENSOR_OUT = 35;
const int SERVO_PIN = 13;
const int BUZZER_PIN = 12;
const int LED_PINS[] = {14, 27, 26, 25};

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo servo;

int vehicleCounts[16] = {0};
int currentIndex = 0;
unsigned long lastCountTime = 0;
unsigned long intervalDuration = 900000;

int currentVehicles = 0;
bool laneOpen = false;

void setup() {
  Serial.begin(115200);
  
  pinMode(IR_SENSOR_IN, INPUT);
  pinMode(IR_SENSOR_OUT, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  for(int i = 0; i < 4; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  servo.attach(SERVO_PIN);
  servo.write(0);
  
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Traffic System");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
  
  lastCountTime = millis();
}

void loop() {
  static bool lastInState = HIGH;
  static bool lastOutState = HIGH;
  
  bool inState = digitalRead(IR_SENSOR_IN);
  bool outState = digitalRead(IR_SENSOR_OUT);
  
  if (inState == LOW && lastInState == HIGH) {
    currentVehicles++;
    Serial.print("Vehicle IN. Total: ");
    Serial.println(currentVehicles);
    delay(100);
  }
  
  if (outState == LOW && lastOutState == HIGH) {
    if (currentVehicles > 0) {
      currentVehicles--;
      Serial.print("Vehicle OUT. Total: ");
      Serial.println(currentVehicles);
    }
    delay(100);
  }
  
  lastInState = inState;
  lastOutState = outState;
  
  if (millis() - lastCountTime >= intervalDuration) {
    vehicleCounts[currentIndex] = currentVehicles;
    currentIndex = (currentIndex + 1) % 16;
    
    Serial.print("Saved count: ");
    Serial.println(currentVehicles);
    
    currentVehicles = 0;
    lastCountTime = millis();
    
    if (currentIndex == 0) {
      makePrediction();
    }
  }
  
  updateDisplay();
  delay(50);
}

void makePrediction() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }
  
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<512> doc;
  JsonArray counts = doc.createNestedArray("counts");
  
  for(int i = 0; i < 16; i++) {
    counts.add(vehicleCounts[i]);
  }
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  Serial.println("Sending prediction request...");
  int httpCode = http.POST(jsonData);
  
  if (httpCode == 200) {
    String response = http.getString();
    
    StaticJsonDocument<256> responseDoc;
    deserializeJson(responseDoc, response);
    
    const char* prediction = responseDoc["prediction"];
    float confidence = responseDoc["confidence"];
    bool shouldOpen = responseDoc["open_lane"];
    
    Serial.print("Prediction: ");
    Serial.print(prediction);
    Serial.print(" (");
    Serial.print(confidence);
    Serial.println("%)");
    
    if (shouldOpen && !laneOpen) {
      openLane();
    } else if (!shouldOpen && laneOpen) {
      closeLane();
    }
  } else {
    Serial.print("HTTP Error: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

void openLane() {
  Serial.println("Opening extra lane...");
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("OPENING LANE");
  lcd.setCursor(0, 1);
  lcd.print("Stay Clear!");
  
  for(int i = 0; i < 5; i++) {
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], HIGH);
    }
    tone(BUZZER_PIN, 1000);
    delay(200);
    
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], LOW);
    }
    noTone(BUZZER_PIN);
    delay(200);
  }
  
  for(int pos = 0; pos <= 90; pos++) {
    servo.write(pos);
    delay(15);
  }
  
  laneOpen = true;
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Extra Lane");
  lcd.setCursor(0, 1);
  lcd.print("OPEN");
  
  delay(2000);
}

void closeLane() {
  Serial.println("Closing extra lane...");
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("CLOSING LANE");
  lcd.setCursor(0, 1);
  lcd.print("Stay Clear!");
  
  for(int i = 0; i < 5; i++) {
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], HIGH);
    }
    tone(BUZZER_PIN, 1000);
    delay(200);
    
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], LOW);
    }
    noTone(BUZZER_PIN);
    delay(200);
  }
  
  for(int pos = 90; pos >= 0; pos--) {
    servo.write(pos);
    delay(15);
  }
  
  laneOpen = false;
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Extra Lane");
  lcd.setCursor(0, 1);
  lcd.print("CLOSED");
  
  delay(2000);
}

void updateDisplay() {
  static unsigned long lastUpdate = 0;
  
  if (millis() - lastUpdate >= 2000) {
    if (!laneOpen || (millis() % 4000 < 2000)) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Vehicles: ");
      lcd.print(currentVehicles);
      
      lcd.setCursor(0, 1);
      if (laneOpen) {
        lcd.print("Lane: OPEN");
      } else {
        lcd.print("Lane: CLOSED");
      }
    }
    
    lastUpdate = millis();
  }
}