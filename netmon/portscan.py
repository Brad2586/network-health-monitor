"""TCP port checks with risky-service flagging."""

import socket
from concurrent.futures import ThreadPoolExecutor


def check_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if a TCP connection to ip:port succeeds."""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def scan_device(ip: str, ports: list[int]) -> list[int]:
    """Return the subset of ports that are open on this device."""
    with ThreadPoolExecutor(max_workers=len(ports) or 1) as pool:
        results = pool.map(lambda p: (p, check_port(ip, p)), ports)
    return [port for port, is_open in results if is_open]


def flag_risky(open_ports: list[int], risky_ports: dict) -> list[str]:
    """Return human-readable warnings for risky open ports.

    risky_ports maps port (as str, from JSON) -> description.
    """
    warnings = []
    for port in open_ports:
        desc = risky_ports.get(str(port))
        if desc:
            warnings.append(f"Port {port} open: {desc}")
    return warnings
