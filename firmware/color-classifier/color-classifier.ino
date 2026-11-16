// Nano 33 BLE Sense (Rev2): classify the color on the board with the logistic regression
// exported by ml/export_c.py (color_model.h), and print one JSON line per new reading.
//
// Libraries: "Arduino_APDS9960". Regenerate color_model.h after collecting new data:
//   python ml/export_c.py
// Output matches docs/mqtt-spec.md (color/classification), without item_id/ts: the gateway adds those.
// Next step: send the same JSON over BLE to the Pi instead of (or as well as) Serial.
#include <Arduino_APDS9960.h>
#include "color_model.h"

// Below this "clear" reading there is no object in front of the sensor (calibrate: read the
// serial output of color-station.ino with the belt empty and set this just above that value).
const int MIN_CLEAR = 10;

int lastR = -1, lastG = -1, lastB = -1, lastClear = -1;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}

  if (!APDS.begin()) {
    Serial.println("APDS-9960 init failed");
    while (true) {}
  }
}

void loop() {
  if (!APDS.colorAvailable()) {
    delay(5);
    return;
  }

  int r, g, b, c;
  APDS.readColor(r, g, b, c);

  // the sensor updates more slowly than we poll: only act on new readings
  if (r == lastR && g == lastG && b == lastB && c == lastClear) return;
  lastR = r; lastG = g; lastB = b; lastClear = c;

  if (c < MIN_CLEAR) return;  // nothing in front of the sensor

  float confidence = 0.0f;
  int cls = classify_color(r, g, b, c, &confidence);
  if (cls < 0) return;

  Serial.print("{\"device\":\"nano1\",\"color\":\"");
  Serial.print(COLOR_LABELS[cls]);
  Serial.print("\",\"confidence\":");
  Serial.print(confidence, 2);
  Serial.print(",\"model\":\"logreg\",\"r\":");
  Serial.print(r);
  Serial.print(",\"g\":");
  Serial.print(g);
  Serial.print(",\"b\":");
  Serial.print(b);
  Serial.print(",\"clear\":");
  Serial.print(c);
  Serial.println("}");
}
