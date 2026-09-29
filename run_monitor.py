"""Network Health Monitor - main entry point.

Usage:
    py run_monitor.py           # scan the subnet in config.json
    py run_monitor.py --demo    # render the dashboard from sample data (no scan)
"""

import json
import sys
from pathlib import Path

from netmon import alerts, dashboard, discover, logger, portscan

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
CSV_PATH = ROOT / "data" / "history.csv"
DASHBOARD_PATH = ROOT / "dashboard.html"

DEMO_DEVICES = [
    {"ip": "192.168.1.1", "mac": "10-20-30-40-50-60", "name": "Router",
     "latency_ms": 2, "open_ports": [80, 443], "warnings": [], "is_unknown": False},
    {"ip": "192.168.1.42", "mac": "AA-BB-CC-DD-EE-FF", "name": "My Laptop",
     "latency_ms": 1, "open_ports": [], "warnings": [], "is_unknown": False},
    {"ip": "192.168.1.77", "mac": "DE-AD-BE-EF-00-01", "name": None,
     "latency_ms": 14, "open_ports": [23, 445],
     "warnings": ["Port 23 open: Telnet (unencrypted remote shell)",
                  "Port 445 open: SMB (common ransomware/lateral-movement target)"],
     "is_unknown": True},
]


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    if "--demo" in sys.argv:
        devices = DEMO_DEVICES
        print("Demo mode: using sample data (no network scan)")
    else:
        print(f"Scanning {config['subnet']}.1-254 ...")
        devices = discover.sweep(config["subnet"])
        print(f"Found {len(devices)} live device(s). Checking ports ...")

        known = {mac.upper(): name for mac, name in config["known_devices"].items()}
        for d in devices:
            d["open_ports"] = portscan.scan_device(d["ip"], config["ports"])
            d["warnings"] = portscan.flag_risky(d["open_ports"], config["risky_ports"])
            d["name"] = known.get(d["mac"])
            d["is_unknown"] = d["mac"] not in known

    logger.log_scan(devices, CSV_PATH)
    dashboard.render(devices, DASHBOARD_PATH)
    print(f"Dashboard written to {DASHBOARD_PATH}")
    print(f"History appended to {CSV_PATH}")

    body = alerts.build_alert_body(devices)
    if body:
        print("\nALERTS:\n" + body)
        if config["email"].get("enabled"):
            alerts.send_alert(body, config["email"])
            print("Alert email sent.")
        else:
            print("(Email alerts disabled in config.json)")


if __name__ == "__main__":
    main()
