# Drone Security Analyst — Assignment Report

## 1. Problem and proposed value

The prototype demonstrates a docked-drone monitoring workflow for a property owner: turn a day of simulated observations and telemetry into contextual event logs, rule-based security/safety alerts, searchable frame records, and a daily summary.

## 2. Scope and assumptions

- The prototype uses simulated frame descriptions and telemetry as permitted by the assignment.
- The scenario represents one day sampled every five minutes (288 frames).
- Descriptions are text input to a deterministic keyword describer. This is a simulation of the visual-analysis boundary, not pixel-level inference or a deployed camera pipeline.
- Telemetry includes time, location and altitude.
- Rules are deterministic and configurable in code: night-time Main Gate loitering, night-time person intrusion in Side Fence/Backyard, after-hours vehicles (22:00–05:00), and altitude below 5 m.
- Loitering requires observations to remain continuous within a configurable maximum gap; the default is five minutes and the dwell threshold is ten minutes.

## 3. Architecture

Frame descriptions and telemetry enter the agent. The simulated describer creates detections. The agent stores frames and detections in SQLite, logs object episodes rather than every repeated frame, evaluates alert rules, and stores alerts. The CLI and dashboard expose summaries, questions and index queries. See `docs/architecture.md` for pipeline, sequence and schema diagrams.

## 4. Implementation choices

- Python: concise implementation, readable testability and standard-library SQLite support.
- SQLite: simple durable relational index for this small prototype; no external database service is required.
- Deterministic keyword describer: keeps the assignment's simulated-frame scenario reproducible and makes tests independent of model downloads or API keys. It is not a real VLM.
- Stateful rule classes: each rule retains episode state to avoid repeated alerts during the same continuous event.
- Deterministic Q&A: responses are derived from indexed records and can be traced to stored data.
- Local dashboard and CLI: provide visible operator interaction and query access without requiring cloud services.

## 5. Expected scenario results

The committed scenario and tests cover a blue truck entering in two distinct episodes, a person at the Main Gate after midnight, restricted-zone night intrusion, an after-hours vehicle and a low-altitude safety event. The expected timestamps and behavior are asserted in the test suite; the report does not claim that the scenario was evaluated on real video.

## 6. Validation

The author reported a local run of `python -m pytest -v` with 40 passing tests in 1.49 seconds before this report refresh. Tests cover describer behavior, rules and episode transitions, indexing, CLI/dashboard endpoints, Q&A, data consistency, and end-to-end behavior. This captured result is historical and must not be represented as a test run of any later edits unless tests are rerun.

## 7. Scalability experiment and interpretation

`scripts/benchmark.py` uses generated/repeated frame objects and the in-memory index to measure synthetic pipeline throughput at multiple workload sizes. Results depend on the machine and Python environment. They are useful for a basic processing-loop comparison only and exclude image inference, real camera decoding, persistent-disk I/O, network latency and concurrent users. They are not production or real-time vision performance measurements.

## 8. AI-assisted workflow

ChatGPT was used as a code-review and development assistant to inspect the project, suggest edge-case tests and improvements, and help draft documentation. The project author remains responsible for understanding, reviewing, validating and explaining adopted changes. The running describer is a deterministic simulation and should not be described as an integrated VLM.

## 9. Limitations

- No real video file decoding, camera stream or pixel-based model inference.
- Keyword parsing can miss objects or misattribute colour/action when multiple objects are described together.
- Episode identity uses a label/colour/location proxy and can conflate distinct objects.
- The sample is sparse at five-minute intervals and may miss short events.
- Rules are illustrative and have not been tuned or validated against real property footage.
- Synthetic benchmark excludes major production costs and concurrency.
- Alerts are stored and surfaced locally; external notification delivery is not implemented.

## 10. Future work

A next iteration could add configurable sampling, real video ingestion and a detector/VLM, tracking IDs, annotated-clip evaluation, precision/recall measurements, alert delivery integrations, persistent/concurrent benchmark workloads, and richer natural-language summaries grounded in indexed records.
