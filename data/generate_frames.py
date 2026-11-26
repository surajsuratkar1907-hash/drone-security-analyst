"""Generate data/frames.json: one simulated 24-hour day of drone frames.

One frame is captured every 5 minutes, giving 288 frames. The SEGMENTS list scripts
the events the rules and queries should find. Every other minute is routine patrol,
where the drone cycles through the property and sees an empty area.

Each segment is (start, end, location, description[, altitude_m]). Times are "HH:MM"
and `end` is exclusive. Frames only show what the camera sees from the drone's
current position.

Run from the project root:  python data/generate_frames.py
"""
from __future__ import annotations

import json
from pathlib import Path

INTERVAL_MIN = 5
PATROL = [
    ("Main Gate", 12.0),
    ("Driveway", 12.0),
    ("Garage", 15.0),
    ("Backyard", 10.0),
    ("Side Fence", 8.0),
    ("Front Lawn", 12.0),
]
ALTITUDE = dict(PATROL)

SEGMENTS = [
    # Night loitering at the main gate: triggers the loitering alert at 00:10.
    ("00:00", "00:25", "Main Gate", "Person standing near the main gate, looking at the fence"),
    ("00:25", "00:50", "Main Gate", "Person checking the gate latch, still near the main gate"),
    # Blue Ford F150: arrives, enters, drives in, parks, is spotted again later.
    ("07:30", "07:40", "Main Gate", "Blue Ford F150 approaching the main gate"),
    ("07:40", "07:45", "Main Gate", "Blue Ford F150 entering through the main gate"),
    ("07:45", "08:00", "Driveway", "Blue Ford F150 driving along the driveway"),
    ("08:00", "08:30", "Garage", "Blue Ford F150 parked at the garage"),
    # Daytime pedestrian: logged, but no alert.
    ("09:00", "09:20", "Front Lawn", "Man in grey hoodie walking across the front lawn"),
    ("12:00", "13:30", "Garage", "Blue Ford F150 spotted at garage"),
    # White delivery van: a daytime entry.
    ("13:30", "13:40", "Main Gate", "White delivery van entering through the main gate"),
    ("13:45", "14:00", "Driveway", "White delivery van parked at the driveway"),
    # Dog in the backyard: an animal in a restricted zone, but daytime, so no alert.
    ("14:00", "14:20", "Backyard", "Dog running across the backyard"),
    # Drone drops to 3 m for an inspection: triggers the low-altitude safety alert.
    ("16:00", "16:05", "Garage", "Drone descending for a close inspection of the garage door", 3.0),
    # Blue Ford F150: leaves, comes back. This is the second entry of the day.
    ("17:00", "17:15", "Garage", "Blue Ford F150 leaving the garage"),
    ("17:15", "17:25", "Driveway", "Blue Ford F150 driving along the driveway"),
    ("17:25", "17:30", "Main Gate", "Blue Ford F150 leaving through the main gate"),
    ("17:40", "17:45", "Main Gate", "Blue Ford F150 entering through the main gate"),
    ("17:45", "18:30", "Driveway", "Blue Ford F150 parked at the driveway"),
    # Night intrusion: a person climbs the side fence, then walks into the backyard.
    ("22:05", "22:20", "Side Fence", "Person climbing over the side fence"),
    ("22:20", "22:30", "Backyard", "Person walking across the backyard"),
    # Car idling at the gate after hours: triggers the after-hours vehicle alert.
    ("23:30", "23:40", "Main Gate", "Car idling at the main gate with headlights on"),
]


def _minute(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def _format(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _is_night(minute: int) -> bool:
    return minute >= 22 * 60 or minute < 5 * 60


def build_frames() -> list[dict]:
    frames: list[dict] = []
    for minute in range(0, 24 * 60, INTERVAL_MIN):
        segment = next(
            (s for s in SEGMENTS if _minute(s[0]) <= minute < _minute(s[1])),
            None,
        )
        if segment is not None:
            location, description = segment[2], segment[3]
            altitude = segment[4] if len(segment) > 4 else ALTITUDE[location]
        else:
            location = PATROL[(minute // INTERVAL_MIN) % len(PATROL)][0]
            lighting = "dim lighting" if _is_night(minute) else "daylight"
            description = f"Empty {location}, {lighting}, no movement"
            altitude = ALTITUDE[location]

        frames.append({
            "frame_id": len(frames) + 1,
            "time": _format(minute),
            "location": location,
            "altitude_m": altitude,
            "description": description,
        })
    return frames


def main() -> None:
    out = Path(__file__).resolve().parent / "frames.json"
    frames = build_frames()
    out.write_text(json.dumps(frames, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(frames)} frames to {out}")


if __name__ == "__main__":
    main()
