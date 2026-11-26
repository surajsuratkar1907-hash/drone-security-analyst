"""Follow-up questions and a one-sentence day summary, answered from the index.

This is rule-based on purpose: it works offline and every answer can be traced to
rows in the database. An LLM could sit in front of this later to handle free phrasing.
"""
from __future__ import annotations

import re

from .describer import COLOR_WORDS, OBJECT_WORDS
from .indexer import FrameIndex

HELP_TEXT = (
    "I can answer questions like:\n"
    "  - what objects were in the video?\n"
    "  - show all truck events\n"
    "  - how many times did a blue truck enter?\n"
    "  - any alerts?\n"
    "  - summarize the day"
)

_OBJECT_QUESTION_WORDS = {"object", "objects", "see", "saw", "what", "which", "list", "things"}


def answer(index: FrameIndex, question: str) -> str:
    text = question.lower()
    tokens = re.findall(r"[a-z0-9]+", text)

    if "summar" in text:
        return summarize_day(index)
    if "alert" in tokens or "alerts" in tokens:
        return _alerts_text(index)

    label = next((OBJECT_WORDS[t] for t in tokens if t in OBJECT_WORDS), None)
    color = next((COLOR_WORDS[t] for t in tokens if t in COLOR_WORDS), None)

    if label is None:
        if _OBJECT_QUESTION_WORDS & set(tokens):
            return _objects_text(index)
        return HELP_TEXT

    phrase = " ".join(p for p in (color, label) if p)

    if {"how", "many", "count", "times"} & set(tokens):
        if "enter" in text:
            n = index.count_entries(label=label, color=color)
            return f"The {phrase} entered {n} time{'s' if n != 1 else ''} today."
        frame_ids = {r["frame_id"] for r in index.frames_with_object(label=label, color=color)}
        return f"The {phrase} appears in {len(frame_ids)} frame(s) today."

    logs = index.list_logs(label=label, color=color)
    if not logs:
        return f"No {phrase} events were logged."
    return "\n".join(f"{r['time']}  {r['text']}" for r in logs)


def summarize_day(index: FrameIndex) -> str:
    frames = index.frame_count()
    if frames == 0:
        return "No frames have been processed yet."
    logs = index.list_logs()
    alerts = index.list_alerts()
    labels = [r["label"] for r in index.object_summary()]
    high = sum(1 for a in alerts if a["severity"] == "high")
    if not alerts:
        alert_detail = "No alerts were raised."
    else:
        alert_detail = " Alerts: " + "; ".join(
            f"{a['time']} {a['rule']} ({a['severity']}) at {a['location']}" for a in alerts
        ) + "."
    return (
        f"Daily overview: {frames} frames processed; {len(logs)} event logs across "
        f"{', '.join(labels) or 'no detected object types'}; {len(alerts)} alerts, "
        f"including {high} high-severity."
        + alert_detail
    )


def _objects_text(index: FrameIndex) -> str:
    rows = index.object_summary()
    if not rows:
        return "Nothing was detected in the video."
    parts = [f"{r['label']} (in {r['frames']} frames)" for r in rows]
    return "Objects seen: " + ", ".join(parts) + "."


def _alerts_text(index: FrameIndex) -> str:
    rows = index.list_alerts()
    if not rows:
        return "No alerts were raised."
    return "\n".join(f"[{r['severity'].upper()}] {r['time']}  {r['message']}" for r in rows)
