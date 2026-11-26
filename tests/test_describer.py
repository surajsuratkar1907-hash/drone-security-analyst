from drone_agent.describer import SimulatedVisionDescriber
from drone_agent.models import Detection

describe = SimulatedVisionDescriber().describe


def test_blue_truck_logged_with_colour_and_action():
    assert describe("Blue Ford F150 spotted at garage") == [
        Detection(label="truck", color="blue", action="spotted")
    ]


def test_person_detected_with_action():
    assert describe("Person still near the main gate, looking at the fence") == [
        Detection(label="person", color=None, action="looking")
    ]


def test_empty_frame_has_no_detections():
    assert describe("Empty backyard, no movement") == []


def test_spelling_variant_of_grey_is_normalised():
    assert describe("Man in grey hoodie walking across the front lawn") == [
        Detection(label="person", color="grey", action="walking")
    ]


def test_animal_detected():
    assert describe("Dog running across the backyard") == [
        Detection(label="animal", color=None, action="running")
    ]
