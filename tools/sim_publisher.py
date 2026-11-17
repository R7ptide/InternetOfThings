import json
import os
import queue
import random
import time

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
ROOT = "factory/sorter1"
COLORS = ["red", "green", "blue"]
BINS = ["red", "green", "blue", "unknown"]
ERROR_RATE = 0.15  # chance that one reading is wrong
READINGS = 4

commands = queue.Queue()
seq = 0


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(f"{ROOT}/line/cmd", qos=1)


def on_message(client, userdata, msg):
    try:
        commands.put(json.loads(msg.payload))
    except ValueError:
        pass


def publish(client, topic, payload, device):
    global seq
    seq += 1
    payload = {"device": device, "seq": seq, **payload}
    client.publish(f"{ROOT}/{topic}", json.dumps(payload), qos=1)


def wait_for(predicate, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            cmd = commands.get(timeout=0.2)
        except queue.Empty:
            continue
        if predicate(cmd):
            return cmd
    return None


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_start()

    counts = {b: 0 for b in BINS}
    item_id = 0
    print("waiting for the gateway to start the belt...")
    wait_for(lambda c: c.get("action") == "belt" and c.get("state") == "run", 3600)

    while True:
        time.sleep(random.uniform(1.5, 3))  # an item travels to the sensor
        item_id += 1
        true_color = random.choice(COLORS)
        publish(client, "line/item", {"item_id": item_id, "event": "detected"}, "uno1")
        print(f"item {item_id} ({true_color}) detected")

        for _ in range(READINGS):
            time.sleep(0.25)
            color = random.choice([c for c in COLORS if c != true_color]) \
                if random.random() < ERROR_RATE else true_color
            publish(client, "color/classification",
                    {"color": color, "confidence": round(random.uniform(0.7, 0.99), 2), "model": "sim"}, "nano1")

        divert = wait_for(lambda c: c.get("action") == "divert" and c.get("item_id") == item_id, 5)
        if divert is None:
            print(f"item {item_id}: no divert command (is gateway/sorter.py running?)")
            continue
        time.sleep(divert.get("delay_ms", 0) / 1000)
        counts[divert["bin"]] += 1
        publish(client, "line/bin", {"item_id": item_id, "bin": divert["bin"], "count": counts[divert["bin"]]}, "uno1")
        print(f"item {item_id}: {true_color} -> bin {divert['bin']}")


if __name__ == "__main__":
    main()
