# Drone Security Analyst — Project Report

## Problem and prototype approach

The prototype models a docked drone observing a property and turns a scripted one-day scenario into event logs, rule-based alerts, searchable frame records and simple follow-up answers. The dataset uses text descriptions instead of camera pixels. This makes the workflow reproducible and lets the rules, indexing and query components be exercised without a real camera or GPU.

## Assumptions

- One simulated day sampled every five minutes (288 frames).
- Descriptions represent objects, colour and action; the keyword parser is not a detector and may misattribute attributes when multiple objects are described together.
- Security rules are deterministic and thresholds are explicit: Main Gate loitering at night for ten minutes, person in restricted Side Fence/Backyard at night, vehicle presence between 22:00 and 05:00, and drone altitude below five metres.
- Loitering observation continuity is limited to five minutes by default; longer gaps restart dwell.

## Architecture and indexing

Input `Frame`/`Telemetry` objects are passed to the simulated describer. The agent stores frames and detections, emits a log when a proxy object episode starts, and evaluates rule classes. SQLite keeps frame, detection, log and alert records. Queries are deterministic and operate on the index. See `docs/architecture.md` for the pipeline and schema.

## Event handling

Episodes suppress repeated frame-level log/alert spam. Object log identity is currently approximated using label, colour and location; without real tracking IDs, separate objects may be conflated. Loitering resets when the person is absent or observations exceed the continuity gap. The system has edge tests for gap reset and midnight continuity.

## Demonstration scenario and expected behavior

The scripted day contains two blue-truck entry episodes, a person at Main Gate after midnight, a Side Fence/Backyard night intrusion, an after-hours car and a low-altitude drone inspection. The automated end-to-end test checks expected event/alert behavior.

## Verification and scalability

The captured test run passed 40 tests. A local synthetic benchmark measured approximately 115,889 frames/s for 288 frames, 130,917 frames/s for 2,880 frames and 121,952 frames/s for 14,400 frames. These numbers are illustrative only and exclude real vision inference, persistent database I/O and concurrency.

## AI-tool workflow

ChatGPT was used as a code-review and drafting assistant to help inspect the implementation, identify edge cases, propose test additions and draft documentation. The project author should explain in the narrated demo which suggestions they adopted, verify the outputs, and reflect on limitations; the assistant is not the vision engine.

## Limitations and next steps

Replace keyword simulation with a real detector/VLM and tracker; evaluate precision/recall on annotated footage; make sampling configurable; add persistent-store and concurrent-load benchmarks; improve event identity with tracking IDs; and make summarization semantically richer while grounding it in indexed records.
