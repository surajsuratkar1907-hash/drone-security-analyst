import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

import pytest

from drone_agent.agent import SecurityAnalystAgent
from drone_agent.dashboard import build_dashboard_data, serve_in_background
from drone_agent.indexer import FrameIndex
from drone_agent.models import load_frames

FRAMES_PATH = Path(__file__).resolve().parents[1] / "data" / "frames.json"


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "index.db")
    index = FrameIndex(path)
    SecurityAnalystAgent(index=index).run(load_frames(FRAMES_PATH))
    index.close()
    return path


def test_dashboard_data_has_every_frame_with_its_logs_and_alerts(db_path):
    index = FrameIndex(db_path)
    data = build_dashboard_data(index)
    index.close()

    assert len(data["frames"]) == 288
    assert data["stats"]["alerts"] == 5
    assert data["stats"]["blue_truck_entries"] == 2
    assert "Side Fence" in data["zones"]

    loiter = next(f for f in data["frames"] if f["time"] == "00:10")
    assert loiter["alerts"][0]["rule"] == "loitering"
    assert loiter["detections"][0]["label"] == "person"

    entering = next(f for f in data["frames"] if f["time"] == "07:40")
    assert entering["detections"] == [{"label": "truck", "color": "blue", "action": "entering"}]
    assert entering["logs"] == []  # same episode as the approach logged at 07:30


def test_http_endpoints_serve_page_data_and_answers(db_path):
    server = serve_in_background(db_path, port=0)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urlopen(base + "/") as res:
            page = res.read().decode("utf-8")
            assert res.headers["Content-Type"].startswith("text/html")
        assert "Drone Security Analyst" in page

        with urlopen(base + "/api/data") as res:
            data = json.loads(res.read())
        assert data["stats"]["frames"] == 288

        with urlopen(base + "/api/ask?q=" + quote("how many times did a blue truck enter today?")) as res:
            assert res.read().decode("utf-8") == "The blue truck entered 2 times today."
    finally:
        server.shutdown()
        server.server_close()
