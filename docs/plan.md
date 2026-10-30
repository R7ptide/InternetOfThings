# Smart Factory Digital Twin: Color-Sorting Conveyor – Project Plan (IoT, UMinho MIA+MCS 2026/27)

## Concept

A miniature conveyor belt. Colored objects are placed on the belt, detected, their color is read, and a servo diverter pushes each one into the correct bin. The **digital twin** mirrors the live state of the line (belt, items, diverter, bins), keeps history, and runs what-if simulations (belt speed, diverter timing vs. throughput and mis-sort rate).

## Architecture (4 layers, matching the course)

| Layer                                         | Component                                                                | Role                                                                                                                                                                                                                                            |
| --------------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Perception – Line controller                  | Arduino UNO R4 WiFi + IO Expansion Shield V7                             | Drives belt (130 DC motor via PWM, or stepper + ULN2003), servo diverter (9g), relay/e-stop; reads ultrasonic/IR sensor (item present) and I2C wattmeter SEN0291 (power per item); LCD/OLED local status; publishes over Wi-Fi                  |
| Perception – Color station (TinyML kit) - ??  | Arduino Nano 33 BLE Sense Rev2 above the belt                            | Reads color/proximity (on-board APDS-9960; optionally TCS34725 SEN0212 as a better sensor, range 3-10 mm so it sits right above the belt); runs a TensorFlow Lite Micro classifier (red/green/blue/other); sends `{color, confidence}` over BLE |
| Gateway                                       | Raspberry Pi 5                                                           | Mosquitto MQTT broker, BLE bridge (Python/bleak), Node-RED or Python normalization to JSON, local buffering, sort-decision logic (color → bin → servo command), e-stop rule                                                                     |
| Cloud (simulated on a laptop, Docker Compose) | InfluxDB + Grafana, twin service (FastAPI/Node), web twin (SVG/Three.js) | Time-series storage, twin state model, history replay, what-if simulation, dashboards and alerts                                                                                                                                                |

Sorting flow: ultrasonic detects item → belt stops/slows under the color station (or the item passes it at known speed) →
Nano classifies → BLE → Pi → decision → MQTT command to UNO → servo diverts at the right moment (delay computed from belt
speed) → item lands in bin → twin updates.

Protocols: MQTT (QoS 1) for telemetry/commands, BLE GATT for Nano→Pi, HTTP/WebSocket to the twin UI.
Topic scheme: `factory/sorter1/<station>/<sensor>` (telemetry), `factory/sorter1/<station>/cmd` (actuation), `factory/sorter1/twin/state`.
Message format: JSON `{ts, device, sensor, value, unit, seq}`; classification event `{ts, item_id, color, confidence, bin}`.
Twin state is one JSON document per asset (belt, diverter, each item, each bin).
Security (assignment asks for it): MQTT username/password + TLS on Mosquitto, per-device credentials, no secrets in
sketches (`secrets.h`, gitignored), command validation on the Pi (only allowed actuator commands), basic threat table in
the report (spoofed color reading, rogue command to the servo/belt, replay).

## Roles

1. **Edge/hardware:** belt build, wiring, UNO R4 firmware (belt, servo, ultrasonic, wattmeter), Nano color sensing and TinyML (data collection, training, deployment).
2. **Gateway/cloud:** Pi setup, MQTT broker + TLS, BLE bridge, sort-decision logic, InfluxDB/Grafana, Docker Compose, security.
3. **Twin/UI + report lead:** twin state model, web visualization, what-if simulator, test plan, report writing.
   Everyone writes their report section as they go.

## Evaluation experiments

- **Sorting accuracy:** N items per color (e.g. 50 each), confusion matrix of true vs. bin; mis-sort rate under normal vs. dim/bright light.
- **TinyML vs. baseline:** accuracy/F1 on held-out data, inference time, RAM/flash use, compared with a fixed-threshold classifier.
- **Latency:** item detected → classified → servo action → twin update, over many samples; also sensor → twin end to end.
- **Throughput:** items per minute at 3 belt speeds; compare with the twin's what-if prediction (twin fidelity).
- **Resilience:** Wi-Fi/BLE interruption and recovery, packet loss, what happens to in-flight items.
- **Power:** wattmeter readings per belt speed, energy per sorted item.
- **Security:** unauthenticated publish rejected; TLS visible in a traffic capture.

## Risks and mitigations

- **Color misreads from ambient light:** shaded tunnel over the sensor, calibrate with a white/black reference, include light-level features in the model, collect data under varied light.
- **Servo timing / mechanical inconsistency:** stop-and-read at the color station first, then move to free-running belt only if time allows; log belt speed to compute the delay.
- **BLE flakiness:** fall back to USB serial for Nano→Pi; keep BLE as the documented alternative.
- **TinyML data quality:** record data in W3, not W5; budget a second round. A threshold baseline guarantees a working demo.
- **Hardware conflicts (shared kits):** reserve boards early.
- **Scope creep (twin visuals):** 2D SVG first, Three.js only after the closed loop works.
