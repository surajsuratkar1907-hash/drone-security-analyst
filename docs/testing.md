# Testing

Run everything with `python -m pytest -v` from the project root.

## Strategy

| Level | What it checks | Files |
|---|---|---|
| Unit: describer | Descriptions become the right detections (label, colour, action) | `tests/test_describer.py` |
| Unit: rules | Each rule fires when it should, stays silent when it should not, and fires once per episode | `tests/test_rules.py` |
| Unit: index | Queries by object, colour, place and time window; entry counting; log episodes | `tests/test_indexer.py` |
| Integration | The agent logs once per episode and stores alerts | `tests/test_agent.py` |
| End-to-end | The full one-day dataset produces the expected alerts and entry count | `tests/test_agent.py::test_full_day_pipeline_end_to_end` |
| Q&A | Follow-up questions return the expected answers | `tests/test_qa.py` |
| Data consistency | `frames.json` matches the generator and has valid IDs and times | `tests/test_frames_data.py` |
| Edge cases | Large observation gaps and continuity across midnight | `tests/test_edge_cases.py` |

## Key test cases

| Test | Scenario | Expected |
|---|---|---|
| `test_blue_truck_logged_with_colour_and_action` | "Blue Ford F150 spotted at garage" | One truck, blue, spotted |
| `test_loitering_alert_fires_at_midnight_after_dwell_time` | Person at gate 00:00 → 00:10 | Exactly one alert at 00:10 |
| `test_loitering_does_not_fire_before_dwell_time` | Person at gate for 5 minutes | No alert |
| `test_loitering_ignored_during_daytime` | Person at gate at 09:00 | No alert |
| `test_loitering_dwell_resets_when_person_leaves` | Person leaves, then returns | Dwell restarts |
| `test_night_intrusion_fires_once_per_episode` | Person in restricted zone for consecutive frames | One alert |
| `test_person_in_restricted_zone_by_day_is_not_an_intrusion` | Person in backyard at 14:00 | No alert |
| `test_vehicle_after_hours_raises_medium_alert` | Car at gate at 23:30 | One medium alert |
| `test_daytime_truck_does_not_trigger_after_hours_rule` | Truck entering at 07:40 | No alert |
| `test_low_altitude_safety_alert` | Drone at 3 m | One high alert |
| `test_normal_altitude_is_silent` | Drone at 15 m | No alert |
| `test_separate_entering_episodes_are_counted_separately` | Entry, gap, entry | Two entries |
| `test_consecutive_entering_frames_count_as_one_entry` | Entering over consecutive frames | One entry per run |
| `test_full_day_pipeline_end_to_end` | 288 frames, one day | Expected alerts and blue-truck entry count |

## Dynamic inputs and emergency responses

- Dynamic inputs include frames with changing time, location, altitude, object descriptions and observation gaps.
- Emergency-style responses include night intrusion, low altitude and loitering; tests check alert timing and episode suppression.
- The committed dataset is deterministic and does not represent live sensor input.

## Manual verification

The author previously reported running `python -m drone_agent run` on the committed dataset and observing logs/alerts matching the scripted scenario.

## Known gaps

- The describer is keyword-based; it is not an image detector or VLM. A pixel-based model would require labelled-image evaluation.
- Proxy identity can merge distinct objects.
- Alert thresholds are illustrative and not tuned against real footage.
- The benchmark does not measure model inference, persistent storage, network latency or concurrency.

## Historical test result

The author reported **40 passing tests in 1.49 seconds** using pytest 8.3.5 before this documentation refresh. This historical result is not a verification of subsequent edits; rerun the suite after changes.

## Synthetic benchmark interpretation

Run `python scripts/benchmark.py`. It measures a synthetic workload with simulated descriptions and the in-memory index. Its throughput is machine-dependent and must not be interpreted as production performance or real-time vision inference.
