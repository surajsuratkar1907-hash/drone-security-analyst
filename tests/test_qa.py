from pathlib import Path

import pytest

from drone_agent.agent import SecurityAnalystAgent
from drone_agent.indexer import FrameIndex
from drone_agent.models import load_frames
from drone_agent.qa import answer

FRAMES_PATH = Path(__file__).resolve().parents[1] / "data" / "frames.json"


@pytest.fixture(scope="module")
def index():
    agent = SecurityAnalystAgent(index=FrameIndex())
    agent.run(load_frames(FRAMES_PATH))
    return agent.index


def test_what_objects_were_in_the_video(index):
    text = answer(index, "What objects were in the video?")
    assert "truck" in text and "person" in text and "animal" in text


def test_show_all_truck_events(index):
    text = answer(index, "show all truck events")
    assert "07:30" in text and "12:00" in text and "17:40" in text


def test_how_many_times_did_blue_truck_enter(index):
    assert answer(index, "how many times did the blue truck enter today?") == \
        "The blue truck entered 2 times today."


def test_alerts_question_lists_alerts(index):
    text = answer(index, "any alerts?")
    assert "[HIGH] 00:10" in text
    assert "[MEDIUM] 23:30" in text


def test_summarize_question(index):
    assert "288 frames" in answer(index, "summarize the day")


def test_unknown_question_returns_help(index):
    assert "I can answer questions like" in answer(index, "tell me a joke")
