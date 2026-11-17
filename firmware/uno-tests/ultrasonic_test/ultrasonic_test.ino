const int SENSOR_PIN = A0;
const float MAX_RANGE_CM = 520.0;
const int ADC_MAX = 1023;  // 10-bit ADC

void setup() {
  Serial.begin(115200);
  analogReadResolution(10);  // the R4 defaults to 10 bits
}

void loop() {
  // average a few samples to smooth the analog noise
  long sum = 0;
  for (int i = 0; i < 8; i++) {
    sum += analogRead(SENSOR_PIN);
    delay(2);
  }
  float raw = sum / 8.0;
  float cm = raw * MAX_RANGE_CM / ADC_MAX;

  Serial.print("raw ");
  Serial.print(raw, 0);
  Serial.print("  ->  ");
  Serial.print(cm, 1);
  Serial.println(" cm");
  delay(200);
}
