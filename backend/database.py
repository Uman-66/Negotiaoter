"""Supabase persistence for the live, flat-column cleaning schema.

This matches the schema used by Uman's public backend. The job-spec JSON is
flattened at the database boundary and reconstructed for every API response.
"""
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import create_client


def _load_local_env() -> None:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().split(" #", 1)[0].rstrip())


_load_local_env()
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_KEY")
    or os.environ.get("SUPABASE_KEY")
    or os.environ.get("VITE_SUPABASE_PUBLISHABLE_KEY")
)
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials missing. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.")
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)


def to_flat_spec(spec_id: str, data: dict) -> dict:
    property_data = data.get("property", {}) or {}
    condition = data.get("condition", {}) or {}
    add_ons = data.get("add_ons", {}) or {}
    access = data.get("access", {}) or {}
    schedule = data.get("schedule", {}) or {}
    return {
        "id": spec_id,
        "property_type": property_data.get("type", "apartment"),
        "property_sqft": property_data.get("sqft", 0),
        "property_bedrooms": property_data.get("bedrooms", 0),
        "property_bathrooms": property_data.get("bathrooms", 0.0),
        "property_levels": property_data.get("levels", 1),
        "clean_type": data.get("clean_type", "standard"),
        "frequency": data.get("frequency", "one_time"),
        "clutter_level": condition.get("clutter_level", "medium"),
        "has_pets": condition.get("has_pets", False),
        "weeks_since_last_clean": condition.get("weeks_since_last_clean", 0),
        "add_on_fridge": add_ons.get("fridge", False),
        "add_on_oven": add_ons.get("oven", False),
        "add_on_windows": add_ons.get("windows", False),
        "add_on_baseboards": add_ons.get("baseboards", False),
        "add_on_laundry": add_ons.get("laundry", False),
        "access_parking": access.get("parking", "street"),
        "access_entry_method": access.get("entry_method", "to be confirmed"),
        "access_walk_up_floor": access.get("walk_up_floor", 0),
        "schedule_preferred_date": schedule.get("preferred_date", ""),
        "schedule_preferred_time_window": schedule.get("preferred_time_window", "to be confirmed"),
        "schedule_flexibility": schedule.get("flexibility"),
        "open_questions": data.get("open_questions", []),
        "confirmed_by_user": data.get("confirmed_by_user", False),
        "intake_source": data.get("intake_source", "voice_interview"),
        "created_at": datetime.utcnow().isoformat(),
    }


def from_flat_spec(row: dict) -> dict:
    return {
        "id": row["id"],
        "property": {
            "type": row["property_type"], "sqft": row["property_sqft"],
            "bedrooms": row["property_bedrooms"], "bathrooms": row["property_bathrooms"],
            "levels": row["property_levels"],
        },
        "clean_type": row["clean_type"], "frequency": row["frequency"],
        "condition": {
            "clutter_level": row["clutter_level"], "has_pets": row["has_pets"],
            "weeks_since_last_clean": row["weeks_since_last_clean"],
        },
        "add_ons": {
            "fridge": row["add_on_fridge"], "oven": row["add_on_oven"], "windows": row["add_on_windows"],
            "baseboards": row["add_on_baseboards"], "laundry": row["add_on_laundry"],
        },
        "access": {
            "parking": row["access_parking"], "entry_method": row["access_entry_method"],
            "walk_up_floor": row["access_walk_up_floor"],
        },
        "schedule": {
            "preferred_date": row["schedule_preferred_date"],
            "preferred_time_window": row["schedule_preferred_time_window"],
            "flexibility": row.get("schedule_flexibility"),
        },
        "open_questions": row.get("open_questions") or [],
        "confirmed_by_user": row.get("confirmed_by_user", False),
        "intake_source": row.get("intake_source", "voice_interview"),
        "created_at": row.get("created_at"),
    }


def db_create_spec(data: dict) -> dict:
    spec_id = f"spec_{uuid.uuid4().hex[:8]}"
    row = to_flat_spec(spec_id, data)
    supabase_client.table("specs").insert(row).execute()
    return from_flat_spec(row)


def db_get_spec(spec_id: str) -> Optional[dict]:
    response = supabase_client.table("specs").select("*").eq("id", spec_id).execute()
    return from_flat_spec(response.data[0]) if response.data else None


