#include <Servo.h>

const int SERVO_PIN = 9;
const int POSITIONS[] = {90, 45, 90, 135, 90, 0, 90};
Servo diverter;

void setup() {
  Serial.begin(115200);
  diverter.attach(SERVO_PIN);
}

void loop() {
  for (int angle : POSITIONS) {
    Serial.print("angle ");
    Serial.println(angle);
    diverter.write(angle);
    delay(1200);
  }
  delay(2000);
}
