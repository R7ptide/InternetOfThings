const int TRIG_PIN = 7;
const int ECHO_PIN = 8;

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long us = pulseIn(ECHO_PIN, HIGH, 30000);  // 30 ms timeout
  if (us == 0) {
    Serial.println("no echo (nothing in range, or TRIG/ECHO wired wrong)");
  } else {
    Serial.print(us / 58.0, 1);
    Serial.println(" cm");
  }
  delay(200);
}
