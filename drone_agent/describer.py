"""Simulated vision model: turns a frame's text description into detections.

In a production system a vision-language model or detector (CLIP, BLIP, YOLO, ...)
would produce these detections from pixels. Here a small keyword vocabulary does
the job, so the rest of the pipeline (rules, index, queries) can be built and tested
without a GPU or a real camera feed.
"""
from __future__ import annotations

import re

from .models import Detection

# Words that mean an object, mapped to a canonical label.
OBJECT_WORDS: dict[str, str] = {
    "truck": "truck",
    "f150": "truck",
    "pickup": "truck",
    "van": "van",
    "car": "car",
    "sedan": "car",
    "person": "person",
    "man": "person",
    "woman": "person",
    "someone": "person",
    "figure": "person",
    "dog": "animal",
    "cat": "animal",
}

# Colour words, with spelling normalised.
COLOR_WORDS: dict[str, str] = {
    "blue": "blue",
    "white": "white",
    "black": "black",
    "red": "red",
    "grey": "grey",
    "gray": "grey",
    "silver": "silver",
    "green": "green",
}

# Motion or state words. The first one in the text becomes the detection's action.
ACTION_WORDS: frozenset[str] = frozenset({
    "entering", "leaving", "approaching", "driving", "parked", "spotted",
    "walking", "running", "standing", "climbing", "checking", "looking",
    "idling", "descending",
})

_TOKEN = re.compile(r"[a-z0-9]+")


class SimulatedVisionDescriber:
    """Produces one Detection per distinct object label found in a description.

    Known limitation: colour and action apply to every object in the same
    description. Keep one main object per simulated frame for accurate results.
    """

    def describe(self, description: str) -> list[Detection]:
        tokens = _TOKEN.findall(description.lower())

        labels: list[str] = []
        for token in tokens:
            label = OBJECT_WORDS.get(token)
            if label and label not in labels:
                labels.append(label)

        color = next((COLOR_WORDS[t] for t in tokens if t in COLOR_WORDS), None)
        action = next((t for t in tokens if t in ACTION_WORDS), None)

        return [Detection(label=label, color=color, action=action) for label in labels]
