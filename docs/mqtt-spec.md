# MQTT spec (v0)

Root: `factory/sorter1/`. Payloads are JSON. Timestamps `ts` are Unix ms from the gateway/cloud clock when possible
(devices without a clock send `uptime_ms` and the gateway adds `ts`). `seq` is a per-device counter to detect loss.

## Telemetry (device -> broker), QoS 0 for streams, QoS 1 for events
| Topic | Payload |
|---|---|
| `factory/sorter1/line/ultrasonic` | `{"device":"uno1","seq":12,"distance_cm":14.2}` |
| `factory/sorter1/line/item` | `{"device":"uno1","seq":13,"item_id":7,"event":"detected"}` |
| `factory/sorter1/line/power` | `{"device":"uno1","seq":14,"voltage_v":5.0,"current_ma":210,"power_mw":1050}` |
| `factory/sorter1/line/bin` | `{"device":"uno1","seq":15,"item_id":7,"bin":"red","count":3}` |
| `factory/sorter1/line/status` | `{"device":"uno1","belt":"running","speed_pct":60,"diverter_deg":90}` (retained) |
| `factory/sorter1/color/raw` | `{"device":"nano1","seq":3,"r":210,"g":40,"b":35,"clear":300}` |
| `factory/sorter1/color/classification` | `{"device":"nano1","seq":4,"item_id":7,"color":"red","confidence":0.93,"model":"threshold"}` |

`color` in {`red`,`green`,`blue`,`unknown`}. `model` in {`threshold`,`tinyml`} so both can be compared.

## Commands (gateway/cloud -> device), QoS 1
| Topic | Payload |
|---|---|
| `factory/sorter1/line/cmd` | `{"action":"divert","item_id":7,"bin":"red","delay_ms":800}` |
| | `{"action":"belt","state":"stop"}` or `{"action":"belt","state":"run","speed_pct":60}` |
| | `{"action":"estop"}` |

Allowed actions are validated by the gateway before forwarding. Devices ignore unknown actions.

## Twin state (cloud -> UI), retained
`factory/sorter1/twin/state`:
```json
{"ts":1730000000000,"belt":{"state":"running","speed_pct":60},
 "diverter":{"angle_deg":90},
 "items":[{"id":7,"color":"red","position":"color_station"}],
 "bins":{"red":3,"green":1,"blue":2,"unknown":0}}
```

## Conventions
- Lowercase topics, no spaces, device ids `uno1`, `nano1`.
- Bins: `red`, `green`, `blue`, `unknown` (unknown goes to the reject bin).
- Security (later): per-device MQTT user + TLS; for now the dev broker allows anonymous.
