"""SQLite-backed frame index.

Every frame is stored with its timestamp, location and altitude. Each detected
object is stored in a separate table, so frames can be searched by time, place or
object (for example "all truck frames between 07:00 and 18:00").
"""
from __future__ import annotations

import sqlite3
from typing import Any

from .models import Alert, Detection, Frame

SCHEMA = """
CREATE TABLE IF NOT EXISTS frames (
    frame_id    INTEGER PRIMARY KEY,
    time        TEXT    NOT NULL,
    minute      INTEGER NOT NULL,
    location    TEXT    NOT NULL,
    altitude_m  REAL    NOT NULL,
    description TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS detections (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    frame_id INTEGER NOT NULL REFERENCES frames(frame_id),
    label    TEXT    NOT NULL,
    color    TEXT,
    action   TEXT
);
CREATE INDEX IF NOT EXISTS idx_detections_label ON detections(label);
CREATE TABLE IF NOT EXISTS logs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    frame_id INTEGER NOT NULL REFERENCES frames(frame_id),
    time     TEXT    NOT NULL,
    minute   INTEGER NOT NULL,
    location TEXT    NOT NULL,
    label    TEXT    NOT NULL,
    color    TEXT,
    action   TEXT,
    text     TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    frame_id INTEGER NOT NULL REFERENCES frames(frame_id),
    time     TEXT    NOT NULL,
    location TEXT    NOT NULL,
    rule     TEXT    NOT NULL,
    severity TEXT    NOT NULL,
    message  TEXT    NOT NULL
);
"""


def _filters(label=None, color=None, location=None, start=None, end=None) -> tuple[list[str], list[Any]]:
    """Build WHERE clauses. Assumes the frames table is aliased f and detections d."""
    clauses: list[str] = []
    params: list[Any] = []
    if label is not None:
        clauses.append("d.label = ?")
        params.append(label)
    if color is not None:
        clauses.append("d.color = ?")
        params.append(color)
    if location is not None:
        clauses.append("f.location = ?")
        params.append(location)
    if start is not None:
        clauses.append("f.minute >= ?")
        params.append(start)
    if end is not None:
        clauses.append("f.minute <= ?")
        params.append(end)
    return clauses, params


class FrameIndex:
    def __init__(self, path: str = ":memory:") -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    # ----- writes -----

    def add_frame(self, frame: Frame, detections: list[Detection]) -> None:
        t = frame.telemetry
        self.conn.execute(
            "INSERT INTO frames (frame_id, time, minute, location, altitude_m, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (frame.frame_id, t.time, t.minute, t.location, t.altitude_m, frame.description),
        )
        self.conn.executemany(
            "INSERT INTO detections (frame_id, label, color, action) VALUES (?, ?, ?, ?)",
            [(frame.frame_id, d.label, d.color, d.action) for d in detections],
        )

    def add_log(self, frame: Frame, detection: Detection, text: str) -> None:
        t = frame.telemetry
        self.conn.execute(
            "INSERT INTO logs (frame_id, time, minute, location, label, color, action, text) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (frame.frame_id, t.time, t.minute, t.location,
             detection.label, detection.color, detection.action, text),
        )

    def add_alert(self, alert: Alert) -> None:
        self.conn.execute(
            "INSERT INTO alerts (frame_id, time, location, rule, severity, message) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (alert.frame_id, alert.time, alert.location, alert.rule, alert.severity, alert.message),
        )

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ----- reads -----

    def frame_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]

    def frames_in_range(self, start: int | None = None, end: int | None = None,
                        location: str | None = None) -> list[dict]:
        """Frames between two minute-of-day values (inclusive)."""
        clauses, params = _filters(location=location, start=start, end=end)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT f.* FROM frames f {where} ORDER BY f.frame_id", params
        ).fetchall()
        return [dict(r) for r in rows]

    def frames_with_object(self, label: str | None = None, color: str | None = None,
                           location: str | None = None, start: int | None = None,
                           end: int | None = None) -> list[dict]:
        """Frames (one row per detection) matching an object, colour, place and time window."""
        clauses, params = _filters(label, color, location, start, end)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"""SELECT f.frame_id, f.time, f.minute, f.location, f.altitude_m, f.description,
                       d.label, d.color, d.action
                FROM detections d JOIN frames f ON f.frame_id = d.frame_id
                {where}
                ORDER BY f.frame_id, d.id""",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def count_entries(self, label: str | None = None, color: str | None = None,
                      location: str | None = None, action: str = "entering") -> int:
        """Count episodes, not frames.

        Consecutive frames with the same object doing the same action count as one
        entry. A blue truck entering over three frames is one entry.
        """
        rows = [r for r in self.frames_with_object(label, color, location) if r["action"] == action]
        episodes = 0
        last_frame: dict[tuple, int] = {}
        for r in rows:
            key = (r["label"], r["color"], r["location"])
            previous = last_frame.get(key)
            if previous is None or r["frame_id"] != previous + 1:
                episodes += 1
            last_frame[key] = r["frame_id"]
        return episodes

    def object_summary(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT label, COUNT(DISTINCT frame_id) AS frames FROM detections "
            "GROUP BY label ORDER BY frames DESC, label"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_logs(self, label: str | None = None, color: str | None = None) -> list[dict]:
        clauses, params = [], []
        if label is not None:
            clauses.append("label = ?")
            params.append(label)
        if color is not None:
            clauses.append("color = ?")
            params.append(color)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT * FROM logs {where} ORDER BY minute, id", params
        ).fetchall()
        return [dict(r) for r in rows]

    def list_alerts(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM alerts ORDER BY frame_id, id").fetchall()
        return [dict(r) for r in rows]
