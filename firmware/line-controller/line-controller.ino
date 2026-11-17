#include <WiFiS3.h>
#include <ArduinoMqttClient.h>
#include <ArduinoJson.h>
#include <Servo.h>
#include "secrets.h"

const int DISTANCE_PIN = A0;
const int DIVERTER_PIN = 9;
const int BELT_PIN = 6;

// diverter angles
const int ANGLE_NEUTRAL = 90;
const int ANGLE_RED = 45;
const int ANGLE_GREEN = 90;
const int ANGLE_BLUE = 135;
const int ANGLE_UNKNOWN = 15;
const unsigned long DIVERT_HOLD_MS = 700;

const int BELT_STOP_ANGLE = 90;  // continuous servo: 90 = stop
const int BELT_DEFAULT_PCT = 30;

const bool STOP_BELT_ON_ITEM = true;          // stop immediately, without waiting for the gateway
const float ITEM_DROP_CM = 3.0;              // item = distance this much closer than the empty belt
const unsigned long ITEM_CLEAR_MS = 400;      // distance must stay normal this long to end an item
const unsigned long TELEMETRY_MS = 500;
const unsigned long RECONNECT_MS = 3000;

const char ROOT[] = "factory/sorter1/line/";
const char DEVICE[] = "uno1";

WiFiClient wifi;
MqttClient mqtt(wifi);
Servo diverter;
Servo belt;

unsigned long seq = 0;
int beltPct = 0;
float baselineCm = 0;
bool itemPresent = false;
int lastItemId = 0;
unsigned long clearSince = 0;
unsigned long lastTelemetry = 0;
unsigned long lastReconnect = 0;
int binCounts[4] = {0, 0, 0, 0};  // red, green, blue, unknown

struct Divert {
  bool used;
  unsigned long at;
  int itemId;
  int bin;  // 0 red, 1 green, 2 blue, 3 unknown
};
Divert pending[8];
unsigned long returnAt = 0;  // when the arm goes back to neutral (0 = not moving)

const char* const BIN_NAMES[4] = {"red", "green", "blue", "unknown"};
const int BIN_ANGLES[4] = {ANGLE_RED, ANGLE_GREEN, ANGLE_BLUE, ANGLE_UNKNOWN};

int binIndex(const char* name) {
  for (int i = 0; i < 3; i++) if (strcmp(name, BIN_NAMES[i]) == 0) return i;
  return 3;
}

float readDistanceCm(int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(DISTANCE_PIN);
    delay(2);
  }
  return (sum / (float)samples) * 520.0 / 1023.0;  // distance = Vout / Vin * 520 cm (5 V, 10-bit ADC)
}

void calibrate() {
  baselineCm = readDistanceCm(32);
  Serial.print("empty-belt distance: ");
  Serial.print(baselineCm, 1);
  Serial.println(" cm");
}

void publish(const char* topic, JsonDocument& doc, bool retain = false) {
  if (!mqtt.connected()) return;
  doc["device"] = DEVICE;
  doc["seq"] = seq++;
  char full[64];
  snprintf(full, sizeof(full), "%s%s", ROOT, topic);
  mqtt.beginMessage(full, retain, 0);
  serializeJson(doc, mqtt);
  mqtt.endMessage();
}

void publishStatus() {
  JsonDocument doc;
  doc["belt"] = beltPct == 0 ? "stopped" : "running";
  doc["speed_pct"] = beltPct;
  doc["diverter_deg"] = diverter.read();
  publish("status", doc, true);
}

void setBelt(int pct) {
  beltPct = constrain(pct, -100, 100);
  belt.write(BELT_STOP_ANGLE + map(beltPct, -100, 100, -90, 90));
  publishStatus();
}

void scheduleDivert(int itemId, int bin, unsigned long delayMs) {
  for (auto& d : pending) {
    if (!d.used) {
      d = {true, millis() + delayMs, itemId, bin};
      return;
    }
  }
  Serial.println("divert queue full, command dropped");
}

