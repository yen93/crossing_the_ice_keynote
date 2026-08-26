---
name: run-crossing-the-ice-keynote-pipeline
description: Run the Crossing the Ice Keynote proposal automation pipeline once, locally, against real Gmail/Drive/Slides/Supabase.
---

Run the pipeline once:

```
python main.py
```

This scans Gmail for unprocessed demo-notes emails matching
`config.GMAIL_TRIGGER_QUERY`, and for each one: OCRs the attachment, looks up
the single master "Crossing the Ice Keynote" template, duplicates it into the
client's Drive folder, rewrites the client-specific text and swaps the client
logo, runs a pre-send QA check, sends Gmail notifications, and logs the
outcome to the `crossing_the_ice_keynote_proposal_logs` Supabase table.

Safe to re-run: Supabase dedup means an already-processed email is skipped.

Requires `.env` to be populated (see `.env.example`) — either via
`python oauth_setup.py` for a fresh Google OAuth consent, or by reusing the
credential values already present in this project's `.env`.
