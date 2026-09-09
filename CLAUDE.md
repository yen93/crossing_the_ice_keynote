# CLAUDE.md

Gmail-triggered pipeline that turns a demo-notes email into a tailored
"Crossing the Ice" keynote proposal deck. Entry point: `python main.py` →
`pipeline.run_once()`. See `as_built.txt` for the full component inventory.

## Run / test
- Run once: `python main.py` (needs a populated `.env`; see `.env.example`).
- Compile check: `python -m py_compile config.py pipeline.py src/*.py`.
- Inspect a deck's shapes/logo placeholders: `python inspect_template.py <id_or_url>`.
- No test suite. Validate logic with small `python -c` snippets against the
  service modules (e.g. `src.logo_service.find_logo_url({...})`).

## LLM provider: OpenAI (not Anthropic)
- As of 2026-09-09 the LLM calls (OCR in `src/ocr_service.py`, slide rewrite in
  `src/slides_rewriter.py`, Fathom matching in `src/fathom_service.py`) use the
  **OpenAI** SDK — `client.chat.completions.create`, model `gpt-4o`, **function
  calling** (`tools=[{type:function,...}]`, read
  `response.choices[0].message.tool_calls[0].function.arguments` via
  `json.loads`). Switched from Anthropic because its credits ran out.
- `ANTHROPIC_API_KEY` still exists in `config.py`/`.env` but is unused (kept for
  easy revert). `OPENAI_API_KEY` is the live one.
- Images are sent as a base64 `image_url`; PDFs as a base64 `file` part.

## The cloud routine is the real deployment — mind these
- The hourly automation (`crossing-the-ice-keynote-automation-hourly`, trigger
  `trig_01SJiDxNiKbNHHtBiUT2je93`) is a **Claude Code cloud routine**. It clones
  this repo at branch **`master`**, writes a `.env` from credentials **embedded
  in the routine's prompt**, and runs `main.py`. Manage it with the `schedule`
  skill / `RemoteTrigger` tool.
- Therefore, to change what the routine actually runs you must **push code to
  `master`** (not just the local working tree) AND, for any credential/env
  change, **edit the routine prompt**. Local `main` and `origin/master` have
  been kept identical — push to both (`git push origin main` then
  `git push origin main:master`).
- The cloud sandbox enforces an **egress allowlist**. External hosts the code
  calls directly (e.g. `api.openai.com`) must be added to the **Default
  environment's** allowed domains in the Claude Code web UI — this is an owner
  action, not settable via the routine API. Symptom when missing: proxy `403
  policy denial`. Note: client-logo / favicon URLs are fetched **server-side by
  Google Slides**, so they never need sandbox egress.

## Supabase dedup gotcha
- `supabase_service.mark_processed` sets `is_processed=true` even on **error**,
  so a failed email is never auto-retried. To reprocess one, reset its row's
  `is_processed=false` in `crossing_the_ice_keynote_proposal_logs` (project
  `aivitcomiywiysrfwqxt`).

## Client logo behaviour
- `logo_service.find_logo_url(ocr_fields)` returns an **unverified** guess: it
  resolves a domain (notes `client_website` > `contact_email` domain >
  org-name slug) and builds candidate URLs (optional logo.dev when
  `LOGODEV_TOKEN` set, else Google favicon). It makes **no network call** — the
  URLs are applied by Slides `replaceImage`. `slides_rewriter` tries each
  candidate until one places. Logo swaps are always flagged **needs-review**.
- Logo placeholders in the template are tagged with alt-text
  `title`/`description` containing `client_logo`; the text-rewrite and logo-swap
  are sent as **separate** batchUpdate calls (a bad logo URL must not roll back
  the text rewrite).

## Secrets / git
- `.env`, the OAuth token, and loose `*.txt` credential files are gitignored —
  never commit real secrets. When committing, stage specific files rather than
  `git add .` to avoid the loose secret files.
- `project_vars.txt` holds Drive folder links and notification recipients (not
  secret).
