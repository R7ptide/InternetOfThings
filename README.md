# Color-Sorting Conveyor with Digital Twin (IoT, UMinho 2026/27)

A miniature conveyor belt that sorts colored objects into bins, with a digital twin that mirrors the line live.

- Plan, timeline and experiments: [docs/plan.md](docs/plan.md)
- Architecture diagram and data flow: [docs/architecture.md](docs/architecture.md)
- MQTT topics and JSON messages: [docs/mqtt-spec.md](docs/mqtt-spec.md)

## Layout

```
docs/                     assignment PDFs, plan, architecture, MQTT spec
gateway/                  Raspberry Pi: sort logic (color -> bin -> command)
cloud/                    docker-compose: Mosquitto, InfluxDB, Grafana
tools/                    simulator to develop without hardware
```

## Quick start (no hardware needed)

```bash
# 1. start the cloud stack (MQTT broker, InfluxDB, Grafana)
cd cloud && docker compose up -d

# 2. install python deps
pip install -r gateway/requirements.txt

# 3. run the sort logic and the fake device in two terminals
python gateway/sorter.py
python tools/sim_publisher.py

# 4. watch everything
mosquitto_sub -h localhost -t 'factory/#' -v
```

Grafana: http://localhost:3000 (admin / admin), InfluxDB: http://localhost:8086.
