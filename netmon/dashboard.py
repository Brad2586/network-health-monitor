"""Render scan results to a standalone HTML dashboard."""

from datetime import datetime
from pathlib import Path

STYLE = """
body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f1419; color: #e6e6e6;
       max-width: 960px; margin: 30px auto; padding: 0 16px; }
h1 { color: #4fc3f7; margin-bottom: 4px; }
.meta { color: #888; margin-bottom: 24px; }
table { width: 100%; border-collapse: collapse; background: #1a2028; border-radius: 8px; overflow: hidden; }
th { background: #232b36; text-align: left; padding: 10px 14px; color: #4fc3f7; }
td { padding: 10px 14px; border-top: 1px solid #2a3340; }
.up { color: #66bb6a; font-weight: bold; }
.warn { color: #ffa726; }
.danger { color: #ef5350; font-weight: bold; }
.badge { background: #ef5350; color: white; border-radius: 4px; padding: 2px 8px;
         font-size: 0.8em; margin-left: 8px; }
.summary { display: flex; gap: 16px; margin-bottom: 24px; }
.card { background: #1a2028; border-radius: 8px; padding: 16px 24px; flex: 1; }
.card .num { font-size: 2em; font-weight: bold; color: #4fc3f7; }
.card .label { color: #888; }
"""


def render(devices: list[dict], out_path: Path) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unknown_count = sum(1 for d in devices if d.get("is_unknown"))
    warning_count = sum(len(d.get("warnings", [])) for d in devices)

    rows = []
    for d in sorted(devices, key=lambda x: tuple(int(o) for o in x["ip"].split("."))):
        name = d.get("name") or "?"
        unknown_badge = '<span class="badge">UNKNOWN DEVICE</span>' if d.get("is_unknown") else ""
        ports = ", ".join(str(p) for p in d.get("open_ports", [])) or "-"
        warnings = "<br>".join(d.get("warnings", []))
        warn_cell = f'<span class="danger">{warnings}</span>' if warnings else "-"
        rows.append(
            f"<tr><td>{d['ip']}</td><td>{d['mac']}</td>"
            f"<td>{name}{unknown_badge}</td>"
            f"<td class='up'>UP ({d['latency_ms']:.0f} ms)</td>"
            f"<td>{ports}</td><td>{warn_cell}</td></tr>"
        )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Network Health Monitor</title>
<meta http-equiv="refresh" content="300">
<style>{STYLE}</style></head><body>
<h1>Network Health Monitor</h1>
<div class="meta">Last scan: {now} &middot; auto-refreshes every 5 min</div>
<div class="summary">
  <div class="card"><div class="num">{len(devices)}</div><div class="label">Devices online</div></div>
  <div class="card"><div class="num">{unknown_count}</div><div class="label">Unknown devices</div></div>
  <div class="card"><div class="num">{warning_count}</div><div class="label">Security warnings</div></div>
</div>
<table>
<tr><th>IP</th><th>MAC</th><th>Name</th><th>Status</th><th>Open Ports</th><th>Warnings</th></tr>
{"".join(rows)}
</table>
</body></html>"""

    out_path.write_text(html, encoding="utf-8")
