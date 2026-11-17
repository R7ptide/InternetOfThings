#include <Arduino_APDS9960.h>

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}

  if (!APDS.begin()) {
    Serial.println("APDS-9960 init failed");
    while (true) {}
  }
  Serial.println("r,g,b,clear,proximity");
}

void loop() {
  // wait until a color sample is available
  while (!APDS.colorAvailable()) delay(5);

  int r, g, b, c;
  APDS.readColor(r, g, b, c);

  int proximity = -1;
  if (APDS.proximityAvailable()) proximity = APDS.readProximity();  // 0 -> close, 255 -> far

  Serial.print(r); Serial.print(',');
  Serial.print(g); Serial.print(',');
  Serial.print(b); Serial.print(',');
  Serial.print(c); Serial.print(',');
  Serial.println(proximity);

  delay(200);
}
