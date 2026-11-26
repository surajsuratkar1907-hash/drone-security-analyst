"""Local web dashboard for the Drone Security Analyst.

Standard library only: a tiny HTTP server serves one HTML page plus two JSON endpoints.

    /              the dashboard page
    /api/data      every frame with its detections, logs and alerts, plus summary stats
    /api/ask?q=... answers a follow-up question (same engine as `python -m drone_agent ask`)
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .indexer import FrameIndex
from .qa import answer

STATIC_DIR = Path(__file__).resolve().parent / "static"


def build_dashboard_data(index: FrameIndex) -> dict:
    """Collect everything the page needs into one JSON-friendly dict."""
    detections: dict[int, list[dict]] = {}
    for r in index.frames_with_object():
        detections.setdefault(r["frame_id"], []).append(
            {"label": r["label"], "color": r["color"], "action": r["action"]})

    logs: dict[int, list[str]] = {}
    log_rows = index.list_logs()
    for r in log_rows:
        logs.setdefault(r["frame_id"], []).append(r["text"])

    alerts: dict[int, list[dict]] = {}
    alert_rows = index.list_alerts()
    for r in alert_rows:
        alerts.setdefault(r["frame_id"], []).append(
            {"severity": r["severity"], "message": r["message"], "rule": r["rule"]})

    frames = []
    for f in index.frames_in_range():
        fid = f["frame_id"]
        frames.append({
            "frame_id": fid,
            "time": f["time"],
            "location": f["location"],
            "altitude_m": f["altitude_m"],
            "description": f["description"],
            "detections": detections.get(fid, []),
            "logs": logs.get(fid, []),
            "alerts": alerts.get(fid, []),
        })

    return {
        "frames": frames,
        "zones": sorted({f["location"] for f in frames}),
        "stats": {
            "frames": len(frames),
            "events": len(log_rows),
            "alerts": len(alert_rows),
            "blue_truck_entries": index.count_entries(label="truck", color="blue"),
        },
        "objects": index.object_summary(),
    }


def make_handler(db_path: str) -> type[BaseHTTPRequestHandler]:
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (name required by http.server)
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", (STATIC_DIR / "dashboard.html").read_bytes())
            elif parsed.path == "/api/data":
                index = FrameIndex(db_path)
                try:
                    body = json.dumps(build_dashboard_data(index)).encode("utf-8")
                finally:
                    index.close()
                self._send(200, "application/json", body)
            elif parsed.path == "/api/ask":
                question = parse_qs(parsed.query).get("q", [""])[0]
                index = FrameIndex(db_path)
                try:
                    text = answer(index, question)
                finally:
                    index.close()
                self._send(200, "text/plain; charset=utf-8", text.encode("utf-8"))
            else:
                self._send(404, "text/plain; charset=utf-8", b"Not found")

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # keep the terminal quiet
            pass

    return DashboardHandler


def create_server(db_path: str, port: int = 8000, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """Create (but do not start) the server. Port 0 picks a free port."""
    return ThreadingHTTPServer((host, port), make_handler(db_path))


def serve(db_path: str, port: int = 8000, host: str = "127.0.0.1") -> None:
    server = create_server(db_path, port, host)
    url = f"http://{host}:{server.server_address[1]}"
    print(f"Dashboard running at {url}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def serve_in_background(db_path: str, port: int = 0) -> ThreadingHTTPServer:
    """Used by tests: start the server on a thread and return it."""
    server = create_server(db_path, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
