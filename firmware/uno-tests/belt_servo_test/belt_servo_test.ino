#include <Servo.h>

const int BELT_PIN = 6;
const int STOP_ANGLE = 90;
Servo belt;

// speed in percent -100 (full reverse) .. 0 (stop) .. 100 (full forward)
void setBeltSpeed(int percent) {
  percent = constrain(percent, -100, 100);
  belt.write(STOP_ANGLE + map(percent, -100, 100, -90, 90));
  Serial.print("belt ");
  Serial.print(percent);
  Serial.println("%");
}

void setup() {
  Serial.begin(115200);
  belt.attach(BELT_PIN);
  setBeltSpeed(0);
}

void loop() {
  int steps[] = {0, 20, 40, 0, -20, -40};
  for (int s : steps) {
    setBeltSpeed(s);
    delay(2500);
  }
}
