import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES_PATH = ROOT / "data" / "frames.json"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_frames", ROOT / "data" / "generate_frames.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_frames_match_generator():
    """If this fails, re-run: python data/generate_frames.py"""
    generated = _load_generator().build_frames()
    committed = json.loads(FRAMES_PATH.read_text(encoding="utf-8"))
    assert committed == generated


def test_frames_have_sequential_ids_and_valid_times():
    frames = json.loads(FRAMES_PATH.read_text(encoding="utf-8"))
    assert [f["frame_id"] for f in frames] == list(range(1, len(frames) + 1))
    for f in frames:
        hours, minutes = map(int, f["time"].split(":"))
        assert 0 <= hours < 24 and 0 <= minutes < 60
        assert {"frame_id", "time", "location", "altitude_m", "description"} <= f.keys()
