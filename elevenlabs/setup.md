# ElevenLabs Dashboard Setup (phone-friendly, Alex's lane)

> **STATUS: DONE PROGRAMMATICALLY (2026-07-18).** `create_agents.py` created both agents and all four webhook tools via the API — IDs in [created.json](created.json). Talk to the caller agent: `https://elevenlabs.io/app/talk-to?agent_id=<agent_caller id>`. The steps below remain as reference for editing in the dashboard.
>
> **Person D:** the four tools point at placeholder URLs (`backend-placeholder.negotiator.example`) — update each tool's URL via dashboard or API once the backend is deployed. Voice is the stock demo voice; pick better ones in the dashboard (free).

All of this is **free to configure** — only conversation minutes burn credits. Do the full setup before dialing anything.

## Agent 1: The Interviewer (intake)

1. ElevenLabs dashboard → **Agents** → Create agent → name it `negotiator-interviewer`.
2. **First message:** "Hi! I'm your moving assistant. I'll ask a few quick questions so movers can give you a real, binding quote — takes about two minutes. Ready?"
3. **System prompt:** paste [prompts/interviewer.md](../prompts/interviewer.md), then append the `interview_questions` list from [verticals/moving.yaml](../verticals/moving.yaml).
4. **Tool:** `save_job_spec` (see [tools.md](tools.md)) → Person D wires the webhook URL.
5. Voice: pick something warm/neutral. Keep model settings default (latency matters more than quality here).

## Agent 2: The Caller (negotiator)

1. Create agent → `negotiator-caller`.
2. **First message:** leave EMPTY / set to wait — the counterparty answers the phone first. If the platform requires one, use: "Hi, is this {{company_name}}?"
3. **System prompt:** paste [prompts/caller.md](../prompts/caller.md). Use dynamic variables for `{company_name}`, `{origin_city}`, `{destination_city}`, `{move_date}`, and inject the confirmed job spec JSON into the prompt per call (Person D passes these as conversation overrides / dynamic variables).
4. **Tools:** `log_quote_item`, `get_best_bid`, `log_outcome` (see [tools.md](tools.md)).
5. Turn-taking: enable interruptions (barge-in) — the brief explicitly judges this.

## Testing discipline (credits!)

- Iterate prompts in **text mode first**: `python3 sim/negotiate.py personas/tough-negotiator.md` (see [sim/README.md](../sim/README.md)). Only dial to verify voice behavior.
- One ~60s sanity call after setup to confirm the account/voice pipeline works. Then stop until the backend is deployed (hour-6 checkpoint).
- Tool calls fail until Person B's endpoints are publicly reachable — don't burn minutes testing tools against localhost.
- Keep every good recording — demo backup material.
