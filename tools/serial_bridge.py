import argparse
import json
import os
import sys
import time

import paho.mqtt.client as mqtt
import serial
from serial.tools import list_ports

ROOT = "factory/sorter1"
TOPIC = f"{ROOT}/color/classification"


def find_port():
    ports = list(list_ports.comports())
    for p in ports:
        text = f"{p.description} {p.manufacturer} {p.device}".lower()
        if p.vid == 0x2341 or "arduino" in text or "nano" in text:
            return p.device
    for p in ports:
        if "ttyACM" in p.device or "usbmodem" in p.device:
            return p.device
    return None


def parse_line(line):
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        event = json.loads(line)
        event["color"]
        float(event["confidence"])
    except (ValueError, KeyError, TypeError):
        return None
    return event


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", help="serial port; auto-detected if omitted")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--host", default=os.environ.get("MQTT_HOST", "localhost"))
    parser.add_argument("--mqtt-port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")))
    args = parser.parse_args()

    port = args.port or find_port()
    if not port:
        sys.exit("No board found. Plug the Nano in, or pass --port (e.g. /dev/ttyACM0 or COM3).")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(args.host, args.mqtt_port)
    client.loop_start()
    print(f"bridging {port} -> mqtt {args.host}:{args.mqtt_port} {TOPIC}")

    sent = 0
    try:
        with serial.Serial(port, args.baud, timeout=2) as ser:
            ser.reset_input_buffer()
            while True:
                event = parse_line(ser.readline().decode(errors="ignore"))
                if event is None:
                    continue
                event["ts"] = int(time.time() * 1000)
                client.publish(TOPIC, json.dumps(event), qos=1)
                sent += 1
                print(f"{sent:4d}  {event['color']} ({float(event['confidence']):.2f})")
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()


if __name__ == "__main__":
    main()
