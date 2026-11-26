# Drone Security Analyst Agent (prototype)

A prototype agent for a docked drone that watches a fixed property. It takes simulated
telemetry (time, location, altitude) and simulated video frames (text descriptions), then:

1. **Describes** each frame and detects objects (trucks, vans, cars, people, animals) with their colour and action.
2. **Logs** an event when an object first appears, for example `Blue truck spotted at Garage, 12:00.`
3. **Alerts** when a predefined rule fires, for example `Person loitering at Main Gate, 00:10`.
4. **Indexes** every frame in SQLite by time, location and object, so you can query it.
5. **Answers** follow-up questions such as "what objects were in the video?" and "how many times did a blue truck enter?"

Only the Python standard library is needed to run the agent. pytest is needed only for the tests.

## Quick start

Requires Python 3.10 or newer.

```bash
cd drone-security-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                       # installs pytest only

python data/generate_frames.py      # optional: regenerates data/frames.json (288 frames)
python -m drone_agent run           # processes all frames, prints logs and alerts, builds data/index.db
```

Queries against the index:

```bash
python -m drone_agent query --object truck --color blue     # frames, plus entry count
python -m drone_agent query --object truck --logs           # event log for trucks
python -m drone_agent query --start 22:00 --end 23:59       # every frame in a time window
python -m drone_agent query --object person --location "Side Fence"
python -m drone_agent ask "what objects were in the video?"
python -m drone_agent ask "show all truck events"
python -m drone_agent ask "how many times did a blue truck enter today?"
python -m drone_agent ask "any alerts?"
python -m drone_agent summary
```

Run the tests:

```bash
python -m pytest -v
```

## Project layout

```
drone-security-agent/
├── data/
│   ├── generate_frames.py   # builds the one-day scenario (288 frames, scripted events)
│   └── frames.json          # generated dataset (committed so the demo runs without regenerating)
├── drone_agent/
│   ├── models.py            # Telemetry, Frame, Detection, Alert, time helpers, JSON loader
│   ├── describer.py         # simulated vision model: frame text -> detections
│   ├── rules.py             # alert rules (loitering, night intrusion, after-hours vehicle, low altitude)
│   ├── agent.py             # per-frame pipeline: describe -> index -> log -> rules -> alerts
│   ├── indexer.py           # SQLite frame index and query API
│   ├── qa.py                # follow-up Q&A and one-sentence day summary
│   └── cli.py               # command-line interface
├── tests/                   # unit, integration and data-consistency tests
├── docs/
│   ├── feature_spec.md      # value to property owners and requirements
│   ├── architecture.md      # pipeline, storage and alert design, with diagrams
│   ├── testing.md           # test strategy, cases and results
│   └── report_outline.md    # outline for the PDF report
├── pytest.ini
└── requirements.txt
```

## Design decisions

- **Simulated vision, real pipeline.** The brief allows simulated frames. The describer is a
  single class with a keyword vocabulary, so it can be swapped for a real VLM (for example
  BLIP-2 or LLaVA for captions, or YOLO plus CLIP for detections) without changing the rules,
  index or CLI. The output type (`Detection`) is the contract between them.
- **Rules are plain Python classes, not prompts.** Security alerts need to be deterministic,
  testable and explainable. An LLM is a poor fit for "is it between 22:00 and 05:00?". Each rule
  inherits from `Rule` and has one job.
- **Episodes, not frames.** A truck approaching the gate over three frames is one event, not
  three. `EpisodeTracker` makes logs and alerts fire once when a condition starts, and again only
  after it has stopped. Without this, a 5-minute frame interval would flood the log.
- **SQLite for the index.** It ships with Python, needs no server, and handles this data size
  easily. Frames, detections, logs and alerts are separate tables. Detections are indexed by
  label, so "all truck frames" stays fast as the data grows. The schema maps directly to a
  larger store (Postgres, or a vector store for image embeddings).
- **Rule-based Q&A.** The follow-up questions are answered from database rows, so every answer
  can be traced and tested. An LLM could sit in front of `qa.py` to handle free-form phrasing.
  The bonus "summary" and "follow-up" features are both implemented this way.
- **Frame-level sampling every 5 minutes.** This keeps the dataset readable (288 frames for one
  day). Real systems sample at several frames per second. `INTERVAL_MIN` in
  `generate_frames.py` changes the density, and the rules work in minutes, so they do not
  depend on the interval.

## Alert rules

| Rule | Fires when | Severity | Example message |
|---|---|---|---|
| `loitering` | A person stays in *Main Gate* at night for ≥ 10 min | high | `Person loitering at Main Gate, 00:10` |
| `night_intrusion` | A person is in a restricted zone (*Side Fence*, *Backyard*) at night | high | `Person in restricted area at Side Fence at night, 22:05` |
| `after_hours_vehicle` | A car, truck or van is present at night (22:00–05:00) | medium | `Car seen at Main Gate after hours, 23:30` |
| `low_altitude` | Drone altitude is below 5 m (safety rule) | high | `Drone altitude 3.0 m at Garage is below the 5.0 m safety minimum, 16:00` |

Rule thresholds are constructor arguments (`LoiteringRule(dwell_minutes=...)`, and so on), so
`default_rules()` can be changed without touching the agent.

## What the demo day contains

`data/frames.json` is one simulated day. It includes:

- A blue Ford F150 that **enters the main gate twice** (07:40 and 17:40).
- A person at the main gate just after midnight, which triggers the loitering alert.
- A person climbing the side fence at 22:05, then walking into the backyard at 22:20.
- A car idling at the gate at 23:30.
- A drone altitude dip to 3 m at 16:00.
- Routine patrol frames, so quiet periods produce no false alerts.

## Testing

36 tests cover the describer, each rule (including the "no alert" cases), the index queries,
entry counting, the full-day pipeline and the Q&A. See `docs/testing.md`.

## AI tools used

> **Fill this in honestly before submitting.** The assessment asks how AI tools changed your
> workflow, and examples are useful to reviewers. Replace each bracketed line with what
> actually happened, for example which tool you used, what it generated, and what you changed.

- **[Tool name, e.g. Claude Code / Cursor / Windsurf]:** [what it generated, e.g. first draft of `indexer.py` schema]. I changed [what you changed and why].
- **[Tool name]:** [e.g. used to validate the architecture; suggested the episode-tracking idea, which I adapted into `EpisodeTracker`].
- **[Tool name]:** [e.g. generated the initial test cases; I rewrote the expected alert times after checking them against the data].

## Limitations and what I would improve with more time

- The vision step is simulated. A real VLM would make frame descriptions less predictable.
  Colour and action are assigned per description, so a frame with two objects of different
  colours is not handled correctly.
- Frames are sampled every 5 minutes. Fast events (someone running past the camera in 10 seconds)
  would be missed. The sampling rate should be an explicit configuration choice.
- The index stores text descriptions, not image embeddings. Next steps would be to store
  CLIP embeddings per frame in a vector index (FAISS or pgvector) and add "find frames like this
  image" search.
- Rules use fixed thresholds. Learned baselines (typical traffic per hour) would reduce false alerts.
- Video summarisation is not implemented as a model call. The current summary is a deterministic
  count over the index.
