"""The Drone Security Analyst agent: the per-frame pipeline.

For each frame the agent:
  1. describes it (simulated vision) into detections,
  2. stores the frame and detections in the index,
  3. logs an event when an object first appears (not on every frame),
  4. runs every rule and stores any alerts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .describer import SimulatedVisionDescriber
from .indexer import FrameIndex
from .models import Alert, Detection, Frame, Telemetry
from .rules import Rule, default_rules


@dataclass
class FrameResult:
    frame_id: int
    logs: list[str] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)


def describe_log(detection: Detection, telemetry: Telemetry) -> str:
    """Build a human-readable log line, e.g. "Blue truck spotted at Garage, 12:00."."""
    subject = " ".join(p for p in (detection.color, detection.label) if p)
    subject = subject[:1].upper() + subject[1:]
    verb = detection.action or "detected"
    return f"{subject} {verb} at {telemetry.location}, {telemetry.time}."


class SecurityAnalystAgent:
    def __init__(self, index: FrameIndex | None = None,
                 describer: SimulatedVisionDescriber | None = None,
                 rules: Iterable[Rule] | None = None) -> None:
        self.index = index if index is not None else FrameIndex()
        self.describer = describer or SimulatedVisionDescriber()
        self.rules: list[Rule] = list(rules) if rules is not None else default_rules()
        # Object episodes seen in the previous frame, keyed by (label, color, location).
        self._active: set[tuple] = set()

    def process_frame(self, frame: Frame) -> FrameResult:
        t = frame.telemetry
        detections = self.describer.describe(frame.description)
        self.index.add_frame(frame, detections)
        result = FrameResult(frame_id=frame.frame_id)

        previous = self._active
        self._active = set()
        for detection in detections:
            key = (detection.label, detection.color, t.location)
            self._active.add(key)
            if key not in previous:  # a new episode started, so log it once
                text = describe_log(detection, t)
                self.index.add_log(frame, detection, text)
                result.logs.append(text)

        for rule in self.rules:
            for alert in rule.evaluate(frame, detections):
                self.index.add_alert(alert)
                result.alerts.append(alert)
        return result

    def run(self, frames: Iterable[Frame]) -> list[FrameResult]:
        results = [self.process_frame(f) for f in sorted(frames, key=lambda f: f.frame_id)]
        self.index.commit()
        return results
