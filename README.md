# The Negotiator

Voice agents that call, compare, and negotiate — ElevenLabs challenge, Hack-Nation 6th Global AI Hackathon. The shipped vertical is **home cleaning**.

## Team roles

| Who | Role | Owns |
|-----|------|------|
| A (frontend) | Dashboard | `frontend/` — intake/spec confirmation, live call board, ranked report |
| B | Backend/orchestrator | `backend/`, tool endpoints (`log_quote_item`, `get_best_bid`, `log_outcome`), red-flag + ranking engine |
| Alex (phone-based) | Conversation design + ElevenLabs config | `prompts/`, `personas/`, `verticals/`, `evals/`, `demo/`, `docs/`, EL dashboard, credit chase |
| D | Voice integration + doc intake | EL tool wiring, web-call sessions, photo/PDF → job spec |

## Hard rules (agreed hour 0)

1. **Prompts are files.** Agents load system prompts from `prompts/` and config from `verticals/` — never hardcoded. Alex iterates on these from a phone; a merged PR changes agent behavior with zero code.
2. **Schemas are the contract.** `schemas/job_spec.schema.json` and `schemas/quote.schema.json` — both intake paths produce the former, every call produces exactly one of the latter.
3. **Backend must be publicly reachable** (deploy or ngrok) before ElevenLabs tool calls can work. Localhost-only blocks voice testing.
4. **Voice minutes are the scarce resource.** Iterate in text mode against `personas/` + `evals/golden-calls.md` first; dial only to verify.

## Repo layout

```
prompts/      system prompts for interviewer & caller agents
personas/     role-player cards (hidden floors + concession rules)
verticals/    per-vertical config — swap file, not code
schemas/      job spec + quote JSON schemas (the contract)
evals/        golden-call checklist, run before burning minutes
demo/         demo script + success-criteria mapping
docs/         the four conversation requirements (judge-facing)
backend/      orchestrator, tool endpoints, ranking (B)
frontend/     dashboard (A)
```

## Run the integrated demo

1. Copy `.env.example` to `.env` and add the existing shared Supabase URL/service key plus OpenAI key.
2. In one terminal: `python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt && .venv/bin/uvicorn backend.main:app --reload --port 8000`.
3. In `frontend/the-negotiator`, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` and leave `NEXT_PUBLIC_USE_MOCKS` unset (mocks are opt-in), then run `npm install && npm run dev`.
4. Upload a PDF or image → review/confirm the generated spec → use the call board and report. Voice calls require a public backend URL and the corresponding ElevenLabs webhook updates in `elevenlabs/tools.md`.

## Working from a phone (Alex)

Sessions run on [claude.ai/code](https://claude.ai/code) against this repo (needs the Claude GitHub app connected). Kickoff prompt to paste at the start of each session:

> I'm working from my phone on the-negotiator repo (ElevenLabs "The Negotiator" hackathon). I own conversation design: prompts/, personas/, verticals/cleaning.yaml, evals/, demo/, docs/. The prompts are loaded as files by the agents, so my changes ship behavior. Keep the cleaning vertical consistent and open a PR when done. This session's task: [TASK]
