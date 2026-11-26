# Drone Security Analyst Agent (prototype)

A reproducible offline prototype for a drone-based property-security monitoring workflow. It processes **simulated frame descriptions** plus telemetry, logs object episodes, evaluates deterministic security/safety rules, indexes records in SQLite, and answers basic follow-up queries.

## Quick start

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python data/generate_frames.py   # optional; regenerates the 288-frame scenario
python -m drone_agent run
python -m drone_agent ask "summarize the day"
python -m drone_agent ask "any alerts?"
python -m drone_agent query --object truck --color blue
python -m pytest -v
```

## Architecture

`Frame` and `Telemetry` are the input contract. `SimulatedVisionDescriber` converts text into detections; the agent indexes frame/detection rows, tracks object-log episodes, then evaluates each rule. `FrameIndex` stores frame, detection, event-log and alert rows in SQLite. `qa.py` answers structured questions from those stored records.

- **Vision simulation:** keyword-based, not pixel-based computer vision. Colour/action are inferred from the whole description and can be ambiguous for multiple objects.
- **Episode logging:** currently uses `(label, colour, location)` as a proxy identity; it cannot reliably distinguish two same-class objects at the same location.
- **Loitering:** requires continuous observations; a configurable observation gap breaks continuity (default 5 minutes).
- **Alerts:** loitering at Main Gate at night (10 minutes), night intrusion at Side Fence/Backyard, after-hours vehicles (22:00–05:00), and altitude below 5 m.
- **Q&A:** deterministic, offline and traceable; not a generative natural-language model. Summary now includes alert time/rule/severity/location details.

See `docs/architecture.md`, `docs/feature_spec.md` and `docs/testing.md`.

## Demo scenario

The committed dataset simulates a day at 5-minute intervals (288 frames), including two blue-truck entry episodes, night loitering, restricted-zone intrusion, an after-hours car, and a low-altitude safety event. Scenario expectations are tested end-to-end.

## Tests and scalability

```bash
python -m pytest -v
python scripts/benchmark.py
```

The suite currently contains 40 tests. Benchmark output is machine-dependent; `scripts/benchmark.py` reports measured throughput for 288, 2,880 and 14,400 simulated frames. See `docs/testing.md` for the captured run and caveats.

## AI-tool use

ChatGPT was used as a coding/review assistant to inspect the project, suggest edge-case tests and improvements, and help draft documentation/report material. All changes and claims should be reviewed by the project author; the vision component remains a deterministic simulation, not an AI vision model. The author should add their own narration/demo recording and reflect on suggestions they accepted or rejected in their submission video.

## Limitations and next steps

- No real video ingestion, detector, tracking IDs or pixel-based verification.
- Simulated sampling may miss short-duration events; cadence and data quality are important.
- Proxy event identity can merge separate entities; a real tracker would supply stable IDs.
- SQLite is suitable for this prototype but deployment needs retention, concurrency, access-control and monitoring design.
- Q&A summarization is deterministic; a language model could generate richer narratives grounded in retrieved records, with citations and guardrails.
