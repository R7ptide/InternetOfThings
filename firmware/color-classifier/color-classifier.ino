#include <Arduino_APDS9960.h>
#include "color_model.h"

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

  // the sensor updates more slowly than we poll
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
