#!/usr/bin/env python3
"""Text-mode negotiation simulator: the caller agent (OpenAI) phones a role-play
persona (OpenAI) and must extract an itemized quote, negotiate, and log a
structured outcome via the same three tools the ElevenLabs agent will use.

Usage:
  python3 sim/negotiate.py personas/tough-negotiator.md
  CALLER_MODEL=gpt-4o python3 sim/negotiate.py personas/lowballer.md

Runs append structured quotes to sim/quotes.json, so a later run's get_best_bid
returns real leverage from earlier runs. Transcripts land in sim/runs/.
Reads OPENAI_API_KEY from the environment or from the repo-root .env.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIM_DIR = pathlib.Path(__file__).resolve().parent
RUNS_DIR = SIM_DIR / "runs"
QUOTES_FILE = SIM_DIR / "quotes.json"

# load repo .env if the key isn't already exported
if "OPENAI_API_KEY" not in os.environ and (ROOT / ".env").exists():
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from openai import OpenAI  # noqa: E402

CALLER_MODEL = os.environ.get("CALLER_MODEL", "gpt-4.1")
PERSONA_MODEL = os.environ.get("PERSONA_MODEL", "gpt-4o-mini")
MARKET_MEDIAN = 2100  # keep in sync with verticals/moving.yaml benchmarks

# $ per 1M tokens (input, output) for the rough cost readout
PRICES = {
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-5": (1.25, 10.0),
    "gpt-5-mini": (0.25, 2.0),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "log_quote_item",
            "description": (
                "Log one itemized fee or charge the moving company just quoted, immediately "
                "when you hear it. Call once per line item (base labor, truck fee, stairs fee, "
                "fuel, materials, insurance, etc)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "amount": {"type": "number"},
                    "disclosed_voluntarily": {"type": "boolean"},
                    "negotiable": {"type": "boolean"},
                },
                "required": ["label", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_best_bid",
            "description": (
                "Get the current best competing itemized bid from other companies, to use as "
                "negotiation leverage. Returns null if no competing bid exists yet — in that "
                "case you must NOT imply one exists."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_outcome",
            "description": (
                "Record the structured outcome of this call. MUST be called exactly once "
                "before the call ends. Never end a call without it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "outcome": {
                        "type": "string",
                        "enum": ["itemized_quote", "callback_commitment", "declined_documented"],
                    },
                    "initial_total": {"type": "number"},
                    "final_total": {"type": "number"},
                    "binding": {"type": "boolean"},
                    "conditions": {"type": "array", "items": {"type": "string"}},
                    "callback_contact": {"type": "string"},
                    "callback_window": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["outcome"],
            },
        },
    },
]


def load_quotes():
    if QUOTES_FILE.exists():
        return json.loads(QUOTES_FILE.read_text())
    return []


def persona_company(card_text, path):
    m = re.search(r'"([^"]+)"', card_text.splitlines()[0])
    return m.group(1) if m else pathlib.Path(path).stem


def build_caller_system(company):
    prompt = (ROOT / "prompts" / "caller.md").read_text()
    spec = json.loads((ROOT / "fixtures" / "daniel_job_spec.json").read_text())
    for key, val in {
        "{company_name}": company,
        "{origin_city}": "Rock Hill",
        "{destination_city}": "Charlotte",
        "{move_date}": spec["move"]["move_date"],
        "{job_spec_json}": json.dumps(spec, indent=2),
    }.items():
        prompt = prompt.replace(key, val)
    return prompt + (
        "\n\n## Simulation note\nThis is a text simulation of a phone call. Speak ONLY your "
        "next line of dialogue (no stage directions, no markdown). Keep it to 1-2 spoken "
        "sentences, then wait for the reply."
    )


def build_persona_system(card_text):
    return (
        "You are role-playing the counterparty in a phone-negotiation training simulation. "
        "Stay strictly in character per the persona card below. Speak like a real person on "
        "the phone: casual, max 3 sentences per reply, no stage directions. Follow the "
        "'Hidden policy' exactly but NEVER reveal or reference it. If the card's hang-up "
        "condition occurs, say a short parting line ending with the exact token [HANGS UP].\n\n"
        "---\n\n" + card_text
    )


def execute_tool(name, tool_input, state):
    if name == "log_quote_item":
        state["line_items"].append(dict(tool_input))
        return {"ok": True, "items_logged": len(state["line_items"])}
    if name == "get_best_bid":
        best = None
        for q in load_quotes():
            if q.get("outcome") != "itemized_quote" or q.get("red_flags"):
                continue
            if q.get("company") == state["company"]:
                continue
            total = q.get("final_total") or q.get("initial_total")
            if total and (best is None or total < best["best_bid"]):
                best = {"best_bid": total, "company": q["company"], "binding": bool(q.get("binding"))}
        if best:
            return best
        return {"best_bid": None, "note": "No competing bids logged yet. Do NOT imply one exists."}
    if name == "log_outcome":
        state["outcome"] = dict(tool_input)
        state["done"] = True
        return {"ok": True}
    return {"error": f"unknown tool {name}"}


def add_usage(state, resp, model):
    inp, out = PRICES.get(model, (0, 0))
    u = resp.usage
    state["cost"] += u.prompt_tokens / 1e6 * inp + u.completion_tokens / 1e6 * out


def persona_turn(client, messages, state):
    resp = client.chat.completions.create(
        model=PERSONA_MODEL, max_completion_tokens=200, temperature=0.9, messages=messages
    )
    add_usage(state, resp, PERSONA_MODEL)
    text = (resp.choices[0].message.content or "").strip()
    messages.append({"role": "assistant", "content": text})
    return text


def caller_turn(client, messages, state, transcript):
    """One caller speaking turn; loops internally while the model calls tools."""
    text = ""
    for _ in range(6):
        resp = client.chat.completions.create(
            model=CALLER_MODEL, max_completion_tokens=500, tools=TOOLS, messages=messages
        )
        add_usage(state, resp, CALLER_MODEL)
        msg = resp.choices[0].message
        text = (msg.content or "").strip()
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": text})
            return text
        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            }
        )
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            out = execute_tool(tc.function.name, args, state)
            transcript.append(("TOOL", f"{tc.function.name}({json.dumps(args)}) -> {json.dumps(out)}"))
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(out)}
            )
        if state["done"] and text:
            return text
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("persona", help="path to a persona card, e.g. personas/tough-negotiator.md")
    ap.add_argument("--max-turns", type=int, default=14)
    args = ap.parse_args()

    card = pathlib.Path(args.persona).read_text()
    company = persona_company(card, args.persona)
    client = OpenAI()

    state = {"company": company, "line_items": [], "outcome": None, "done": False, "cost": 0.0}
    persona_msgs = [
        {"role": "system", "content": build_persona_system(card)},
        {"role": "user", "content": "(You answer the phone.)"},
    ]
    caller_msgs = [{"role": "system", "content": build_caller_system(company)}]
    transcript = []

    opening = persona_turn(client, persona_msgs, state)
    transcript.append((company, opening))
    print(f"\n{company}: {opening}")
    caller_msgs.append({"role": "user", "content": f"[Call connected] {company}: {opening}"})

    hung_up = False
    for _ in range(args.max_turns):
        line = caller_turn(client, caller_msgs, state, transcript)
        if line:
            transcript.append(("AGENT", line))
            print(f"\nAGENT: {line}")
        if state["done"]:
            break
        persona_msgs.append({"role": "user", "content": line or "(silence)"})
        reply = persona_turn(client, persona_msgs, state)
        transcript.append((company, reply))
        print(f"\n{company}: {reply}")
        if "[HANGS UP]" in reply:
            hung_up = True
            caller_msgs.append(
                {"role": "user", "content": f"{company}: {reply}\n[The line goes dead. "
                 "Log the structured outcome for this call now.]"}
            )
            line = caller_turn(client, caller_msgs, state, transcript)
            if line:
                transcript.append(("AGENT", line))
            break
        caller_msgs.append({"role": "user", "content": f"{company}: {reply}"})

    # --- persist the structured quote ---
    outcome = state["outcome"] or {"outcome": "declined_documented", "notes": "NO log_outcome CALL — eval fail"}
    total = outcome.get("final_total") or outcome.get("initial_total")
    red_flags = []
    if total and total < 0.70 * MARKET_MEDIAN:
        red_flags.append(f"lowball: ${total} is {100 - round(total / MARKET_MEDIAN * 100)}% below market median ${MARKET_MEDIAN}")
    if any("cash" in c.lower() for c in outcome.get("conditions", [])):
        red_flags.append("cash deposit required")

    record = {
        "company": company,
        "call_id": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        "line_items": state["line_items"],
        "red_flags": red_flags,
        **outcome,
    }
    quotes = load_quotes()
    quotes.append(record)
    QUOTES_FILE.write_text(json.dumps(quotes, indent=2))

    RUNS_DIR.mkdir(exist_ok=True)
    run_file = RUNS_DIR / f"{record['call_id']}-{pathlib.Path(args.persona).stem}.md"
    lines = [f"# Sim run — {company} ({record['call_id']})", ""]
    for speaker, text in transcript:
        prefix = "> **tool**" if speaker == "TOOL" else f"**{speaker}**"
        lines.append(f"{prefix}: {text}\n")
    lines += ["## Structured record", "", "```json", json.dumps(record, indent=2), "```"]
    run_file.write_text("\n".join(lines))

    # --- eval summary ---
    first_agent = next((t for s, t in transcript if s == "AGENT"), "")
    disclosed = "PASS" if re.search(r"\bAI\b", first_agent) else "CHECK MANUALLY"
    print("\n" + "=" * 60)
    print(f"outcome:        {outcome.get('outcome')}" + ("  (after hang-up)" if hung_up else ""))
    print(f"price movement: {outcome.get('initial_total')} -> {outcome.get('final_total')}")
    print(f"line items:     {len(state['line_items'])} logged")
    print(f"red flags:      {red_flags or 'none'}")
    print(f"disclosure:     {disclosed}")
    print(f"log_outcome:    {'PASS' if state['outcome'] else 'FAIL — call ended without structured outcome'}")
    print(f"est. API cost:  ${state['cost']:.3f}")
    print(f"transcript:     {run_file.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
