import json
import os
import threading
import time
from collections import defaultdict

ROOT = "factory/sorter1"

MIN_CONFIDENCE = 0.6      # below this the item goes to the reject bin
BINS = ("red", "green", "blue")
MIN_SAMPLES = 3           # classifications to collect before deciding
COLOR_TIMEOUT_S = 2.0     # decide with whatever we have after this long (none -> unknown)
BELT_SPEED_PCT = 30
TRAVEL_DELAY_MS = 1500    # color sensor -> diverter arm
DIVERT_MARGIN_S = 3.0     # extra wait for the line/bin confirmation before giving up
TICK_S = 0.05             # how often timeouts are checked

IDLE, COLLECTING, DIVERTING = "idle", "collecting", "diverting"


class Sequencer:
    def __init__(self, publish, clock=time.monotonic, log=print):
        self.publish = publish  # publish(topic, dict)
        self.clock = clock
        self.log = log
        self.lock = threading.Lock()
        self.state = IDLE
        self.item_id = None
        self.samples = []
        self.deadline = 0.0

    # --- helpers -------------------------------------------------------------------------
    def _cmd(self, payload):
        self.publish(f"{ROOT}/line/cmd", payload)

    def start_belt(self):
        self._cmd({"action": "belt", "state": "run", "speed_pct": BELT_SPEED_PCT})

    def _set(self, state, timeout=None):
        self.state = state
        self.deadline = self.clock() + timeout if timeout is not None else 0.0

    def decide(self):
        """Confidence-weighted vote over the collected samples -> (bin, confidence)."""
        if not self.samples:
            return "unknown", 0.0
        votes = defaultdict(float)
        for color, confidence in self.samples:
            votes[color] += confidence
        winner = max(votes, key=votes.get)
        confidence = votes[winner] / len(self.samples)  # disagreement lowers it
        if winner not in BINS or confidence < MIN_CONFIDENCE:
            return "unknown", confidence
        return winner, confidence

    def _finish_reading(self):
        bin_name, confidence = self.decide()
        self.log(f"item {self.item_id}: {len(self.samples)} samples -> {bin_name} ({confidence:.2f})")
        self.start_belt()
        self._cmd({"action": "divert", "item_id": self.item_id, "bin": bin_name, "delay_ms": TRAVEL_DELAY_MS})
        self._set(DIVERTING, TRAVEL_DELAY_MS / 1000 + DIVERT_MARGIN_S)

    # --- inputs ----------------------------------------------------------------------------
    def on_message(self, topic, payload):
        try:
            data = json.loads(payload)
        except ValueError:
            self.log(f"ignoring bad JSON on {topic}")
            return
        with self.lock:
            if topic.endswith("/line/item"):
                self._on_item(data)
            elif topic.endswith("/color/classification"):
                self._on_color(data)
            elif topic.endswith("/line/bin"):
                self._on_bin(data)

    def _on_item(self, data):
        if data.get("event") != "detected":
            return
        if self.state != IDLE:
            self.log(f"item {data.get('item_id')} detected while busy ({self.state}), ignored")
            return
        self.item_id = data.get("item_id")
        self.samples = []
        self._cmd({"action": "belt", "state": "stop"})  # the UNO already stops locally; this is a backup
        self._set(COLLECTING, COLOR_TIMEOUT_S)
        self.log(f"item {self.item_id} detected, reading color")

    def _on_color(self, data):
        if self.state != COLLECTING:
            return  # stale reading, nothing is waiting for it
        try:
            self.samples.append((data["color"], float(data["confidence"])))
        except (KeyError, ValueError, TypeError):
            return
        if len(self.samples) >= MIN_SAMPLES:
            self._finish_reading()

    def _on_bin(self, data):
        if self.state == DIVERTING and data.get("item_id") == self.item_id:
            self.log(f"item {self.item_id} sorted into {data.get('bin')} (count {data.get('count')})")
            self._set(IDLE)

    def tick(self):
        """Call regularly: handles timeouts."""
        with self.lock:
            if not self.deadline or self.clock() < self.deadline:
                return
            if self.state == COLLECTING:
                self.log(f"item {self.item_id}: color timeout")
                self._finish_reading()
            elif self.state == DIVERTING:
                self.log(f"item {self.item_id}: no bin confirmation, giving up")
                self._set(IDLE)


def main():
    import paho.mqtt.client as mqtt

    broker = os.environ.get("MQTT_HOST", "localhost")
    port = int(os.environ.get("MQTT_PORT", "1883"))

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def publish(topic, payload):
        client.publish(topic, json.dumps(payload), qos=1)

    sequencer = Sequencer(publish)

    def on_connect(client, userdata, flags, reason_code, properties):
        print("connected to broker:", reason_code)
        for topic in ("line/item", "color/classification", "line/bin"):
            client.subscribe(f"{ROOT}/{topic}", qos=1)
        sequencer.start_belt()

    client.on_connect = on_connect
    client.on_message = lambda c, u, msg: sequencer.on_message(msg.topic, msg.payload)
    client.connect(broker, port)
    client.loop_start()

    stop = threading.Event()
    try:
        while not stop.wait(TICK_S):  # paces the loop; stop.set() would end it
            sequencer.tick()
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()


if __name__ == "__main__":
    main()
