#!/usr/bin/env python3
"""Create the Negotiator's ElevenLabs tools and agents programmatically.

Creates 4 webhook tools (placeholder backend URLs — Person D updates them once
the backend is deployed) and 2 agents (interviewer + caller) using the prompts
in prompts/. Records all IDs in elevenlabs/created.json.

Free to run (agent/tool creation burns no credits). Re-running creates
duplicates — check the dashboard or created.json first.

Usage: python3 elevenlabs/create_agents.py
"""
import json
import os
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://api.elevenlabs.io"
PLACEHOLDER = "https://backend-placeholder.negotiator.example"  # Person D: replace via tool update
LLM = "gpt-4o"
VOICE_ID = "cjVigY5qzO86Huf0OWal"  # ElevenLabs default demo voice; pick a better one in dashboard

if "ELEVENLABS_API_KEY" not in os.environ and (ROOT / ".env").exists():
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ["ELEVENLABS_API_KEY"]


def api(path, body=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR {e.code} on {path}: {e.read().decode()[:500]}", file=sys.stderr)
        raise


def existing_tools():
    tools = api("/v1/convai/tools").get("tools", [])
    return {t["tool_config"]["name"]: t["id"] for t in tools}


EXISTING = None


def webhook_tool(name, description, method, url, body_schema=None):
    global EXISTING
    if EXISTING is None:
        EXISTING = existing_tools()
    if name in EXISTING:
        print(f"(reusing existing tool {name})")
        return EXISTING[name]
    cfg = {
        "type": "webhook",
        "name": name,
        "description": description,
        "response_timeout_secs": 10,
        "api_schema": {"url": url, "method": method},
    }
    if body_schema:
        cfg["api_schema"]["request_body_schema"] = body_schema
    return api("/v1/convai/tools", {"tool_config": cfg})["id"]


def interviewer_prompt():
    prompt = (ROOT / "prompts" / "interviewer.md").read_text()
    yaml_text = (ROOT / "verticals" / "moving.yaml").read_text()
    m = re.search(r"interview_questions:\n((?:  - .+\n)+)", yaml_text)
    questions = m.group(1) if m else ""
    return prompt + "\n\n## Interview questions (from verticals/moving.yaml)\n" + questions


def caller_prompt():
    # single-brace placeholders in the repo prompt -> ElevenLabs {{dynamic_variables}}
    prompt = (ROOT / "prompts" / "caller.md").read_text()
    for var in ["company_name", "origin_city", "destination_city", "move_date", "job_spec_json"]:
        prompt = prompt.replace("{" + var + "}", "{{" + var + "}}")
    return prompt


def make_agent(name, prompt, first_message, tool_ids, dynamic_defaults=None):
    agent_cfg = {
        "prompt": {"prompt": prompt, "llm": LLM, "tool_ids": tool_ids},
        "first_message": first_message,
        "language": "en",
    }
    if dynamic_defaults:
        agent_cfg["dynamic_variables"] = {"dynamic_variable_placeholders": dynamic_defaults}
    body = {
        "name": name,
        "conversation_config": {
            "agent": agent_cfg,
            "tts": {"model_id": "eleven_flash_v2", "voice_id": VOICE_ID},
            "turn": {"turn_timeout": 7},
        },
    }
    return api("/v1/convai/agents/create", body)["agent_id"]


def main():
    ids = {}

    ids["tool_save_job_spec"] = webhook_tool(
        "save_job_spec",
        "Save the completed, user-confirmed job specification. Call exactly once, only "
        "after the user has explicitly confirmed the read-back of the full spec.",
        "POST", f"{PLACEHOLDER}/api/job-spec",
        {
            "type": "object",
            "description": "The complete job spec (see schemas/job_spec.schema.json)",
            "properties": {
                "origin": {"type": "object", "description": "address, home_type, bedrooms, floor, elevator, stairs_flights, parking_distance_ft", "properties": {}},
                "destination": {"type": "object", "description": "address, home_type, floor, elevator, stairs_flights, parking_distance_ft", "properties": {}},
                "move": {"type": "object", "description": "distance_miles, move_date, flexibility_days", "properties": {}},
                "inventory": {"type": "object", "description": "large_items, boxes_estimate, fragile_items", "properties": {}},
                "services": {"type": "object", "description": "packing, disassembly, insurance", "properties": {}},
            },
            "required": ["origin", "destination", "move", "inventory", "services"],
        },
    )
    print("save_job_spec tool:", ids["tool_save_job_spec"])

    ids["tool_log_quote_item"] = webhook_tool(
        "log_quote_item",
        "Log one itemized fee or charge the company just quoted, immediately when you hear "
        "it. Call once per line item (base labor, truck fee, stairs fee, fuel, materials, insurance, etc).",
        "POST", f"{PLACEHOLDER}/api/quote-items",
        {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "What the charge is for"},
                "amount": {"type": "number", "description": "Dollar amount"},
                "disclosed_voluntarily": {"type": "boolean", "description": "false if you had to press for it"},
                "negotiable": {"type": "boolean", "description": "true if the rep indicated flexibility"},
            },
            "required": ["label", "amount"],
        },
    )
    print("log_quote_item tool:", ids["tool_log_quote_item"])

    ids["tool_get_best_bid"] = webhook_tool(
        "get_best_bid",
        "Get the current best competing itemized bid from other companies, for negotiation "
        "leverage. Returns null if no competing bid exists yet — then you must NOT imply one exists.",
        "GET", f"{PLACEHOLDER}/api/best-bid",
    )
    print("get_best_bid tool:", ids["tool_get_best_bid"])

    ids["tool_log_outcome"] = webhook_tool(
        "log_outcome",
        "Record the structured outcome of this call. MUST be called exactly once before the "
        "call ends. Never end a call without it.",
        "POST", f"{PLACEHOLDER}/api/outcome",
        {
            "type": "object",
            "properties": {
                "outcome": {"type": "string", "description": "one of: itemized_quote | callback_commitment | declined_documented"},
                "initial_total": {"type": "number", "description": "First total quoted, before negotiation"},
                "final_total": {"type": "number", "description": "Total after negotiation"},
                "binding": {"type": "boolean", "description": "true if the company called the quote binding"},
                "conditions": {"type": "array", "description": "e.g. 'weekday move only', 'cash deposit required'", "items": {"type": "string", "description": "one condition attached to the price"}},
                "callback_contact": {"type": "string", "description": "Name of who will call back, if callback_commitment"},
                "callback_window": {"type": "string", "description": "Promised time window, if callback_commitment"},
                "notes": {"type": "string", "description": "Anything else the customer should know"},
            },
            "required": ["outcome"],
        },
    )
    print("log_outcome tool:", ids["tool_log_outcome"])

    ids["agent_interviewer"] = make_agent(
        "negotiator-interviewer",
        interviewer_prompt(),
        "Hi! I'm your moving assistant. I'll ask a few quick questions so movers can give "
        "you a real, binding quote — takes about two minutes. Ready?",
        [ids["tool_save_job_spec"]],
    )
    print("interviewer agent:", ids["agent_interviewer"])

    ids["agent_caller"] = make_agent(
        "negotiator-caller",
        caller_prompt(),
        "Hi, is this {{company_name}}?",
        [ids["tool_log_quote_item"], ids["tool_get_best_bid"], ids["tool_log_outcome"]],
        dynamic_defaults={
            "company_name": "the moving company",
            "origin_city": "Rock Hill",
            "destination_city": "Charlotte",
            "move_date": "2026-08-08",
            "job_spec_json": json.dumps(json.loads((ROOT / "fixtures" / "daniel_job_spec.json").read_text())),
        },
    )
    print("caller agent:", ids["agent_caller"])

    out = ROOT / "elevenlabs" / "created.json"
    out.write_text(json.dumps(ids, indent=2) + "\n")
    print("\nAll IDs saved to", out.relative_to(ROOT))
    print("Test in browser: https://elevenlabs.io/app/talk-to?agent_id=" + ids["agent_caller"])


if __name__ == "__main__":
    main()
