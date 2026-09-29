"""Email alerts for unknown devices and security warnings (optional)."""

import smtplib
from email.message import EmailMessage


def build_alert_body(devices: list[dict]) -> str | None:
    """Return alert text if anything is worth alerting on, else None."""
    lines = []
    for d in devices:
        if d.get("is_unknown"):
            lines.append(f"Unknown device joined: {d['ip']} (MAC {d['mac']})")
        for w in d.get("warnings", []):
            lines.append(f"{d['ip']} ({d.get('name') or 'unknown'}): {w}")
    return "\n".join(lines) if lines else None


def send_alert(body: str, email_cfg: dict) -> None:
    if not email_cfg.get("enabled"):
        return
    msg = EmailMessage()
    msg["Subject"] = "Network Health Monitor - Alert"
    msg["From"] = email_cfg["username"]
    msg["To"] = email_cfg["to"]
    msg.set_content(body)

    with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as smtp:
        smtp.starttls()
        smtp.login(email_cfg["username"], email_cfg["password"])
        smtp.send_message(msg)
