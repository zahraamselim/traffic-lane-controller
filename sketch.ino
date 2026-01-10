#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <LiquidCrystal.h>
#include <ESP32Servo.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/predict";

const int IR_SENSOR_IN = 34;
const int IR_SENSOR_OUT = 35;
const int SERVO_PIN = 13;
const int BUZZER_PIN = 12;
const int LED_PINS[] = {14, 27, 26, 25};

const int RS = 19;
const int E = 23;
const int D4 = 18;
const int D5 = 17;
const int D6 = 16;
const int D7 = 15;

const unsigned long DECISION_INTERVAL = 30000;

LiquidCrystal lcd(RS, E, D4, D5, D6, D7);
Servo servo;

int currentCount = 0;
bool gateOpen = false;

unsigned long lastDecision = 0;
unsigned long lastDisplay = 0;

bool lastInState = HIGH;
bool lastOutState = HIGH;
unsigned long lastInTime = 0;
unsigned long lastOutTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  pinMode(IR_SENSOR_IN, INPUT);
  pinMode(IR_SENSOR_OUT, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  for(int i = 0; i < 4; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  servo.attach(SERVO_PIN);
  servo.write(0);
  
  lcd.begin(16, 2);
  lcd.print("Traffic System");
  lcd.setCursor(0, 1);
  lcd.print("Connecting WiFi");
  
  Serial.println("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if(WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    
    lcd.clear();
    lcd.print("WiFi Connected");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());
    delay(2000);
  } else {
    Serial.println("\nWiFi failed");
    lcd.clear();
    lcd.print("WiFi Failed");
    delay(3000);
  }
  
  lcd.clear();
  lcd.print("System Ready");
  delay(1000);
  
  lastDecision = millis();
  Serial.println("System ready");
  Serial.println("Making prediction every 30 seconds");
}

void loop() {
  unsigned long now = millis();
  
  bool inState = digitalRead(IR_SENSOR_IN);
  bool outState = digitalRead(IR_SENSOR_OUT);
  
  if (inState == LOW && lastInState == HIGH && (now - lastInTime > 300)) {
    currentCount++;
    lastInTime = now;
    
    Serial.print("Vehicle IN. Count: ");
    Serial.println(currentCount);
    
    tone(BUZZER_PIN, 1500);
    delay(100);
    noTone(BUZZER_PIN);
  }
  
  if (outState == LOW && lastOutState == HIGH && (now - lastOutTime > 300)) {
    if (currentCount > 0) currentCount--;
    lastOutTime = now;
    
    Serial.print("Vehicle OUT. Count: ");
    Serial.println(currentCount);
    
    tone(BUZZER_PIN, 800);
    delay(100);
    noTone(BUZZER_PIN);
  }
  
  lastInState = inState;
  lastOutState = outState;
  
  if (now - lastDecision >= DECISION_INTERVAL) {
    makeDecision();
    lastDecision = now;
  }
  
  if (now - lastDisplay >= 500) {
    updateDisplay(now);
    lastDisplay = now;
  }
  
  delay(50);
}

void makeDecision() {
  Serial.println("Making decision");
  Serial.print("Current count: ");
  Serial.println(currentCount);
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    lcd.clear();
    lcd.print("WiFi Error");
    delay(2000);
    return;
  }
  
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<128> doc;
  JsonArray counts = doc.createNestedArray("counts");
  counts.add(currentCount);
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  Serial.println("Sending to server");
  int httpCode = http.POST(jsonData);
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (error) {
      Serial.print("Parse error: ");
      Serial.println(error.c_str());
      lcd.clear();
      lcd.print("Parse Error");
      delay(2000);
      http.end();
      return;
    }
    
    const char* prediction = responseDoc["prediction"];
    float confidence = responseDoc["confidence"];
    bool shouldOpen = responseDoc["open_lane"];
    
    Serial.print("Prediction: ");
    Serial.print(prediction);
    Serial.print(" (");
    Serial.print(confidence, 1);
    Serial.println("%)");
    
    lcd.clear();
    lcd.print(prediction);
    lcd.setCursor(0, 1);
    lcd.print("Conf: ");
    lcd.print(confidence, 1);
    lcd.print("%");
    delay(2000);
    
    if (shouldOpen != gateOpen) {
      if (shouldOpen) {
        openGate();
      } else {
        closeGate();
      }
    } else {
      lcd.clear();
      lcd.print(gateOpen ? "Keep Open" : "Keep Closed");
      delay(2000);
    }
    
  } else {
    Serial.print("Server error: ");
    Serial.println(httpCode);
    lcd.clear();
    lcd.print("Server Error");
    lcd.setCursor(0, 1);
    lcd.print("Code: ");
    lcd.print(httpCode);
    delay(2000);
  }
  
  http.end();
  Serial.println("Decision complete");
}

void openGate() {
  Serial.println("Opening gate");
  
  for(int i = 0; i < 5; i++) {
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], HIGH);
    }
    tone(BUZZER_PIN, 1000);
    delay(300);
    
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], LOW);
    }
    noTone(BUZZER_PIN);
    delay(300);
  }
  
  lcd.clear();
  lcd.print("Opening Gate");
  
  for(int pos = 0; pos <= 90; pos++) {
    servo.write(pos);
    delay(15);
  }
  
  gateOpen = true;
  Serial.println("Gate opened");
}

void closeGate() {
  Serial.println("Closing gate");
  
  for(int i = 0; i < 5; i++) {
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], HIGH);
    }
    tone(BUZZER_PIN, 1000);
    delay(300);
    
    for(int j = 0; j < 4; j++) {
      digitalWrite(LED_PINS[j], LOW);
    }
    noTone(BUZZER_PIN);
    delay(300);
  }
  
  lcd.clear();
  lcd.print("Closing Gate");
  
  for(int pos = 90; pos >= 0; pos--) {
    servo.write(pos);
    delay(15);
  }
  
  gateOpen = false;
  Serial.println("Gate closed");
}

void updateDisplay(unsigned long now) {
  lcd.clear();
  lcd.print("Count: ");
  lcd.print(currentCount);
  
  lcd.setCursor(0, 1);
  lcd.print("Gate: ");
  lcd.print(gateOpen ? "OPEN" : "CLOSED");
  
  unsigned long timeToNext = DECISION_INTERVAL - (now - lastDecision);
  lcd.setCursor(12, 1);
  lcd.print(timeToNext / 1000);
  lcd.print("s");
}