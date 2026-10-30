import json
import os

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
ROOT = "factory/sorter1"

MIN_CONFIDENCE = 0.6
BINS = {"red", "green", "blue"}  # anything else goes to "unknown" 
DIVERT_DELAY_MS = 800  # TODO: compute from belt speed and distance to the diverter


def on_connect(client, userdata, flags, reason_code, properties):
    print("connected to broker:", reason_code)
    client.subscribe(f"{ROOT}/color/classification", qos=1)


def on_message(client, userdata, msg):
    try:
        event = json.loads(msg.payload)
        color = event["color"]
        confidence = float(event.get("confidence", 0))
        item_id = event["item_id"]
    except (ValueError, KeyError) as exc:
        print("ignoring bad message:", msg.payload, exc)
        return

    target = color if color in BINS and confidence >= MIN_CONFIDENCE else "unknown"
    cmd = {"action": "divert", "item_id": item_id, "bin": target, "delay_ms": DIVERT_DELAY_MS}
    client.publish(f"{ROOT}/line/cmd", json.dumps(cmd), qos=1)
    print(f"item {item_id}: {color} ({confidence:.2f}) -> bin {target}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()
