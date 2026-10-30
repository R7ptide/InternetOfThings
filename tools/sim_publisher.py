import json
import os
import random
import time

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
ROOT = "factory/sorter1"
COLORS = ["red", "green", "blue", "unknown"]
WEIGHTS = [0.3, 0.3, 0.3, 0.1]


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER, PORT)
    client.loop_start()

    item_id = 0
    seq = 0
    while True:
        item_id += 1
        seq += 1
        client.publish(f"{ROOT}/line/item",
                       json.dumps({"device": "uno1", "seq": seq, "item_id": item_id, "event": "detected"}), qos=1)
        time.sleep(0.5)

        color = random.choices(COLORS, WEIGHTS)[0]
        confidence = round(random.uniform(0.5, 0.99), 2)
        client.publish(f"{ROOT}/color/classification",
                       json.dumps({"device": "nano1", "seq": seq, "item_id": item_id, "color": color,
                                   "confidence": confidence, "model": "threshold"}), qos=1)
        client.publish(f"{ROOT}/line/ultrasonic",
                       json.dumps({"device": "uno1", "seq": seq, "distance_cm": round(random.uniform(4, 30), 1)}))
        print(f"item {item_id}: {color} ({confidence})")
        time.sleep(random.uniform(2, 4))


if __name__ == "__main__":
    main()
