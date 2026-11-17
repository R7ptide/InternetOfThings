#include <Servo.h>

const int SERVO_PIN = 9;
const bool REATTACH = true;               // attach -> move -> detach on every step
const int POSITIONS[] = {90, 45, 90, 135, 90, 15, 90};  
Servo diverter;

void setup() {
  Serial.begin(115200);
  if (!REATTACH) diverter.attach(SERVO_PIN);
}

void loop() {
  for (int angle : POSITIONS) {
    Serial.print("angle ");
    Serial.println(angle);
    if (REATTACH) diverter.attach(SERVO_PIN);
    diverter.write(angle);
    delay(700);                           // time for the arm to arrive
    if (REATTACH) diverter.detach();      // stops the pulses; the arm goes slack
    delay(500);
  }
  Serial.println("--- cycle done ---");
  delay(2000);
}
