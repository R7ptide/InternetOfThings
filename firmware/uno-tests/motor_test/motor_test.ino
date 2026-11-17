const int MOTOR_PIN = 5;

void setSpeed(int percent) {
  analogWrite(MOTOR_PIN, map(percent, 0, 100, 0, 255));
  Serial.print("speed ");
  Serial.print(percent);
  Serial.println("%");
}

void setup() {
  Serial.begin(115200);
  pinMode(MOTOR_PIN, OUTPUT);
  setSpeed(0);
}

void loop() {
  for (int p = 0; p <= 100; p += 20) { setSpeed(p); delay(1000); }
  delay(2000);
  for (int p = 100; p >= 0; p -= 20) { setSpeed(p); delay(1000); }
  delay(3000);
}
