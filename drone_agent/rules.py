"""Predefined alert rules.

Each rule is stateful so it fires once per continuous episode, not once per frame.
An episode ends when the condition stops being true.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Hashable, Iterable

from .models import Alert, Detection, Frame

MINUTES_PER_DAY = 24 * 60
NIGHT_START = 22 * 60   # 22:00
NIGHT_END = 5 * 60      # 05:00
VEHICLE_LABELS = frozenset({"car", "truck", "van"})


def is_night(minute: int) -> bool:
    """True between 22:00 and 05:00, which wraps past midnight."""
    return minute >= NIGHT_START or minute < NIGHT_END


class EpisodeTracker:
    """Reports True only when a condition key starts or changes.

    Pass None when the condition is off. Passing the same key again returns False.
    """

    def __init__(self) -> None:
        self._active: Hashable | None = None

    def update(self, key: Hashable | None) -> bool:
        if key is None:
            self._active = None
            return False
        if key == self._active:
            return False
        self._active = key
        return True


class Rule(ABC):
    name: str = "rule"

    @abstractmethod
    def evaluate(self, frame: Frame, detections: list[Detection]) -> list[Alert]:
        """Return the alerts this frame triggers (usually none)."""

    def _alert(self, frame: Frame, severity: str, message: str) -> Alert:
        return Alert(
            frame_id=frame.frame_id,
            time=frame.telemetry.time,
            location=frame.telemetry.location,
            rule=self.name,
            severity=severity,
            message=message,
        )


class LoiteringRule(Rule):
    """A person stays in a watched zone at night for at least `dwell_minutes`."""

    name = "loitering"

    def __init__(self, zones: Iterable[str] = ("Main Gate",), dwell_minutes: int = 10) -> None:
        self.zones = set(zones)
        self.dwell_minutes = dwell_minutes
        self._tracker = EpisodeTracker()
        self._since = 0
        self._alerted = False

    def evaluate(self, frame: Frame, detections: list[Detection]) -> list[Alert]:
        t = frame.telemetry
        has_person = any(d.label == "person" for d in detections)
        applies = has_person and t.location in self.zones and is_night(t.minute)

        if self._tracker.update(t.location if applies else None):
            self._since = t.minute
            self._alerted = False
        if not applies:
            return []

        dwell = (t.minute - self._since) % MINUTES_PER_DAY
        if dwell >= self.dwell_minutes and not self._alerted:
            self._alerted = True
            return [self._alert(frame, "high", f"Person loitering at {t.location}, {t.time}")]
        return []


class NightIntrusionRule(Rule):
    """Any person in a restricted zone during night hours is an immediate alert."""

    name = "night_intrusion"

    def __init__(self, restricted_zones: Iterable[str] = ("Side Fence", "Backyard")) -> None:
        self.restricted_zones = set(restricted_zones)
        self._tracker = EpisodeTracker()

    def evaluate(self, frame: Frame, detections: list[Detection]) -> list[Alert]:
        t = frame.telemetry
        has_person = any(d.label == "person" for d in detections)
        applies = has_person and t.location in self.restricted_zones and is_night(t.minute)
        if not self._tracker.update((t.location,) if applies else None):
            return []
        return [self._alert(frame, "high", f"Person in restricted area at {t.location} at night, {t.time}")]


class AfterHoursVehicleRule(Rule):
    """A vehicle present during night hours."""

    name = "after_hours_vehicle"

    def __init__(self) -> None:
        self._tracker = EpisodeTracker()

    def evaluate(self, frame: Frame, detections: list[Detection]) -> list[Alert]:
        t = frame.telemetry
        vehicle = next((d for d in detections if d.label in VEHICLE_LABELS), None)
        applies = vehicle is not None and is_night(t.minute)
        key = (t.location, vehicle.label) if applies else None
        if not self._tracker.update(key):
            return []
        return [self._alert(frame, "medium", f"{vehicle.label.capitalize()} seen at {t.location} after hours, {t.time}")]


class LowAltitudeRule(Rule):
    """Safety rule: the drone flew below the minimum safe altitude."""

    name = "low_altitude"

    def __init__(self, min_altitude_m: float = 5.0) -> None:
        self.min_altitude_m = min_altitude_m
        self._tracker = EpisodeTracker()

    def evaluate(self, frame: Frame, detections: list[Detection]) -> list[Alert]:
        t = frame.telemetry
        applies = t.altitude_m < self.min_altitude_m
        if not self._tracker.update((t.location,) if applies else None):
            return []
        return [self._alert(
            frame,
            "high",
            f"Drone altitude {t.altitude_m:.1f} m at {t.location} is below the "
            f"{self.min_altitude_m:.1f} m safety minimum, {t.time}",
        )]


def default_rules() -> list[Rule]:
    """The rule set used when none is given. Create fresh instances per run (they hold state)."""
    return [LoiteringRule(), NightIntrusionRule(), AfterHoursVehicleRule(), LowAltitudeRule()]
