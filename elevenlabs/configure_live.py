#!/usr/bin/env python3
"""Point the existing ElevenLabs agents at a deployed Negotiator backend.

Usage:
  BACKEND_URL=https://your-tunnel.example .venv/bin/python elevenlabs/configure_live.py --apply

Reads the existing agent/tool IDs from created.json. Run without --apply to
inspect the exact changes before mutating the ElevenLabs workspace.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://api.elevenlabs.io/v1/convai"


def load_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().split(" #", 1)[0].rstrip())


def api(key: str, method: str, path: str, payload: dict | None = None) -> dict:
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"ElevenLabs {method} {path} failed ({error.code}): {detail}") from error


def parameter(kind: str, description: str, enum: list[str] | None = None) -> dict:
    return {
        "type": kind, "description": description, "enum": enum,
        "is_system_provided": False, "dynamic_variable": "", "allowed_values_dynamic_variable": "",
        "constant_value": "", "is_omitted": False,
    }


def object_schema(properties: dict, required: list[str], description: str = "") -> dict:
    return {"description": description, "dynamic_variable": "", "is_omitted": False, "type": "object", "required": required, "properties": properties}


def cleaning_spec_schema() -> dict:
    simple = lambda fields: object_schema({name: parameter(kind, name.replace("_", " ")) for name, kind in fields}, [name for name, _ in fields])
    properties = {
        "property": simple([("type", "string"), ("sqft", "number"), ("bedrooms", "number"), ("bathrooms", "number"), ("levels", "number")]),
        "clean_type": parameter("string", "standard, deep, or move_out", ["standard", "deep", "move_out"]),
        "frequency": parameter("string", "one_time, weekly, biweekly, or monthly", ["one_time", "weekly", "biweekly", "monthly"]),
        "condition": simple([("clutter_level", "string"), ("has_pets", "boolean"), ("weeks_since_last_clean", "number")]),
        "add_ons": simple([("fridge", "boolean"), ("oven", "boolean"), ("windows", "boolean"), ("baseboards", "boolean"), ("laundry", "boolean")]),
        "access": simple([("parking", "string"), ("entry_method", "string"), ("walk_up_floor", "number")]),
        "schedule": simple([("preferred_date", "string"), ("preferred_time_window", "string"), ("flexibility", "string")]),
        "open_questions": {"description": "Unanswered details", "dynamic_variable": "", "constant_value": None, "is_omitted": False, "type": "array", "items": parameter("string", "one unanswered question")},
        "confirmed_by_user": parameter("boolean", "true only after explicit confirmation"),
        "intake_source": parameter("string", "voice_interview", ["voice_interview"]),
    }
    return object_schema(properties, list(properties), "The complete confirmed home-cleaning specification.")


def configured_tool(current: dict, key: str, backend_url: str) -> dict:
    config = current["tool_config"]
    config["response_timeout_secs"] = 15
    schema = config["api_schema"]
    if key == "tool_save_job_spec":
        config["description"] = "Save the complete cleaning specification only after explicit customer confirmation."
        schema.update({"url": f"{backend_url}/specs", "method": "POST", "request_body_schema": cleaning_spec_schema()})
    elif key == "tool_log_quote_item":
        config["description"] = "Log one itemized cleaning quote fee as soon as the company states it."
        schema.update({"url": f"{backend_url}/tools/log_quote_item", "method": "POST", "request_body_schema": object_schema({
            "call_id": parameter("string", "The call_id supplied for this call."),
            "label": parameter("string", "What the charge is for."), "amount": parameter("number", "Dollar amount."),
            "disclosed_voluntarily": parameter("boolean", "False if the agent had to press for it."),
            "negotiable": parameter("boolean", "True if the company indicated flexibility."),
        }, ["call_id", "label", "amount"])})
    elif key == "tool_get_best_bid":
        config["description"] = "Retrieve the real current competing bid before using price leverage. Never invent a bid."
        schema.update({"url": f"{backend_url}/tools/get_best_bid", "method": "GET", "request_body_schema": None, "query_params_schema": {
            "properties": {
                "spec_id": parameter("string", "The spec_id supplied for this call."),
                "exclude": parameter("string", "Current company name to exclude."),
            },
            "required": ["spec_id"],
        }})
    elif key == "tool_log_outcome":
        config["description"] = "Record the final structured outcome before the call ends: quote, callback, or declined."
        schema.update({"url": f"{backend_url}/tools/log_outcome", "method": "POST", "request_body_schema": object_schema({
            "call_id": parameter("string", "The call_id supplied for this call."),
            "outcome": parameter("string", "quote, callback, or declined", ["quote", "callback", "declined"]),
            "pricing_model": parameter("string", "flat or hourly"), "opening_total": parameter("number", "First quoted total."),
            "final_total": parameter("number", "Final negotiated total."), "total": parameter("number", "Final total."),
            "moved_because": parameter("string", "Reason the price moved."),
            "conditions": {"description": "Conditions attached to the quote", "dynamic_variable": "", "constant_value": None, "is_omitted": False, "type": "array", "items": parameter("string", "one condition")},
            "notes": parameter("string", "Anything the customer should know."), "callback_contact": parameter("string", "Callback contact, if any."),
            "callback_window": parameter("string", "Callback time window, if any."), "transcript_url": parameter("string", "Transcript URL, if available."), "recording_url": parameter("string", "Recording URL, if available."),
        }, ["call_id", "outcome"])})
    return config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Patch the live ElevenLabs tools and agent prompts.")
    args = parser.parse_args()
    load_env()
    api_key = os.environ["ELEVENLABS_API_KEY"]
    backend_url = os.environ["BACKEND_URL"].rstrip("/")
    ids = json.loads((ROOT / "elevenlabs" / "created.json").read_text())
    print(f"Backend: {backend_url}")
    for key in ("tool_save_job_spec", "tool_log_quote_item", "tool_get_best_bid", "tool_log_outcome"):
        current = api(api_key, "GET", f"/tools/{ids[key]}")
        config = configured_tool(current, key, backend_url)
        print(f"{'PATCH' if args.apply else 'WOULD PATCH'} {key} -> {config['api_schema']['url']}")
        if args.apply:
            api(api_key, "PATCH", f"/tools/{ids[key]}", {"tool_config": config})
    if args.apply:
        interviewer = (ROOT / "prompts" / "interviewer.md").read_text()
        caller = (ROOT / "prompts" / "caller.md").read_text()
        for variable in ("company_name", "spec_id", "call_id", "job_spec_json"):
            caller = caller.replace("{" + variable + "}", "{{" + variable + "}}")
        for name, prompt, tool_keys, dynamic_variables in (
            ("agent_interviewer", interviewer, ["tool_save_job_spec"], None),
            ("agent_caller", caller, ["tool_log_quote_item", "tool_get_best_bid", "tool_log_outcome"], {
                "company_name": "the cleaning company", "spec_id": "set-per-call",
                "call_id": "set-per-call", "job_spec_json": "set-per-call",
            }),
        ):
            agent_config = {"prompt": {"prompt": prompt, "tool_ids": [ids[key] for key in tool_keys]}}
            if dynamic_variables:
                agent_config["dynamic_variables"] = {"dynamic_variable_placeholders": dynamic_variables}
            api(api_key, "PATCH", f"/agents/{ids[name]}", {"conversation_config": {"agent": agent_config}})
            print(f"PATCHED {name}")


if __name__ == "__main__":
    main()
