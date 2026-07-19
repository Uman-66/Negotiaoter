# Text-mode negotiation simulator

Tests the caller prompt against the persona cards **without burning ElevenLabs minutes**. The caller is an OpenAI agent with the same three tools the voice agent has (`log_quote_item`, `get_best_bid`, `log_outcome`); the counterparty is a second model playing the persona card, hidden policy and all.

We run on **OpenAI** because that's where the hackathon credits are. Defaults: caller = `gpt-4.1` (strong tool calling, and the closest match to what the ElevenLabs agent runs in production), persona = `gpt-4o-mini`.

## Setup (once)

```bash
python3 -m pip install --user openai
# OPENAI_API_KEY is read from the repo-root .env automatically (gitignored)
```

## Run

```bash
cd ~/HackNation_Negotiator
python3 sim/negotiate.py personas/tough-negotiator.md
python3 sim/negotiate.py personas/lowballer.md
python3 sim/negotiate.py personas/upseller.md
python3 sim/negotiate.py personas/stonewaller.md
```

Run order matters: quotes persist in `sim/quotes.json`, so later runs have real leverage for `get_best_bid` — that's how you rehearse the demo's "can you beat $X?" moment. Delete `sim/quotes.json` to reset the market.

Each run prints the live dialogue, an eval summary (outcome, price movement, red flags, disclosure check, cost), and writes a full transcript + structured record to `sim/runs/`.

## Cost

A full run is **$0.03–0.05**. The whole 4-persona sweep is under $0.20. Override models with `CALLER_MODEL=` / `PERSONA_MODEL=` env vars.

## Verified results (first live sweep, 2026-07-18)

| Run | Result |
|---|---|
| tough-negotiator (cold) | Itemization extracted under pushback, disclosure held — but no negotiation attempt → **prompt fixed** (negotiation now mandatory) |
| lowballer | Hidden $250 stairs fee extracted ($1,100 → real $1,350), lowball red flag fired (36% below market) |
| upseller | **Price moved $2,000 → $1,850** on cited real leverage; upsell declined; refused to book |
| tough-negotiator (leverage) | **Price moved $2,400 → $2,160** + $200 fuel waiver for weekday, per hidden concession rule |

Known gaps to iterate on: lowballer's second hidden fee ($150 fuel/materials) was not extracted, and his cash-deposit demand wasn't logged as a condition (so that red flag didn't fire). See `evals/golden-calls.md` case 1.

## Iterating (Alex's loop, works from a phone via Claude Code web)

1. Edit `prompts/caller.md` or a persona card.
2. Run the sim against the affected personas (or ask a Claude Code session on the repo to).
3. Check the eval summary against `evals/golden-calls.md` — cases 2, 3, 5, and 10 must pass before any demo recording.
