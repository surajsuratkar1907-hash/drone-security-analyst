from drone_agent.models import Frame, Telemetry
from drone_agent.rules import (
    AfterHoursVehicleRule,
    LoiteringRule,
    LowAltitudeRule,
    NightIntrusionRule,
    default_rules,
)
from drone_agent.describer import SimulatedVisionDescriber

describe = SimulatedVisionDescriber().describe


def make_frame(frame_id, time, location, description, altitude=12.0):
    return Frame(frame_id, Telemetry(time, location, altitude), description)


def run_rule(rule, frames):
    """Feed frames through one rule and collect the alerts it raises."""
    alerts = []
    for frame in frames:
        alerts.extend(rule.evaluate(frame, describe(frame.description)))
    return alerts


PERSON_AT_GATE = "Person standing near the main gate"
EMPTY_GATE = "Empty main gate, dim lighting, no movement"


def test_loitering_alert_fires_at_midnight_after_dwell_time():
    frames = [make_frame(i + 1, f"00:{m:02d}", "Main Gate", PERSON_AT_GATE)
              for i, m in enumerate(range(0, 15, 5))]  # 00:00, 00:05, 00:10
    alerts = run_rule(LoiteringRule(dwell_minutes=10), frames)
    assert len(alerts) == 1
    assert alerts[0].time == "00:10"
    assert alerts[0].message == "Person loitering at Main Gate, 00:10"
    assert alerts[0].severity == "high"


def test_loitering_does_not_fire_before_dwell_time():
    frames = [make_frame(1, "00:00", "Main Gate", PERSON_AT_GATE),
              make_frame(2, "00:05", "Main Gate", PERSON_AT_GATE)]
    assert run_rule(LoiteringRule(dwell_minutes=10), frames) == []


def test_loitering_ignored_during_daytime():
    frames = [make_frame(i + 1, f"09:{m:02d}", "Main Gate", PERSON_AT_GATE)
              for i, m in enumerate(range(0, 30, 5))]
    assert run_rule(LoiteringRule(), frames) == []


def test_loitering_dwell_resets_when_person_leaves():
    frames = [
        make_frame(1, "00:00", "Main Gate", PERSON_AT_GATE),
        make_frame(2, "00:05", "Main Gate", EMPTY_GATE),       # person leaves
        make_frame(3, "00:10", "Main Gate", PERSON_AT_GATE),   # returns, dwell restarts
        make_frame(4, "00:15", "Main Gate", PERSON_AT_GATE),
    ]
    assert run_rule(LoiteringRule(dwell_minutes=10), frames) == []


def test_night_intrusion_fires_once_per_episode():
    frames = [
        make_frame(1, "22:05", "Side Fence", "Person climbing over the side fence"),
        make_frame(2, "22:10", "Side Fence", "Person climbing over the side fence"),
    ]
    alerts = run_rule(NightIntrusionRule(), frames)
    assert len(alerts) == 1
    assert alerts[0].location == "Side Fence"


def test_person_in_restricted_zone_by_day_is_not_an_intrusion():
    frames = [make_frame(1, "14:00", "Backyard", "Person walking across the backyard")]
    assert run_rule(NightIntrusionRule(), frames) == []


def test_vehicle_after_hours_raises_medium_alert():
    frames = [make_frame(1, "23:30", "Main Gate", "Car idling at the main gate with headlights on")]
    alerts = run_rule(AfterHoursVehicleRule(), frames)
    assert len(alerts) == 1
    assert alerts[0].severity == "medium"
    assert "Car seen at Main Gate after hours" in alerts[0].message


def test_daytime_truck_does_not_trigger_after_hours_rule():
    frames = [make_frame(1, "07:40", "Main Gate", "Blue Ford F150 entering through the main gate")]
    assert run_rule(AfterHoursVehicleRule(), frames) == []


def test_low_altitude_safety_alert():
    frames = [make_frame(1, "16:00", "Garage", "Drone descending for a close inspection", altitude=3.0)]
    alerts = run_rule(LowAltitudeRule(min_altitude_m=5.0), frames)
    assert len(alerts) == 1
    assert "3.0 m" in alerts[0].message


def test_normal_altitude_is_silent():
    frames = [make_frame(1, "16:00", "Garage", "Empty garage", altitude=15.0)]
    assert run_rule(LowAltitudeRule(), frames) == []


def test_default_rules_has_all_four_rules():
    names = {r.name for r in default_rules()}
    assert names == {"loitering", "night_intrusion", "after_hours_vehicle", "low_altitude"}
