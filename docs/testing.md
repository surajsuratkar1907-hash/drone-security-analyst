# Testing

Run everything with `python -m pytest -v` from the project root. The suite runs in under a second.

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

## Key test cases

| Test | Scenario | Expected |
|---|---|---|
| `test_blue_truck_logged_with_colour_and_action` | "Blue Ford F150 spotted at garage" | One truck, blue, spotted |
| `test_loitering_alert_fires_at_midnight_after_dwell_time` | Person at gate 00:00 → 00:10 | Exactly one alert at 00:10 |
| `test_loitering_does_not_fire_before_dwell_time` | Person at gate for 5 minutes | No alert |
| `test_loitering_ignored_during_daytime` | Person at gate at 09:00 | No alert |
| `test_loitering_dwell_resets_when_person_leaves` | Person leaves, then returns | No alert (dwell restarts) |
| `test_night_intrusion_fires_once_per_episode` | Person on side fence for two frames | One alert |
| `test_person_in_restricted_zone_by_day_is_not_an_intrusion` | Person in backyard at 14:00 | No alert |
| `test_vehicle_after_hours_raises_medium_alert` | Car at gate at 23:30 | One medium alert |
| `test_daytime_truck_does_not_trigger_after_hours_rule` | Truck entering at 07:40 | No alert |
| `test_low_altitude_safety_alert` | Drone at 3 m | One high alert |
| `test_normal_altitude_is_silent` | Drone at 15 m | No alert |
| `test_separate_entering_episodes_are_counted_separately` | Entry, gap, entry | Two entries |
| `test_consecutive_entering_frames_count_as_one_entry` | Entering over consecutive frames | One entry per run |
| `test_full_day_pipeline_end_to_end` | 288 frames, one day | Alerts: 00:10 loitering, 16:00 low altitude, 22:05 and 22:20 intrusion, 23:30 after-hours vehicle; blue truck entered twice |
| `test_how_many_times_did_blue_truck_enter` | Question on the full day | "The blue truck entered 2 times today." |

## Dynamic inputs and emergency responses

- **Dynamic inputs.** The tests feed frames in different orders, with gaps, with changing
  altitude and with mixed day and night times. `sorted()` in `run()` handles out-of-order frame IDs.
- **Emergency-style responses.** Night intrusion, low altitude and loitering each produce a
  high-severity alert on the first qualifying frame. The end-to-end test checks the exact
  timestamps, so a regression in timing or a missed rule fails the build.

## Manual verification

`python -m drone_agent run` was run on the committed dataset. The printed logs and alerts
matched the scripted scenario in `data/generate_frames.py`.

## Known gaps

- The describer is keyword-based, so it is only as good as the description text. A real
  detector would need its own accuracy tests against labelled footage.
- Alert thresholds are not tuned against real data.

## Updated verification and edge cases

The current repository test run is **40 passing tests** (captured after the updates). Added edge tests cover a large observation gap breaking loitering continuity and continuity across midnight. The loitering rule now accepts `max_observation_gap_minutes` (default 5) and resets its dwell episode if observations are farther apart than that threshold.

## Benchmark (captured run)

Run `python scripts/benchmark.py` from the repository root. One local run reported:

| Workload | Elapsed | Throughput |
|---:|---:|---:|
| 288 frames | 0.0027 s | 107,874.5 frames/s |
| 2,880 frames | 0.0265 s | 108,833.3 frames/s |
| 14,400 frames | 0.1042 s | 138,171.3 frames/s |

These are a single local synthetic run, not a production performance guarantee. It measures the in-memory pipeline with simulated descriptions and a SQLite in-memory index; it does not measure real vision inference, persistent-disk I/O, network latency or concurrent clients.
