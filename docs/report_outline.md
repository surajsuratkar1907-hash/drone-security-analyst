# Report outline (PDF)

The report carries equal weight with the code. Use this structure, and fill each section with your own reasoning.

1. **Problem and approach.** Restate the problem in your own words. Explain the simulation
   choice and why it is reasonable for a prototype.
2. **Assumptions.** Dataset (one simulated day, 5-minute sampling), what the simulated describer
   can and cannot do, and the alert thresholds you picked.
3. **Architecture.** Include the diagrams from `docs/architecture.md`. Explain the episode model
   and why rules are deterministic code, not prompts.
4. **Tool choices.** Why SQLite, why keyword-based describer for now, and what you would use
   instead in production: CLIP vs. BLIP vs. a detector, a vector index, and so on.
5. **Indexing (cross-domain).** Explain frame-by-frame storage, the schema, and what you
   learned while building it. Show example queries and their output.
6. **Results.** Show logs, alerts and query output from `python -m drone_agent run`. Reference
   your demo video timestamps.
7. **Testing.** Summarise `docs/testing.md` and the end-to-end result.
8. **AI tools.** Be specific: which tool, what it generated, what you changed, what it got wrong.
   Reviewers want to see your judgement, not just that you used AI.
9. **Limitations and next steps.** What you would build with more time (video summarisation,
   a stronger VLM, embeddings-based frame search, learned baselines).
