# The Negotiator — 24h Implementation Plan (4 people)

## Hour-0 decisions (lock these, don't debate later)

**Vertical: moving.** The brief hands you every number you need (5.6x spread, FMCSA 40% stat, 30%-below-market red-flag rule, 13k BBB complaints) — zero research required, and the "Daniel" demo story is pre-written. Verticals must be config-not-code anyway, so you lose nothing by taking the default.

**Demo counterparties: teammates role-playing on live calls.** The brief explicitly allows humans playing distinct counterparts, and explicitly calls agent-to-agent scripted dialogue a weak submission ("stage a screenplay"). Human role-play gives you real friction, burns half the credits, and needs zero extra engineering. Write persona cards (below) so the negotiation styles are distinct and price movement is provable.

**Build text-first, voice-swappable.** Because credits aren't confirmed, the negotiation brain, quote pipeline, red-flag engine, and report must all work with a text LLM loop before any audio exists. Voice is a layer you snap on mid-hackathon.

## Credits contingency (start in hour 0, one owner)

1. One person owns chasing the organizer credit code (Discord/Slack/booth) — check hourly.
2. Meanwhile every teammate makes a **free ElevenLabs account** (~10k credits ≈ roughly 15 min of agent conversation each). Four accounts ≈ ~1 hour of total talk time. Use three for dev, keep one untouched for the demo.
3. Agent creation, prompt config, and tool definitions in the ElevenLabs dashboard are **free** — only conversation minutes burn credits. Do all setup before making a single call.
4. Keep every good recording. Hard fallback demo = full loop in text mode + the recorded voice calls.

**Cost warnings:** agent minutes are your scarce resource — cap test calls at ~2 minutes and know what you're testing before dialing. Skip Twilio/real-business calls unless you're ahead at hour 16 (adds cost, consent/compliance questions, and unpredictability; the brief accepts web calls with role-players).

## Architecture

```
User ── voice interview ──┐
User ── doc upload (photo/PDF) ──┤→ Job Spec JSON ── user confirms
                                  ↓
                        Orchestrator (per-company call sessions)
                                  ↓
        Caller agent (ElevenLabs) with mid-call tools:
          log_quote_item · get_best_bid · log_outcome
                                  ↓
        Quotes DB → red-flag + ranking engine → Report UI
```

**The load-bearing trick is mid-call tool calls.** The caller agent invokes `log_quote_item` and `log_outcome` *during* the conversation (ElevenLabs agent tools/webhooks), so every quote lands structured and itemized — a hard requirement. `get_best_bid` returns the current best competing bid mid-call, so leverage ("I have a binding quote for $1,850 — can you beat it?") is real data, not script. That's what makes price movement emergent, which is the #1 judging criterion.

**Vertical config (`verticals/moving.yaml`):** spec schema (rooms, large items, stairs, long-carry), interview question list, price benchmarks (moveBuddha/FMCSA medians), red-flag rules (>30% below median; refuses itemization; sight-unseen binding quote), negotiation levers. Judges explicitly want swapping verticals to mean swapping this file. Stretch goal: a second skeleton config (auto repair) shown for 10 seconds in the demo.

**Persona cards (3 required styles):** each role-playing teammate gets a hidden price floor, a fee structure, and a concession rule, e.g.:
- *Tough negotiator* — starts $2,400, floor $1,900, drops 10% only if a competing binding quote is cited
- *Lowballer* — quotes $1,100 (triggers the red flag), reveals $400 in stairs/fuel fees only if pressed on itemization
- *Hard-sell upseller* — reasonable base, pushes packing service + insurance, needs firm scope defense
- (*Bonus 4th:* stonewaller — "we don't quote over the phone" → agent must exit with a structured callback commitment)

**Suggested stack:** Next.js frontend · small Node or FastAPI backend · Supabase free tier as the shared DB (teammates run locally against one DB, and Supabase Realtime gives the frontend live call-board updates for free) · Claude/GPT API for the counter-agent in text mode and for document parsing (vision → spec JSON).

## Who builds what

**Person A (frontend-strong):** owns the entire UI — it's a big share of judged surface. Four screens: (1) intake + **spec confirmation** (required step), (2) live call board — one card per company, status, streaming transcript, quote items appearing as tools fire, (3) ranked comparison report — itemized fee table, red-flag badges, recommended deal with plain-language "why" and clickable transcript citations, (4) recordings/transcript viewer. Builds against JSON fixtures from hour 1 so they're never blocked on backend or credits. Also owns demo visual polish.

**Person B (backend/orchestrator):** job-spec + quote JSON schemas (write these in hour 0 — they're the contract everyone codes against), quotes DB, call-session state machine (queued → calling → quoted/declined/callback), red-flag + ranking engine, the three tool endpoints, report generation with transcript citations.

**Person C (conversation design):** the brief says this challenge "is won in call design, not model architecture." System prompts for interviewer/caller/closer, the four required conversation behaviors as concrete artifacts — AI disclosure line ("I'm an AI assistant calling on behalf of a customer…"), "are you a robot?" response, honesty guardrails (never invent inventory or a fake bid — cite only bids in the DB), structured call endings (quote / callback / documented decline, never "around two thousand"). Persona cards. A ~10-case text eval: does the agent extract every fee, catch the lowball red flag, hold the honesty line? Iterates in cheap text mode all day.

**Person D (ElevenLabs + intake):** agent setup in the dashboard, tool wiring to Person B's endpoints, web-call sessions (Twilio only as stretch), voice interview intake agent, and **document intake** — photo of a room or an existing quote PDF → vision model → the *same* spec JSON as the interview (both paths are required). Owns the credit chase.

## Timeline

| Hours | Milestone |
|---|---|
| 0–1 | Lock decisions, scaffold repo, **agree schemas**, create free EL accounts, chase credits |
| 1–6 | Parallel build, text mode. B: DB/API/orchestrator · C: prompts + text negotiation loop vs LLM counter-agent · A: UI on fixtures · D: EL agent config + doc intake |
| **6** | **Checkpoint: full loop runs end-to-end in text** (intake spec → 3 simulated calls → ranked report) |
| 6–12 | Voice on: interview agent live, caller agent logging quotes via tools, first live call vs role-playing teammate, frontend on realtime data |
| 12–16 | The Closer: `get_best_bid` leverage + a renegotiation call, red flags in report, transcript citations |
| 16–20 | Hardening + **record golden calls as backup**: friction tests (interruptions, stonewall, "are you a robot?"), run evals |
| 20–23 | Demo script + video, README, submission. **Feature freeze at 22** |
| 23–24 | Buffer |

## Demo script (~3 min) → success-criteria mapping

1. 20s of Daniel's problem (brief's own numbers) → *provable pain*
2. Voice interview clip + photo upload producing the identical spec, user confirms → *both intake paths, one spec*
3. Live call board: 3 calls vs 3 personas, quote items streaming in → *3 negotiation styles, structured quotes*
4. The money moment, played aloud: agent cites the $1,850 competing bid, tough negotiator drops from $2,400 to $1,950 → *price moves from leverage* — replay the "are you a robot?" clip here too
5. Report: lowballer flagged (-38% + hidden fees), recommended deal explained with transcript citation → *ranked, evidence-backed*

## Scope traps — refuse these

- Real Twilio calls to real businesses (compliance + unpredictability; only if everything else is done)
- Agent-to-agent audio bridging (fiddly, double credits, and reads as "screenplay")
- Real Google Places integration — a mocked call list + one sentence on where it comes from satisfies the brief
- A second working vertical — show the config file, don't build it
- Auth, deployment, mobile. Localhost + a good screen recording wins.