def db_update_spec(spec_id: str, data: dict) -> Optional[dict]:
    if not db_get_spec(spec_id):
        return None
    row = to_flat_spec(spec_id, data)
    row.pop("id", None)
    row.pop("created_at", None)
    supabase_client.table("specs").update(row).eq("id", spec_id).execute()
    return db_get_spec(spec_id)


def db_confirm_spec(spec_id: str) -> dict:
    supabase_client.table("specs").update({"confirmed_by_user": True}).eq("id", spec_id).execute()
    spec = db_get_spec(spec_id)
    if not spec:
        raise Exception("Spec not found")
    companies = supabase_client.table("companies").select("*").execute().data
    for company in companies:
        existing = supabase_client.table("calls").select("id").eq("spec_id", spec_id).eq("company_id", company["id"]).execute()
        if not existing.data:
            supabase_client.table("calls").insert({
                "id": f"call_{uuid.uuid4().hex[:8]}", "spec_id": spec_id, "company_id": company["id"],
                "status": "queued", "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat(),
            }).execute()
    return db_get_spec(spec_id) or spec


def db_start_call(spec_id: str, company_id: str) -> dict:
    response = supabase_client.table("calls").select("*").eq("spec_id", spec_id).eq("company_id", company_id).execute()
    if response.data:
        call = response.data[0]
        call_id = call["id"]
        supabase_client.table("calls").update({"status": "calling", "updated_at": datetime.utcnow().isoformat()}).eq("id", call_id).execute()
    else:
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        supabase_client.table("calls").insert({"id": call_id, "spec_id": spec_id, "company_id": company_id, "status": "calling", "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()}).execute()
    company = supabase_client.table("companies").select("name").eq("id", company_id).execute().data
    return {"call_id": call_id, "spec_id": spec_id, "company_id": company_id, "company_name": company[0]["name"] if company else "Unknown", "status": "calling"}


def db_get_calls(spec_id: str) -> List[Dict[str, Any]]:
    calls = supabase_client.table("calls").select("*").eq("spec_id", spec_id).execute().data
    companies = {company["id"]: company for company in supabase_client.table("companies").select("*").execute().data}
    results: List[Dict[str, Any]] = []
    for call in calls:
        company = companies.get(call["company_id"], {"name": "Unknown", "persona": "Unknown"})
        quote_rows = supabase_client.table("quotes").select("*").eq("call_id", call["id"]).execute().data
        quote_data = None
        if quote_rows:
            quote = quote_rows[0]
            items = supabase_client.table("quote_items").select("*").eq("quote_id", quote["id"]).execute().data
            quote_data = {
                "id": quote["id"], "outcome": quote["outcome"], "pricing_model": quote.get("pricing_model"),
                "total": quote.get("total"), "opening_total": quote.get("opening_total"), "final_total": quote.get("final_total"),
                "moved_because": quote.get("moved_because"), "conditions": quote.get("conditions") or [],
                "red_flags": quote.get("red_flags") or [], "red_flag_reasons": quote.get("red_flag_reasons") or [],
                "notes": quote.get("notes"), "transcript_url": quote.get("transcript_url"), "recording_url": quote.get("recording_url"),
                "line_items": [{"label": item["label"], "amount": item["amount"]} for item in items],
            }
        results.append({"call_id": call["id"], "company_id": call["company_id"], "company_name": company["name"], "persona": company.get("persona", "Unknown"), "status": call["status"], "quote": quote_data, "updated_at": call.get("updated_at")})
    return results


def _quote_for_call(call: dict) -> dict:
    response = supabase_client.table("quotes").select("*").eq("call_id", call["id"]).execute()
    if response.data:
        return response.data[0]
    quote = {"id": f"quote_{call['id']}", "call_id": call["id"], "company_id": call["company_id"], "spec_id": call["spec_id"], "outcome": "quote", "pricing_model": "flat", "opening_total": 0.0, "final_total": 0.0, "total": 0.0, "created_at": datetime.utcnow().isoformat()}
    supabase_client.table("quotes").insert(quote).execute()
    return quote


def db_log_quote_item(call_id: str, label: str, amount: float, disclosed_voluntarily: bool, negotiable: bool) -> dict:
    response = supabase_client.table("calls").select("*").eq("id", call_id).execute()
    if not response.data:
        raise Exception(f"Call session {call_id} not found")
    call = response.data[0]
    if call["status"] == "queued":
        supabase_client.table("calls").update({"status": "calling"}).eq("id", call_id).execute()
    quote = _quote_for_call(call)
    supabase_client.table("quote_items").insert({"quote_id": quote["id"], "call_id": call_id, "label": label, "amount": amount, "disclosed_voluntarily": disclosed_voluntarily, "negotiable": negotiable, "created_at": datetime.utcnow().isoformat()}).execute()
    items = supabase_client.table("quote_items").select("amount").eq("quote_id", quote["id"]).execute().data
    total = sum(float(item["amount"]) for item in items)
    update = {"total": total, "final_total": total}
    if not quote.get("opening_total"):
        update["opening_total"] = total
    supabase_client.table("quotes").update(update).eq("id", quote["id"]).execute()
    return {"success": True, "current_quote_total": total}


def db_get_best_bid(spec_id: str, exclude_company: str = None) -> dict:
    quotes = supabase_client.table("quotes").select("*").eq("spec_id", spec_id).eq("outcome", "quote").execute().data
    companies = {company["id"]: company["name"] for company in supabase_client.table("companies").select("id,name").execute().data}
    eligible = []
    for quote in quotes:
        name = companies.get(quote["company_id"], "")
        total = quote.get("final_total") or quote.get("total")
        if total and (not exclude_company or exclude_company.lower() not in name.lower()):
            eligible.append((float(total), name))
    if not eligible:
        return {"best_bid": None, "company_name": None}
    best_bid, company_name = min(eligible, key=lambda item: item[0])
    return {"best_bid": best_bid, "company_name": company_name}


def db_log_outcome(call_id: str, data: dict, run_red_flags_fn) -> dict:
    response = supabase_client.table("calls").select("*").eq("id", call_id).execute()
    if not response.data:
        raise Exception(f"Call session {call_id} not found")
    call = response.data[0]
    quote = _quote_for_call(call)
    final_total = data.get("final_total") if data.get("final_total") is not None else data.get("total")
    update = {
        "outcome": data["outcome"], "pricing_model": data.get("pricing_model") or "flat",
        "moved_because": data.get("moved_because"), "conditions": data.get("conditions") or [],
        "notes": data.get("notes"), "callback_contact": data.get("callback_contact"),
        "callback_window": data.get("callback_window"), "transcript_url": data.get("transcript_url"), "recording_url": data.get("recording_url"),
    }
    if final_total is not None:
        update["total"] = final_total
        update["final_total"] = final_total
    if data.get("opening_total") is not None:
        update["opening_total"] = data["opening_total"]
    elif not quote.get("opening_total") and final_total is not None:
        update["opening_total"] = final_total
    supabase_client.table("quotes").update(update).eq("id", quote["id"]).execute()
    spec = db_get_spec(call["spec_id"]) or {}
    items = supabase_client.table("quote_items").select("*").eq("quote_id", quote["id"]).execute().data
    line_items = [{"label": item["label"], "amount": item["amount"]} for item in items]
    quote_for_rules = {"total": update.get("total", quote.get("total")), "final_total": update.get("final_total", quote.get("final_total")), "opening_total": update.get("opening_total", quote.get("opening_total")), "outcome": update["outcome"], "pricing_model": update["pricing_model"], "conditions": update["conditions"], "notes": update["notes"] or ""}
    red_flags, reasons = run_red_flags_fn(spec, quote_for_rules, line_items)
    supabase_client.table("quotes").update({"red_flags": red_flags, "red_flag_reasons": reasons}).eq("id", quote["id"]).execute()
    supabase_client.table("calls").update({"status": "declined" if data["outcome"] == "declined" else "done", "updated_at": datetime.utcnow().isoformat()}).eq("id", call_id).execute()
    return {"success": True, "quote_id": quote["id"], "red_flags": red_flags, "red_flag_reasons": reasons}


def init_db() -> None:
    response = supabase_client.table("companies").select("id").limit(1).execute()
    if not response.data:
        supabase_client.table("companies").insert([
            {"id": "company_1", "name": "Apex Cleaning Co", "persona": "Premium"},
            {"id": "company_2", "name": "Budget Cleaners", "persona": "Lowballer"},
            {"id": "company_3", "name": "Sparkle & Shine", "persona": "Upseller"},
        ]).execute()
