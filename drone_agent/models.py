"""Core data types shared by every part of the agent."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MINUTES_PER_DAY = 24 * 60


def parse_time(value: str) -> int:
    """Convert "HH:MM" into minutes since midnight."""
    try:
        hours_text, minutes_text = value.split(":")
        hours, minutes = int(hours_text), int(minutes_text)
    except ValueError as exc:
        raise ValueError(f"Invalid time {value!r}; expected HH:MM") from exc
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(f"Time out of range: {value!r}")
    return hours * 60 + minutes


def format_time(minute: int) -> str:
    """Convert minutes since midnight back into "HH:MM"."""
    minute %= MINUTES_PER_DAY
    return f"{minute // 60:02d}:{minute % 60:02d}"


@dataclass(frozen=True)
class Telemetry:
    """Where the drone was and how high it was when a frame was captured."""

    time: str
    location: str
    altitude_m: float

    @property
    def minute(self) -> int:
        return parse_time(self.time)


@dataclass(frozen=True)
class Frame:
    """One simulated video frame: telemetry plus a text description of what the camera sees."""

    frame_id: int
    telemetry: Telemetry
    description: str


@dataclass(frozen=True)
class Detection:
    """Something the vision step found in a frame."""

    label: str                  # truck, van, car, person, animal
    color: str | None = None    # blue, white, grey, ...
    action: str | None = None   # entering, parked, walking, ...


@dataclass(frozen=True)
class Alert:
    """A security or safety alert raised by a rule."""

    frame_id: int
    time: str
    location: str
    rule: str
    severity: str               # low | medium | high
    message: str


def load_frames(path: str | Path) -> list[Frame]:
    """Read a frames JSON file (see data/generate_frames.py) into Frame objects."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Frame(
            frame_id=int(item["frame_id"]),
            telemetry=Telemetry(
                time=item["time"],
                location=item["location"],
                altitude_m=float(item["altitude_m"]),
            ),
            description=item["description"],
        )
        for item in raw
    ]
