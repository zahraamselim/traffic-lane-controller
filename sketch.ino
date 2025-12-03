#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <LiquidCrystal.h>
#include <ESP32Servo.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";

const int BTN_IN = 16;
const int BTN_OUT = 17;
const int SERVO = 5;
const int BUZZER = 23;
const int LEDS[] = {2, 4, 12, 13};

const unsigned long STEP_INTERVAL = 5000;
const unsigned long STRIDE_INTERVAL = 15000;
const unsigned long WINDOW_SIZE = 60000;

const byte POINTS_PER_WINDOW = WINDOW_SIZE / STEP_INTERVAL;
const byte POINTS_PER_STRIDE = STRIDE_INTERVAL / STEP_INTERVAL;

LiquidCrystal lcd(14, 27, 26, 25, 33, 32);
Servo servo;

int traffic[POINTS_PER_WINDOW];
byte idx = 0;
int count = 0;
int totalCount = 0;
bool gateOpen = false;

unsigned long lastSave = 0;
unsigned long lastDecision = 0;
unsigned long decisionStart = 0;
bool deciding = false;

bool lastIn = LOW;
bool lastOut = LOW;
unsigned long lastInTime = 0;
unsigned long lastOutTime = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(BTN_IN, INPUT);
  pinMode(BTN_OUT, INPUT);
  pinMode(BUZZER, OUTPUT);
  
  for(byte i = 0; i < 4; i++) {
    pinMode(LEDS[i], OUTPUT);
    digitalWrite(LEDS[i], LOW);
  }
  
  servo.attach(SERVO);
  servo.write(0);
  
  lcd.begin(16, 2);
  lcd.print("Traffic System");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  
  lcd.clear();
  lcd.print("Ready");
  delay(1000);
  
  for(byte i = 0; i < POINTS_PER_WINDOW; i++) traffic[i] = 0;
  
  lastSave = lastDecision = millis();
}

void loop() {
  unsigned long now = millis();
  
  bool inState = digitalRead(BTN_IN);
  bool outState = digitalRead(BTN_OUT);
  
  if (inState && !lastIn && (now - lastInTime > 300)) {
    count++;
    totalCount++;
    lastInTime = now;
  }
  
  if (outState && !lastOut && (now - lastOutTime > 300)) {
    if (count > 0) count--;
    if (totalCount > 0) totalCount--;
    lastOutTime = now;
  }
  
  lastIn = inState;
  lastOut = outState;
  
  if (now - lastSave >= STEP_INTERVAL) {
    traffic[idx] = count;
    idx = (idx + 1) % POINTS_PER_WINDOW;
    count = 0;
    lastSave = now;
  }
  
  if (now - lastDecision >= STRIDE_INTERVAL) {
    makeDecision();
    lastDecision = now;
    totalCount = 0;
  }
  
  if (deciding && (now - decisionStart >= 5000)) {
    deciding = false;
  }
  
  static unsigned long lastDisp = 0;
  if (!deciding && now - lastDisp >= 200) {
    lcd.clear();
    lcd.print("Vehicles: ");
    lcd.print(totalCount);
    lcd.setCursor(0, 1);
    lcd.print("Next: ");
    lcd.print((STRIDE_INTERVAL - (now - lastDecision)) / 1000);
    lcd.print("s");
    lastDisp = now;
  }
  
  delay(10);
}

void makeDecision() {
  int window[POINTS_PER_WINDOW];
  byte dataPoints = min(idx, POINTS_PER_WINDOW);
  
  if (dataPoints < POINTS_PER_WINDOW) {
    for(byte i = 0; i < POINTS_PER_WINDOW; i++) {
      window[i] = traffic[i % dataPoints];
    }
  } else {
    for(byte i = 0; i < POINTS_PER_WINDOW; i++) {
      byte actualIdx = (idx - POINTS_PER_WINDOW + i + POINTS_PER_WINDOW) % POINTS_PER_WINDOW;
      window[i] = traffic[actualIdx];
    }
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    lcd.clear();
    lcd.print("WiFi Error");
    deciding = true;
    decisionStart = millis();
    delay(3000);
    return;
  }
  
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<512> doc;
  JsonArray counts = doc.createNestedArray("counts");
  
  for(byte i = 0; i < POINTS_PER_WINDOW; i++) {
    counts.add(window[i]);
  }
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  Serial.println("Sending to server...");
  int httpCode = http.POST(jsonData);
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    
    StaticJsonDocument<256> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (error) {
      Serial.print("JSON error: ");
      Serial.println(error.c_str());
      http.end();
      return;
    }
    
    const char* prediction = responseDoc["prediction"];
    float confidence = responseDoc["confidence"];
    bool shouldOpen = responseDoc["open_lane"];
    
    Serial.print("Prediction: ");
    Serial.print(prediction);
    Serial.print(" (");
    Serial.print(confidence);
    Serial.println("%)");
    
    lcd.clear();
    lcd.print("Conf: ");
    lcd.print(confidence, 1);
    lcd.print("%");
    lcd.setCursor(0, 1);
    
    if (shouldOpen != gateOpen) {
      lcd.print(shouldOpen ? "OPEN GATE" : "CLOSE GATE");
      deciding = true;
      decisionStart = millis();
      delay(3000);
      
      if (shouldOpen) {
        openGate();
      } else {
        closeGate();
      }
    } else {
      lcd.print(gateOpen ? "KEEP OPEN" : "KEEP CLOSED");
      deciding = true;
      decisionStart = millis();
      delay(3000);
    }
  } else {
    Serial.print("HTTP Error: ");
    Serial.println(httpCode);
    lcd.clear();
    lcd.print("Server Error");
    lcd.setCursor(0, 1);
    lcd.print("Code: ");
    lcd.print(httpCode);
    deciding = true;
    decisionStart = millis();
    delay(3000);
  }
  
  http.end();
}

void openGate() {
  lcd.clear();
  lcd.print("OPENING GATE");
  
  for(byte i = 0; i < 3; i++) {
    for(byte j = 0; j < 4; j++) digitalWrite(LEDS[j], HIGH);
    tone(BUZZER, 1000);
    delay(200);
    for(byte j = 0; j < 4; j++) digitalWrite(LEDS[j], LOW);
    noTone(BUZZER);
    delay(200);
  }
  
  for(int pos = 0; pos <= 90; pos++) {
    servo.write(pos);
    delay(15);
  }
  
  gateOpen = true;
}

void closeGate() {
  lcd.clear();
  lcd.print("CLOSING GATE");
  
  for(byte i = 0; i < 3; i++) {
    for(byte j = 0; j < 4; j++) digitalWrite(LEDS[j], HIGH);
    tone(BUZZER, 1000);
    delay(200);
    for(byte j = 0; j < 4; j++) digitalWrite(LEDS[j], LOW);
    noTone(BUZZER);
    delay(200);
  }
  
  for(int pos = 90; pos >= 0; pos--) {
    servo.write(pos);
    delay(15);
  }
  
  gateOpen = false;
}