"""Append scan results to a CSV history file."""

import csv
from datetime import datetime
from pathlib import Path

FIELDS = ["timestamp", "ip", "mac", "name", "latency_ms", "open_ports", "warnings"]


def log_scan(devices: list[dict], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    timestamp = datetime.now().isoformat(timespec="seconds")

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        for d in devices:
            writer.writerow({
                "timestamp": timestamp,
                "ip": d["ip"],
                "mac": d["mac"],
                "name": d.get("name", ""),
                "latency_ms": d["latency_ms"],
                "open_ports": " ".join(str(p) for p in d.get("open_ports", [])),
                "warnings": "; ".join(d.get("warnings", [])),
            })
