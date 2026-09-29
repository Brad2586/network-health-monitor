"""Device discovery: threaded ping sweep + ARP table parsing (Windows)."""

import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor


def get_own_ip_and_mac(subnet: str) -> tuple[str, str]:
    """Return this machine's IP and MAC on the scanned subnet.

    ARP never lists our own machine, and a PC can have several adapters
    (e.g. Ethernet + Wi-Fi), so we ask the OS which interface routes to the
    target subnet, then match that IP to its adapter in `ipconfig /all`.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((f"{subnet}.1", 80))  # no traffic sent; selects the interface
        own_ip = s.getsockname()[0]
    finally:
        s.close()

    own_mac = "UNKNOWN"
    try:
        out = subprocess.run(["ipconfig", "/all"], capture_output=True,
                             text=True, timeout=10)
        current_mac = None
        for line in out.stdout.splitlines():
            mac_match = re.search(r"Physical Address.*:\s*([0-9A-Fa-f-]{17})", line)
            if mac_match:
                current_mac = mac_match.group(1).upper()
            elif re.search(rf"IPv4 Address.*:\s*{re.escape(own_ip)}\b", line):
                if current_mac:
                    own_mac = current_mac
                break
    except (subprocess.TimeoutExpired, OSError):
        pass
    return own_ip, own_mac


def ping(ip: str, timeout_ms: int = 500) -> float | None:
    """Ping once. Returns latency in ms, or None if host is down."""
    try:
        out = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), ip],
            capture_output=True, text=True, timeout=timeout_ms / 1000 + 2,
        )
        if out.returncode != 0:
            return None
        match = re.search(r"time[=<](\d+)ms", out.stdout)
        return float(match.group(1)) if match else 0.0
    except (subprocess.TimeoutExpired, OSError):
        return None


def get_arp_table() -> dict[str, str]:
    """Parse `arp -a` into {ip: mac} with normalized MAC format."""
    table = {}
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
        for line in out.stdout.splitlines():
            match = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})", line)
            if match:
                table[match.group(1)] = match.group(2).upper()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return table


def sweep(subnet: str, max_workers: int = 64) -> list[dict]:
    """Ping every host in subnet.1-254; return live devices with IP, MAC, latency."""
    ips = [f"{subnet}.{i}" for i in range(1, 255)]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        latencies = list(pool.map(ping, ips))

    arp = get_arp_table()
    own_ip, own_mac = get_own_ip_and_mac(subnet)
    if own_mac != "UNKNOWN":
        arp[own_ip] = own_mac

    devices = []
    for ip, latency in zip(ips, latencies):
        if latency is not None:
            devices.append({
                "ip": ip,
                "mac": arp.get(ip, "UNKNOWN"),
                "latency_ms": latency,
            })
    return devices
