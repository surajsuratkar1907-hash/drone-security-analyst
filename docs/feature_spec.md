# Feature spec: Drone Security Analyst Agent

## Value to the property owner

A docked drone patrols the property every day. Owners cannot watch the feeds all day, and the
footage holds little value if nobody can find the moment that matters. This agent watches the
feed for them. It records what came and went (vehicles, people, animals), raises an alert when
something needs attention now (someone loitering at the gate at midnight), and makes the whole
day searchable ("show all truck events", "how many times did the blue truck enter?").

## Key requirements

1. **R1: Log every object event with context.** Each time a new object appears (or a new
   episode starts), record what it is, its colour, what it is doing, where, and when. An object
   that stays in view for several frames produces one event, not one per frame.
2. **R2: Raise rule-based alerts in near real time.** Alerts fire for defined risks: a person
   loitering at the gate at night, a person in a restricted zone at night, a vehicle after hours,
   and an unsafe drone altitude. Each alert names the time and place. Each alert fires once per
   episode.
3. **R3: Make the day searchable by time, place and object.** Every frame is stored with its
   timestamp and telemetry. Owners and staff can ask for frames or events by object, colour,
   place or time window, and ask follow-up questions in plain language.

## Out of scope for the prototype

- Live camera or drone integration (the prototype uses simulated frames).
- Face or licence-plate recognition.
- Multi-drone or multi-camera fusion.
- Notifications (SMS, push). Alerts are printed and stored in the index.
