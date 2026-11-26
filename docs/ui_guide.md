# Dashboard guide (for the demo video)

## Start it

```bash
cd drone-security-agent
python -m drone_agent ui          # builds the index if needed, then serves http://127.0.0.1:8000
```

Open http://127.0.0.1:8000 in Chrome or Edge. Press Ctrl+C in the terminal to stop.

## What each part shows

| Area | What it means |
|---|---|
| **Stats bar** (top) | Frames processed, events logged, alerts raised, blue-truck entries |
| **Drone camera** (left, top) | The simulated frame: description, time, location, altitude, detected objects. Turns red and pulses during a high-severity alert. |
| **Patrol map** (left, bottom) | The six zones. The green dot shows the drone's current zone. Dashed zones are restricted. |
| **Live event log** (right) | Events as they happen, newest first. An event is logged when an object first appears. |
| **Alerts** (right, bottom) | Alerts raised so far, colour-coded (red = high, amber = medium). |
| **Timeline** (bottom) | All 288 frames. Blue = object seen, red = alert. Click any cell to jump there. |
| **Ask the index** (bottom right) | Type a question or click a preset. The answer comes from the database. |

## Suggested recording script (about 3 minutes)

1. **Intro (20 s).** "This is a Drone Security Analyst for a docked drone. It watches the property all day, logs what it sees, raises alerts, and makes the footage searchable."
2. **Pipeline (30 s).** Show the terminal running `python -m drone_agent run`, then the stats bar. Explain telemetry and frames.
3. **Play at Normal speed (60 s).** Press Play. Narrate:
   - 00:00: person at the main gate. Log entry.
   - 00:10: the loitering alert fires and the camera turns red.
   - 07:30–08:00: blue F150 approaches, enters, parks.
   - 16:00: low-altitude safety alert.
   - 22:05 and 22:20: night intrusion alerts at the side fence and backyard.
   - 23:30: car at the gate after hours.
4. **Timeline (15 s).** Click a red cell to jump to an alert. Show how the timeline reveals the whole day.
5. **Ask (40 s).** Click "Entries" (answer: 2), "Objects", and "Alerts". Type "show all truck events".
6. **Tests and close (20 s).** Run `python -m pytest -v` in the terminal. Say what the tests cover.

Use the **Slow** speed if you need more time to explain a moment. Use Space to pause or play,
and the arrow keys to step frame by frame.

## Tips for recording

- Make the browser window full screen and zoom to 110–125% so the text reads on video.
- Record your voiceover while you narrate. Videos without a voiceover are marked incorrect.
- Keep the terminal visible for the first and last parts of the demo.
