from pathlib import Path

from drone_agent.agent import SecurityAnalystAgent
from drone_agent.indexer import FrameIndex
from drone_agent.models import Frame, Telemetry, load_frames
from drone_agent.qa import summarize_day

FRAMES_PATH = Path(__file__).resolve().parents[1] / "data" / "frames.json"


def make_frame(frame_id, time, location, description, altitude=12.0):
    return Frame(frame_id, Telemetry(time, location, altitude), description)


def test_one_log_per_object_episode_not_per_frame():
    frames = [
        make_frame(1, "12:00", "Garage", "Blue Ford F150 spotted at garage"),
        make_frame(2, "12:05", "Garage", "Blue Ford F150 spotted at garage"),
        make_frame(3, "12:10", "Garage", "Blue Ford F150 spotted at garage"),
    ]
    agent = SecurityAnalystAgent(index=FrameIndex())
    results = agent.run(frames)
    assert [len(r.logs) for r in results] == [1, 0, 0]
    assert results[0].logs == ["Blue truck spotted at Garage, 12:00."]


def test_frame_is_stored_even_when_nothing_is_detected():
    agent = SecurityAnalystAgent(index=FrameIndex())
    agent.run([make_frame(1, "03:00", "Garage", "Empty garage, dim lighting, no movement")])
    assert agent.index.frame_count() == 1
    assert agent.index.list_logs() == []


def test_alerts_are_stored_in_index():
    frames = [
        make_frame(1, "23:30", "Main Gate", "Car idling at the main gate with headlights on"),
    ]
    agent = SecurityAnalystAgent(index=FrameIndex())
    results = agent.run(frames)
    assert len(results[0].alerts) == 1
    stored = agent.index.list_alerts()
    assert len(stored) == 1 and stored[0]["rule"] == "after_hours_vehicle"


def test_full_day_pipeline_end_to_end():
    """Regression test over the committed one-day dataset."""
    frames = load_frames(FRAMES_PATH)
    assert len(frames) == 288  # one frame every 5 minutes for 24 hours

    agent = SecurityAnalystAgent(index=FrameIndex())
    agent.run(frames)
    index = agent.index

    alerts = [(a["time"], a["rule"]) for a in index.list_alerts()]
    assert alerts == [
        ("00:10", "loitering"),
        ("16:00", "low_altitude"),
        ("22:05", "night_intrusion"),
        ("22:20", "night_intrusion"),
        ("23:30", "after_hours_vehicle"),
    ]

    # The blue F150 entered the main gate twice today.
    assert index.count_entries(label="truck", color="blue") == 2

    summary = summarize_day(index)
    assert "288 frames" in summary
    assert "5 alerts" in summary
