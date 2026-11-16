"""Log color samples from the Nano (color-station.ino) to a labeled CSV, and summarize them.

Collect:   python tools/log_colors.py --label red --samples 30
Summary:   python tools/log_colors.py --summary

Close the Arduino Serial Monitor first: only one program can use the port at a time.
Samples are appended to ml/data/colors.csv with columns:
  ts,label,r,g,b,clear,proximity,r_share,g_share,b_share
"""
import argparse
import csv
import os
import sys
import time
from collections import defaultdict
from statistics import mean, pstdev

import serial
from serial.tools import list_ports

DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "ml", "data", "colors.csv")
FIELDS = ["ts", "label", "r", "g", "b", "clear", "proximity", "r_share", "g_share", "b_share"]


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
    parts = line.strip().split(",")
    if len(parts) != 5:
        return None
    try:
        return [int(x) for x in parts]
    except ValueError:
        return None  # header or partial line


def collect(args):
    port = args.port or find_port()
    if not port:
        sys.exit("No board found. Plug it in, or pass --port (e.g. /dev/ttyACM0 or COM3).")

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    new_file = not os.path.exists(out)

    print(f"port {port}, label '{args.label}', {args.samples} samples -> {out}")
    print("Hold the object in position. Ctrl+C to stop early.")

    saved = 0
    last = None  # the sensor updates slower than the board prints, so skip repeated readings
    with serial.Serial(port, args.baud, timeout=2) as ser, open(out, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(FIELDS)
        ser.reset_input_buffer()
        try:
            while saved < args.samples:
                values = parse_line(ser.readline().decode(errors="ignore"))
                if values is None:
                    continue
                r, g, b, clear, prox = values
                total = r + g + b
                if total == 0 or (r, g, b, clear) == last:
                    continue
                last = (r, g, b, clear)
                shares = (r / total, g / total, b / total)
                writer.writerow([int(time.time() * 1000), args.label, r, g, b, clear, prox,
                                 f"{shares[0]:.3f}", f"{shares[1]:.3f}", f"{shares[2]:.3f}"])
                f.flush()
                saved += 1
                print(f"{saved:3d}/{args.samples}  r={r:4d} g={g:4d} b={b:4d} clear={clear:4d}"
                      f"  shares r={shares[0]:.2f} g={shares[1]:.2f} b={shares[2]:.2f}")
        except KeyboardInterrupt:
            print("\nstopped early")
    print(f"saved {saved} samples")


def summary(args):
    path = os.path.abspath(args.out)
    if not os.path.exists(path):
        sys.exit(f"{path} not found. Collect some samples first.")

    by_label = defaultdict(list)
    with open(path, "r", newline="") as f:
        for row in csv.DictReader(f):
            by_label[row["label"]].append(
                (float(row["r_share"]), float(row["g_share"]), float(row["b_share"]), int(row["clear"])))

    print(f"{'label':8} {'n':>4}  {'r_share':>14} {'g_share':>14} {'b_share':>14}  {'clear':>7}")
    means = {}
    for label, rows in sorted(by_label.items()):
        cols = list(zip(*rows))
        means[label] = [mean(c) for c in cols[:3]]
        cells = [f"{mean(c):.3f}±{pstdev(c):.3f}" for c in cols[:3]]
        print(f"{label:8} {len(rows):4d}  {cells[0]:>14} {cells[1]:>14} {cells[2]:>14}  {mean(cols[3]):7.0f}")

    labels = sorted(means)
    if len(labels) > 1:
        print("\nDistance between label means (share space). Bigger is easier to separate; compare with the ± above:")
        for i, a in enumerate(labels):
            for b in labels[i + 1:]:
                d = sum((x - y) ** 2 for x, y in zip(means[a], means[b])) ** 0.5
                print(f"  {a} vs {b}: {d:.3f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", help="color label for this run, e.g. red")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--port", help="serial port; auto-detected if omitted")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--summary", action="store_true", help="print per-label stats from the CSV and exit")
    args = parser.parse_args()

    if args.summary:
        summary(args)
    elif args.label:
        collect(args)
    else:
        parser.error("give --label to collect, or --summary")


if __name__ == "__main__":
    main()
