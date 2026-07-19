# ElevenLabs Dashboard Setup (phone-friendly, Alex's lane)

> **STATUS: configured for the current public backend.** The existing agent IDs are in [created.json](created.json), and `configure_live.py` has pointed their tools at `https://flail-poker-decency.ngrok-free.dev`. Re-run the script only when the public URL changes.

```bash
BACKEND_URL=https://flail-poker-decency.ngrok-free.dev .venv/bin/python elevenlabs/configure_live.py --apply
```
>
> **Person D:** the four tools point at placeholder URLs (`backend-placeholder.negotiator.example`) — update each tool's URL via dashboard or API once the backend is deployed. Voice is the stock demo voice; pick better ones in the dashboard (free).

All of this is **free to configure** — only conversation minutes burn credits. Do the full setup before dialing anything.

## Agent 1: The Interviewer (intake)

1. ElevenLabs dashboard → **Agents** → Create agent → name it `negotiator-interviewer`.
2. **First message:** "Hi! I’m your cleaning assistant. I’ll ask a few questions so cleaners can give you a comparable quote — ready?"
3. **System prompt:** paste [prompts/interviewer.md](../prompts/interviewer.md), then append the `interview_questions` list from [verticals/cleaning.yaml](../verticals/cleaning.yaml).
4. **Tool:** `save_job_spec` (see [tools.md](tools.md)) → Person D wires the webhook URL.
5. Voice: pick something warm/neutral. Keep model settings default (latency matters more than quality here).

## Agent 2: The Caller (negotiator)

1. Create agent → `negotiator-caller`.
2. **First message:** leave EMPTY / set to wait — the counterparty answers the phone first. If the platform requires one, use: "Hi, is this {{company_name}}?"
3. **System prompt:** paste [prompts/caller.md](../prompts/caller.md). Use dynamic variables for `{company_name}`, `{spec_id}`, `{call_id}`, and `{job_spec_json}`.
4. **Tools:** `log_quote_item`, `get_best_bid`, `log_outcome` (see [tools.md](tools.md)).
5. Turn-taking: enable interruptions (barge-in) — the brief explicitly judges this.

## Testing discipline (credits!)

- Iterate prompts in **text mode first**: `python3 sim/negotiate.py personas/tough-negotiator.md` (see [sim/README.md](../sim/README.md)). Only dial to verify voice behavior.
- One ~60s sanity call after setup to confirm the account/voice pipeline works. Then stop until the backend is deployed (hour-6 checkpoint).
- Tool calls fail until Person B's endpoints are publicly reachable — don't burn minutes testing tools against localhost.
- Keep every good recording — demo backup material.

## Caller handoff (required for a real call)

1. The interviewer’s `save_job_spec` tool returns the `spec_id`.
2. Confirm it with `PATCH /specs/{spec_id}/confirm`, then fetch `GET /calls?spec_id={spec_id}`.
3. For each company, call `POST /calls/start` with the `spec_id` and `company_id`. Pass the returned `call_id` to the caller agent as a dynamic variable, alongside `spec_id`, `company_name`, and `job_spec_json` (the confirmed spec JSON).
4. The caller can now log line items and the outcome; the closer may use `get_best_bid` after another completed quote exists.
