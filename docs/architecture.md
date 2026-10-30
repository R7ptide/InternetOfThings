# Architecture

```mermaid
flowchart LR
  subgraph Edge["Perception layer"]
    N["Nano 33 BLE Sense<br/>color sensor + TinyML"]
    U["UNO R4 WiFi<br/>belt motor, servo, ultrasonic, wattmeter"]
  end
  subgraph GW["Gateway - Raspberry Pi 5"]
    B["BLE bridge"]
    M["Mosquitto MQTT"]
    S["sorter.py<br/>color -> bin -> command"]
  end
  subgraph Cloud["Cloud (laptop, Docker)"]
    I[("InfluxDB")]
    G["Grafana"]
    T["Twin service + web UI"]
  end
  N -- BLE --> B --> M
  U -- "Wi-Fi / MQTT" --> M
  M <--> S
  S -- "cmd" --> M --> U
  M --> I --> G
  M --> T
```

## Flow of one item
1. Ultrasonic sensor (UNO) sees an item: `line/ultrasonic` / `line/item` event.
2. Item reaches the color station; Nano reads RGB, classifies it, sends `{color, confidence}` over BLE.
3. BLE bridge on the Pi republishes it to MQTT as `color/classification`.
4. `sorter.py` maps color to bin and publishes `line/cmd` `{action: "divert", bin, delay_ms}`.
5. UNO moves the servo after `delay_ms`; item falls in the bin; UNO publishes `line/bin` count event.
6. Twin service updates the item and bin state; Grafana shows history.

## Layers (course mapping)
- Perception and communication: Nano, UNO, BLE, Wi-Fi
- Processing: gateway (sort logic), TinyML on the edge, cloud (storage, twin)
- Application: web twin and Grafana dashboards

## To decide this week
- Stop-and-read vs. free-running belt (start with stop-and-read)
- Which color sensor (Nano APDS-9960 first, TCS34725 if readings are noisy)
- Belt motor: 130 DC motor (PWM) vs. stepper