void runDiverts() {
  unsigned long now = millis();
  if (returnAt && now >= returnAt) {
    diverter.write(ANGLE_NEUTRAL);
    returnAt = 0;
  }
  if (returnAt) return;  // arm busy

  for (auto& d : pending) {
    if (d.used && now >= d.at) {
      d.used = false;
      diverter.write(BIN_ANGLES[d.bin]);
      returnAt = now + DIVERT_HOLD_MS;
      binCounts[d.bin]++;

      JsonDocument doc;
      doc["item_id"] = d.itemId;
      doc["bin"] = BIN_NAMES[d.bin];
      doc["count"] = binCounts[d.bin];
      publish("bin", doc);
      return;
    }
  }
}

void onCommand(int size) {
  JsonDocument doc;
  if (deserializeJson(doc, mqtt)) {
    Serial.println("bad command JSON");
    return;
  }
  const char* action = doc["action"] | "";

  if (strcmp(action, "divert") == 0) {
    scheduleDivert(doc["item_id"] | 0, binIndex(doc["bin"] | "unknown"), doc["delay_ms"] | 0);
  } else if (strcmp(action, "belt") == 0) {
    const char* state = doc["state"] | "";
    if (strcmp(state, "stop") == 0) setBelt(0);
    else if (strcmp(state, "run") == 0) setBelt(doc["speed_pct"] | BELT_DEFAULT_PCT);
  } else if (strcmp(action, "estop") == 0) {
    for (auto& d : pending) d.used = false;
    setBelt(0);
  } else if (strcmp(action, "calibrate") == 0) {
    calibrate();
  }
}

void connectWifi() {
  while (WiFi.begin(WIFI_SSID, WIFI_PASS) != WL_CONNECTED) {
    Serial.println("connecting to wifi...");
    delay(2000);
  }
  Serial.print("wifi ok, ip ");
  Serial.println(WiFi.localIP());
}

void tryConnectMqtt() {
  mqtt.setId(DEVICE);
  if (!mqtt.connect(MQTT_HOST, MQTT_PORT)) {
    Serial.println("mqtt not connected, will retry");
    return;
  }
  mqtt.onMessage(onCommand);
  char topic[64];
  snprintf(topic, sizeof(topic), "%scmd", ROOT);
  mqtt.subscribe(topic, 1);
  Serial.println("mqtt connected");
  publishStatus();
}

// the item is "present" while the distance is clearly below the empty-belt baseline.
void detectItems() {
  float d = readDistanceCm(4);
  bool close = d < baselineCm - ITEM_DROP_CM;
  unsigned long now = millis();

  if (close && !itemPresent) {
    itemPresent = true;
    lastItemId++;
    JsonDocument doc;
    doc["item_id"] = lastItemId;
    doc["event"] = "detected";
    publish("item", doc);
    Serial.print("item ");
    Serial.println(lastItemId);
    if (STOP_BELT_ON_ITEM && beltPct != 0) setBelt(0);  // stop-and-read: the gateway restarts it
  } else if (!close && itemPresent) {
    if (clearSince == 0) clearSince = now;
    if (now - clearSince > ITEM_CLEAR_MS) itemPresent = false;
  }
  if (close) clearSince = 0;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(10);
  diverter.attach(DIVERTER_PIN);
  diverter.write(ANGLE_NEUTRAL);
  belt.attach(BELT_PIN);
  setBelt(0);
  calibrate();  // keep the belt area empty when the board starts
  connectWifi();
  tryConnectMqtt();
}

void loop() {
  unsigned long now = millis();

  if (!mqtt.connected()) {
    if (now - lastReconnect > RECONNECT_MS) {
      lastReconnect = now;
      tryConnectMqtt();
    }
  } else {
    mqtt.poll();
  }

  detectItems();
  runDiverts();

  if (now - lastTelemetry > TELEMETRY_MS) {
    lastTelemetry = now;
    JsonDocument doc;
    doc["distance_cm"] = serialized(String(readDistanceCm(4), 1));
    publish("ultrasonic", doc);
  }
}
