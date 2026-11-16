// Nano 33 BLE Sense (Rev2): read color from the on-board APDS-9960 and print over serial.
// Library: "Arduino_APDS9960" (Library Manager). Board: Arduino Mbed OS Nano Boards.
// Goal for the checkpoint: see distinct RGB values for red / green / blue objects.
// Next: log samples as CSV for training, then BLE + TinyML classifier.
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
  if (APDS.proximityAvailable()) proximity = APDS.readProximity();  // 0 = close, 255 = far

  // CSV: easy to paste into a spreadsheet or save for the ML dataset
  Serial.print(r); Serial.print(',');
  Serial.print(g); Serial.print(',');
  Serial.print(b); Serial.print(',');
  Serial.print(c); Serial.print(',');
  Serial.println(proximity);

  delay(200);
}
