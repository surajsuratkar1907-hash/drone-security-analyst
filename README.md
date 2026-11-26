# Drone Security Analyst Agent (prototype)

A reproducible offline prototype for a docked-drone property-security workflow. It processes **simulated frame descriptions** plus telemetry, logs object episodes, evaluates deterministic security/safety rules, indexes records in SQLite, and answers follow-up queries through a CLI and local dashboard.

> Scope note: The assignment explicitly permits simulated video frames with text descriptions. This project implements that simulation; its describer is a deterministic keyword parser, not pixel-based vision or a deployed VLM.

## Quick start

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python data/generate_frames.py   # optional; regenerates the 288-frame scenario
python -m drone_agent run
python -m drone_agent ask "summarize the day"
python -m drone_agent ask "any alerts?"
python -m drone_agent query --object truck --color blue
python -m drone_agent ui         # local dashboard at http://127.0.0.1:8000
python -m pytest -v
python scripts/benchmark.py
```

## Architecture and design decisions

`Frame` and `Telemetry` are the input contract. `SimulatedVisionDescriber` converts text to detections; the agent indexes frame/detection rows, logs event episodes, then evaluates rules. `FrameIndex` stores frame, detection, event-log and alert rows in SQLite. `qa.py` answers deterministic questions from stored records.

- **Simulation:** keyword-based, not pixel-based vision. The frame text is the visual-analysis input, as permitted by the assignment.
- **Episode logging:** uses `(label, colour, location)` as a proxy identity; it cannot reliably distinguish two same-class objects at the same location.
- **Loitering:** requires continuous observations; a configurable observation gap breaks continuity (default 5 minutes).
- **Alerts:** loitering at Main Gate at night (10 minutes), night intrusion at Side Fence/Backyard, after-hours vehicles (22:00–05:00), and altitude below 5 m.
- **Q&A:** deterministic, offline and traceable; not a generative natural-language model.
- **SQLite:** lightweight local index without an external database service.

See `docs/architecture.md`, `docs/feature_spec.md`, `docs/testing.md`, `docs/acceptance_matrix.md` and `docs/report.md`.

## Scenario

The committed dataset simulates one day at five-minute intervals (288 frames), including two blue-truck entry episodes, night loitering, restricted-zone intrusion, an after-hours car and a low-altitude safety event. Scenario expectations are tested end-to-end.

## Tests and scalability

```bash
python -m pytest -v
python scripts/benchmark.py
```

The historical test run reported 40 passing tests. Rerun tests after any subsequent changes. Benchmark results are machine-dependent and measure a synthetic pipeline with simulated descriptions; they do not measure real vision inference, camera decoding, network latency, persistent-disk I/O or concurrent clients. See `docs/testing.md` for test scope and caveats.

## AI-assisted development

ChatGPT was used as a coding/review assistant to inspect the project, suggest edge-case tests and improvements, and help draft documentation. The author should review, validate and explain adopted suggestions. The runtime describer remains a deterministic simulation, not an integrated AI vision model.

## Limitations

- No real video ingestion, detector, tracking IDs or pixel-based verification.
- Simulated sampling may miss short-duration events.
- Proxy event identity can merge separate entities.
- SQLite is suitable for this prototype but deployment needs retention, concurrency, access-control and monitoring design.
- Q&A is deterministic; a grounded LLM could be added later.
- Alerts are locally stored/displayed; external notifications are not implemented.
