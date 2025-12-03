# Circuit Wiring Guide

## Component Layout

```
                    ESP32
                  ┌─────────┐
                  │         │
   IR Sensor IN──►│ GPIO34  │
   IR Sensor OUT─►│ GPIO35  │
                  │         │
   LCD SDA───────►│ GPIO21  │
   LCD SCL───────►│ GPIO22  │
                  │         │
   Servo─────────►│ GPIO13  │
   Buzzer────────►│ GPIO12  │
                  │         │
   LED 1─────────►│ GPIO14  │
   LED 2─────────►│ GPIO27  │
   LED 3─────────►│ GPIO26  │
   LED 4─────────►│ GPIO25  │
                  │         │
   3.3V──────────►│ 3V3     │
   GND───────────►│ GND     │
                  └─────────┘
```

## Power Distribution

### Breadboard Power Rails

- **Red rail (+)**: Connect to ESP32 3V3 pin
- **Blue rail (-)**: Connect to ESP32 GND pin

### Component Power

All components use the breadboard rails:

- IR sensors: 3.3V from red rail
- LCD: 5V (if available) or 3.3V
- Servo: 5V (requires external power for high torque)
- LEDs and buzzer: Powered through GPIO pins

## Step-by-Step Wiring

### 1. IR Sensors (Entry and Exit Detection)

**IR Sensor IN (Entry):**

- VCC → Breadboard red rail (+)
- GND → Breadboard blue rail (-)
- OUT → ESP32 GPIO34

**IR Sensor OUT (Exit):**

- VCC → Breadboard red rail (+)
- GND → Breadboard blue rail (-)
- OUT → ESP32 GPIO35

### 2. LCD Display (16x2 with I2C)

- VCC → Breadboard red rail (+)
- GND → Breadboard blue rail (-)
- SDA → ESP32 GPIO21
- SCL → ESP32 GPIO22

**Note**: I2C address is usually 0x27 or 0x3F. If LCD doesn't work, try changing the address in code.

### 3. Servo Motor (Lane Barrier)

- Brown wire (GND) → Breadboard blue rail (-)
- Red wire (VCC) → External 5V power or breadboard red rail
- Orange wire (Signal) → ESP32 GPIO13

**Important**: If servo draws too much current, use a separate 5V power supply.

### 4. Warning LEDs (4x Red)

For each LED (repeat for GPIO14, 27, 26, 25):

```
ESP32 GPIO pin ─── 220Ω Resistor ─── LED Anode (+)
                                          │
                                     LED Cathode (-)
                                          │
                                    Breadboard GND
```

**LED Polarity:**

- Long leg = Anode (+) = to resistor
- Short leg = Cathode (-) = to GND

### 5. Buzzer (Audio Warning)

```
ESP32 GPIO12 ─── 100Ω Resistor ─── Buzzer (+)
                                        │
                                   Buzzer (-)
                                        │
                                  Breadboard GND
```

## Resistor Color Codes

### 220Ω (for LEDs)

- Red, Red, Brown, Gold
- Band 1: Red (2)
- Band 2: Red (2)
- Band 3: Brown (×10)
- Band 4: Gold (±5%)

### 100Ω (for Buzzer)

- Brown, Black, Brown, Gold
- Band 1: Brown (1)
- Band 2: Black (0)
- Band 3: Brown (×10)
- Band 4: Gold (±5%)

## Connection Verification Checklist

Before powering on:

- [ ] All GND connections to blue rail
- [ ] All VCC connections to red rail
- [ ] Breadboard rails connected to ESP32
- [ ] No short circuits between + and - rails
- [ ] LEDs oriented correctly (long leg to resistor)
- [ ] Resistors in series with LEDs and buzzer
- [ ] I2C wires (SDA/SCL) not swapped
- [ ] Servo signal wire to GPIO13 only
- [ ] IR sensor OUT pins to correct GPIO

## Testing Individual Components

### Test LEDs

```cpp
void setup() {
  pinMode(14, OUTPUT);
  digitalWrite(14, HIGH); // LED should light up
}
```

### Test Buzzer

```cpp
void setup() {
  pinMode(12, OUTPUT);
  tone(12, 1000); // Should beep at 1000Hz
}
```

### Test Servo

```cpp
#include <ESP32Servo.h>
Servo servo;
void setup() {
  servo.attach(13);
  servo.write(90); // Should move to 90 degrees
}
```

### Test LCD

```cpp
#include <LiquidCrystal_I2C.h>
LiquidCrystal_I2C lcd(0x27, 16, 2);
void setup() {
  lcd.init();
  lcd.backlight();
  lcd.print("Hello!");
}
```

### Test IR Sensors

```cpp
void setup() {
  Serial.begin(115200);
  pinMode(34, INPUT);
  pinMode(35, INPUT);
}
void loop() {
  Serial.print("IN: ");
  Serial.print(digitalRead(34));
  Serial.print(" OUT: ");
  Serial.println(digitalRead(35));
  delay(100);
}
```

## Common Issues

### LCD Backlight On But No Text

- Wrong I2C address (try 0x3F instead of 0x27)
- Adjust contrast potentiometer on I2C module

### Servo Jitters or Doesn't Move

- Insufficient power (use external 5V supply)
- Loose connection to GPIO13

### LEDs Dim or Not Lighting

- Resistor value too high (should be 220Ω)
- LED backwards (swap anode/cathode)

### Buzzer Silent

- Check resistor (100Ω, not higher)
- Verify positive lead to GPIO through resistor

### IR Sensors Always Triggered

- Too sensitive (adjust if potentiometer available)
- Ambient IR interference (shield sensors)

## Wokwi Simulation

To test the circuit in Wokwi simulator:

1. Go to wokwi.com
2. Create new ESP32 project
3. Upload the diagram.json file
4. Upload the esp32_traffic_controller.ino code
5. Click "Start Simulation"

**Note**: WiFi functionality won't work in simulation, but you can test the hardware logic.

## Physical Build Tips

1. **Use different wire colors** for easier debugging:

   - Red: Power (3.3V/5V)
   - Black: Ground
   - Yellow: Signal wires
   - Blue: I2C (SDA/SCL)

2. **Keep wires short** to reduce noise and interference

3. **Mount ESP32 securely** to prevent accidental disconnections

4. **Label components** especially multiple LEDs

5. **Test incrementally** add one component at a time

6. **Use a multimeter** to verify connections before powering on
