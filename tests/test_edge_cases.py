from drone_agent.rules import LoiteringRule
from drone_agent.models import Frame, Telemetry
from drone_agent.describer import SimulatedVisionDescriber


def frame(i, time, desc='Person standing at main gate'):
    return Frame(i, Telemetry(time, 'Main Gate', 12.0), desc)


def test_loitering_resets_after_large_observation_gap():
    rule = LoiteringRule(dwell_minutes=10, max_observation_gap_minutes=5)
    d = SimulatedVisionDescriber()
    alerts = []
    for f in [frame(1, '00:00'), frame(2, '00:05'), frame(3, '00:20'), frame(4, '00:25'), frame(5, '00:30')]:
        alerts.extend(rule.evaluate(f, d.describe(f.description)))
    assert [a.time for a in alerts] == ['00:30']


def test_loitering_continuity_across_midnight():
    rule = LoiteringRule(dwell_minutes=10)
    d = SimulatedVisionDescriber()
    alerts = []
    for f in [frame(1, '23:55'), frame(2, '00:00'), frame(3, '00:05')]:
        alerts.extend(rule.evaluate(f, d.describe(f.description)))
    assert [a.time for a in alerts] == ['00:05']
