import pytest

from drone_agent.describer import SimulatedVisionDescriber
from drone_agent.indexer import FrameIndex
from drone_agent.models import Frame, Telemetry, parse_time
from drone_agent.agent import SecurityAnalystAgent


def make_frame(frame_id, time, location, description, altitude=12.0):
    return Frame(frame_id, Telemetry(time, location, altitude), description)


@pytest.fixture
def index_with_frames():
    frames = [
        make_frame(1, "07:30", "Main Gate", "Blue Ford F150 approaching the main gate"),
        make_frame(2, "07:35", "Main Gate", "Blue Ford F150 approaching the main gate"),
        make_frame(3, "07:40", "Main Gate", "Blue Ford F150 entering through the main gate"),
        make_frame(4, "09:00", "Front Lawn", "Empty front lawn, daylight, no movement"),
        make_frame(5, "12:00", "Garage", "Blue Ford F150 spotted at garage"),
        make_frame(6, "17:40", "Main Gate", "Blue Ford F150 entering through the main gate"),
    ]
    agent = SecurityAnalystAgent(index=FrameIndex())
    agent.run(frames)
    return agent.index


def test_frames_queryable_by_object(index_with_frames):
    rows = index_with_frames.frames_with_object(label="truck")
    assert [r["frame_id"] for r in rows] == [1, 2, 3, 5, 6]


def test_frames_queryable_by_colour_and_location(index_with_frames):
    rows = index_with_frames.frames_with_object(label="truck", color="blue", location="Garage")
    assert [r["frame_id"] for r in rows] == [5]


def test_frames_queryable_by_time_window(index_with_frames):
    rows = index_with_frames.frames_with_object(
        label="truck", start=parse_time("07:00"), end=parse_time("08:00"))
    assert [r["frame_id"] for r in rows] == [1, 2, 3]


def test_time_range_query_returns_all_frames_in_window(index_with_frames):
    rows = index_with_frames.frames_in_range(parse_time("09:00"), parse_time("12:00"))
    assert [r["frame_id"] for r in rows] == [4, 5]


def test_consecutive_entering_frames_count_as_one_entry(index_with_frames):
    # Frame 3 is the only entering frame in its run, so it counts once.
    assert index_with_frames.count_entries(label="truck", color="blue") == 2


def test_separate_entering_episodes_are_counted_separately():
    frames = [
        make_frame(1, "07:40", "Main Gate", "Blue Ford F150 entering through the main gate"),
        make_frame(2, "07:45", "Main Gate", "Blue Ford F150 entering through the main gate"),
        make_frame(3, "07:50", "Main Gate", "Empty main gate, daylight, no movement"),
        make_frame(4, "17:40", "Main Gate", "Blue Ford F150 entering through the main gate"),
    ]
    agent = SecurityAnalystAgent(index=FrameIndex())
    agent.run(frames)
    assert agent.index.count_entries(label="truck", color="blue") == 2


def test_object_summary_counts_frames(index_with_frames):
    summary = {r["label"]: r["frames"] for r in index_with_frames.object_summary()}
    assert summary == {"truck": 5}


def test_logs_written_once_per_episode(index_with_frames):
    # Frames 1-3 are one continuous episode (blue truck at Main Gate), so they log once.
    # Frame 5 (Garage) and frame 6 (Main Gate, after a gap) each start a new episode.
    logs = index_with_frames.list_logs(label="truck")
    assert [l["text"] for l in logs] == [
        "Blue truck approaching at Main Gate, 07:30.",
        "Blue truck spotted at Garage, 12:00.",
        "Blue truck entering at Main Gate, 17:40.",
    ]
