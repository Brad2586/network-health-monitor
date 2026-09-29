# Network Health Monitor

A Python tool that discovers devices on your local network, monitors their health
(latency, availability, open ports), logs results over time, and renders an HTML
status dashboard with alerts for outages and unknown devices.

Built with Windows in mind (uses `ping` and `arp` under the hood), standard library
only — no packages required for v1.

## Features

- **Device discovery** — threaded ping sweep of your subnet + ARP table parsing
  to find live hosts and MAC addresses
- **Health checks** — latency (ms) per device, up/down status
- **Port scanning** — checks common ports per device and flags risky services
  (Telnet, FTP, SMB, RDP left open)
- **History logging** — appends every scan to `data/history.csv` for trend analysis
- **HTML dashboard** — generates `dashboard.html` with device status, latency,
  open ports, and new-device warnings
- **Unknown device alerts** — compares against `config.json` known devices and
  highlights anything new that joins the network (optional email alert)

## Quick start

```powershell
# Demo mode - generates the dashboard from sample data, no network access needed
py run_monitor.py --demo

# Real scan of your subnet (edit config.json first)
py run_monitor.py

# Then open dashboard.html in a browser
```

## Configuration (`config.json`)

| Key | Meaning |
|-----|---------|
| `subnet` | Base of your LAN, e.g. `"192.168.1"` (scans .1-.254) |
| `ports` | TCP ports to check on each live device |
| `risky_ports` | Ports that trigger a security warning if open |
| `known_devices` | Map of MAC address -> friendly name; unknown MACs are flagged |
| `email` | SMTP settings for alerts (set `"enabled": false` to skip) |

## Scheduling (Windows Task Scheduler)

Run every 15 minutes:

```
Program:  py
Arguments: C:\Users\Bleon\Projects\network-health-monitor\run_monitor.py
```

## How it works

1. `netmon/discover.py` pings every address in the subnet concurrently, then reads
   the ARP cache to map IP -> MAC
2. `netmon/portscan.py` attempts TCP connections to the configured ports
3. `netmon/logger.py` appends one CSV row per device per scan
4. `netmon/dashboard.py` renders the latest scan (plus per-device history) to HTML
5. `netmon/alerts.py` emails a summary when a device goes down or an unknown MAC
   appears (disabled by default)

## Roadmap

- [ ] Latency history charts on the dashboard
- [ ] SQLite storage instead of CSV
- [ ] Monitor an ESP32 device via its HTTP health endpoint
- [ ] Service banner grabbing for open ports
