# App with OpenAI Integration

## Purpose

A minimal web application that accepts user text and performs one of four OpenAI-powered operations: Summarize, Rephrase (tone-controlled), Extract JSON, Classify sentiment. The app must expose a single backend endpoint that calls OpenAI and a simple frontend to exercise it.

## Deliverables

1. Working web app (frontend + backend).
2. Source code in a repo with a short README.md describing setup and run commands.
3. .env.example showing required environment variables.
4. Light automated checks (unit or contract tests) for the backend endpoint.
5. A short sample input file (sample.txt) for manual verification.

## Requirements

### Functional

- Users can paste text (1–5000 chars).
- Users choose one Mode: summarize, rephrase, extract_json, classify.
- If Mode = rephrase, users must choose Tone: casual | professional | friendly.
- On submit, the app calls your backend (not OpenAI directly from the browser).
- The result is displayed in a result panel.
    - For extract_json, render pretty-printed JSON.
- Show token usage returned by OpenAI: prompt, completion, total.
- Provide a “Copy result” button.

### Non-Functional

- Keep the OpenAI API key on the server only.
- Handle errors with human-readable messages (no stack traces in the UI).
- No external databases required.

### UI Requirements

- Single-page layout.
- Controls:
    - Mode (select)
    - Tone (select, visible only when Mode = rephrase)
    - Text area (paste input)
    - Run button
    - Copy result button
- Result panel with monospaced rendering for JSON mode.
- Small footer line showing token usage.

### Testing (minimal)

- Provide automated tests that assert:
    - summarize with valid input returns 200 and non-empty result.
    - rephrase without tone returns 400.
    - classify returns one of the three allowed labels.
    - extract_json returns valid JSON with all required keys.
    - Rate limit path returns 429 after threshold (can be a lowered threshold in test).

### Out of Scope

- User auth.
- Persistent storage.
- Cloud deployment.

## Acceptance Criteria (Pass/Fail)

- All Mode specs met exactly.
- Token usage visible in UI.
- .env.example present; app runs locally with documented commands.
- Tests pass locally.
- No API key present in client code or devtools network traces.

## Submission

- Repo URL with instructions.
- Include two screenshots in the repo:
    - screenshot_ui.png (app with controls/results)
    - screenshot_json.png (valid extract_json output shown)
