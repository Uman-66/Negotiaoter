import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from supabase import create_client, Client

logger = logging.getLogger("database")

# Load .env if it exists
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Supabase Client Initialization
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_PUBLISHABLE_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in .env")

try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to initialize Supabase client: {e}")

# --- We no longer use SQLite ---
# SQLAlchemy models are kept only for potential local testing, but we never instantiate them.
# They are not used when use_supabase() is True.

Base = declarative_base()

# --- SQLAlchemy Models (kept for reference, but not used in production) ---
class Spec(Base):
    __tablename__ = "specs"
    id = Column(String, primary_key=True, index=True)
    property_type = Column(String, nullable=False)
    property_sqft = Column(Integer, nullable=False)
    property_bedrooms = Column(Integer, nullable=False)
    property_bathrooms = Column(Float, nullable=False)
    property_levels = Column(Integer, default=1)
    clean_type = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    clutter_level = Column(String, nullable=False)
    has_pets = Column(Boolean, nullable=False)
    weeks_since_last_clean = Column(Integer, nullable=False)
    add_on_fridge = Column(Boolean, default=False)
    add_on_oven = Column(Boolean, default=False)
    add_on_windows = Column(Boolean, default=False)
    add_on_baseboards = Column(Boolean, default=False)
    add_on_laundry = Column(Boolean, default=False)
    access_parking = Column(String, nullable=False)
    access_entry_method = Column(String, nullable=False)
    access_walk_up_floor = Column(Integer, default=0)
    schedule_preferred_date = Column(String, nullable=False)
    schedule_preferred_time_window = Column(String, nullable=False)
    schedule_flexibility = Column(String, nullable=True)
    open_questions = Column(JSON, default=list)
    confirmed_by_user = Column(Boolean, default=False)
    intake_source = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    calls = relationship("Call", back_populates="spec", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="spec", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    persona = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    calls = relationship("Call", back_populates="company")
    quotes = relationship("Quote", back_populates="company")

class Call(Base):
    __tablename__ = "calls"
    id = Column(String, primary_key=True, index=True)
    spec_id = Column(String, ForeignKey("specs.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    spec = relationship("Spec", back_populates="calls")
    company = relationship("Company", back_populates="calls")
    quotes = relationship("Quote", back_populates="call", cascade="all, delete-orphan")

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(String, primary_key=True, index=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    spec_id = Column(String, ForeignKey("specs.id"), nullable=False)
    outcome = Column(String, nullable=False)
    pricing_model = Column(String, nullable=True)
    opening_total = Column(Float, nullable=True)
    final_total = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    moved_because = Column(String, nullable=True)
    conditions = Column(JSON, default=list)
    red_flags = Column(JSON, default=list)
    red_flag_reasons = Column(JSON, default=list)
    callback_contact = Column(String, nullable=True)
    callback_window = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    transcript_url = Column(String, nullable=True)
    recording_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    call = relationship("Call", back_populates="quotes")
    company = relationship("Company", back_populates="quotes")
    spec = relationship("Spec", back_populates="quotes")
    line_items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")

class QuoteItem(Base):
    __tablename__ = "quote_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    call_id = Column(String, nullable=True)
    label = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    disclosed_voluntarily = Column(Boolean, default=True)
    negotiable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    quote = relationship("Quote", back_populates="line_items")


# --- Force Supabase only ---
def use_supabase() -> bool:
    """
    Returns True if Supabase client is available.
    Raises RuntimeError if not – we do NOT fall back to SQLite.
    """
    if supabase_client is None:
        raise RuntimeError("Supabase client is not initialized. Check your credentials.")
    return True


# --- Serialization Helpers (unchanged) ---
def to_flat_spec(spec_id: str, data: dict) -> dict:
    prop = data.get("property", {}) or {}
    cond = data.get("condition", {}) or {}
    addons = data.get("add_ons", {}) or {}
    acc = data.get("access", {}) or {}
    sched = data.get("schedule", {}) or {}
    return {
        "id": spec_id,
        "property_type": prop.get("type", "apartment"),
        "property_sqft": prop.get("sqft", 0),
        "property_bedrooms": prop.get("bedrooms", 0),
        "property_bathrooms": prop.get("bathrooms", 0.0),
        "property_levels": prop.get("levels", 1),
        "clean_type": data.get("clean_type", "standard"),
        "frequency": data.get("frequency", "one_time"),
        "clutter_level": cond.get("clutter_level", "medium"),
        "has_pets": cond.get("has_pets", False),
        "weeks_since_last_clean": cond.get("weeks_since_last_clean", 0),
        "add_on_fridge": addons.get("fridge", False),
        "add_on_oven": addons.get("oven", False),
        "add_on_windows": addons.get("windows", False),
        "add_on_baseboards": addons.get("baseboards", False),
        "add_on_laundry": addons.get("laundry", False),
        "access_parking": acc.get("parking", "street"),
        "access_entry_method": acc.get("entry_method", ""),
        "access_walk_up_floor": acc.get("walk_up_floor", 0),
        "schedule_preferred_date": sched.get("preferred_date", ""),
        "schedule_preferred_time_window": sched.get("preferred_time_window", ""),
        "schedule_flexibility": sched.get("flexibility"),
        "open_questions": data.get("open_questions", []),
        "confirmed_by_user": data.get("confirmed_by_user", False),
        "intake_source": data.get("intake_source", "voice_interview"),
        "created_at": datetime.utcnow().isoformat()   # explicitly set
    }

def from_flat_spec(flat: dict) -> dict:
    return {
        "id": flat["id"],
        "property": {
            "type": flat["property_type"],
            "sqft": flat["property_sqft"],
            "bedrooms": flat["property_bedrooms"],
            "bathrooms": flat["property_bathrooms"],
            "levels": flat["property_levels"]
        },
        "clean_type": flat["clean_type"],
        "frequency": flat["frequency"],
        "condition": {
            "clutter_level": flat["clutter_level"],
            "has_pets": flat["has_pets"],
            "weeks_since_last_clean": flat["weeks_since_last_clean"]
        },
        "add_ons": {
            "fridge": flat["add_on_fridge"],
            "oven": flat["add_on_oven"],
            "windows": flat["add_on_windows"],
            "baseboards": flat["add_on_baseboards"],
            "laundry": flat["add_on_laundry"]
        },
        "access": {
            "parking": flat["access_parking"],
            "entry_method": flat["access_entry_method"],
            "walk_up_floor": flat["access_walk_up_floor"]
        },
        "schedule": {
            "preferred_date": flat["schedule_preferred_date"],
            "preferred_time_window": flat["schedule_preferred_time_window"],
            "flexibility": flat["schedule_flexibility"]
        },
        "open_questions": flat["open_questions"] or [],
        "confirmed_by_user": flat["confirmed_by_user"],
        "intake_source": flat["intake_source"],
        "created_at": flat.get("created_at")
    }

def to_spec_db(spec_id: str, data: dict) -> Spec:
    flat = to_flat_spec(spec_id, data)
    # delete id so it is set on constructor explicitly
    del flat["id"]
    return Spec(id=spec_id, **flat)

def from_spec_db(spec: Spec) -> dict:
    return from_flat_spec(spec.__dict__)


# --- Unified Wrapper Interface (Supabase only) ---

def db_create_spec(data: dict) -> dict:
    spec_id = f"spec_{uuid.uuid4().hex[:8]}"
    flat_data = to_flat_spec(spec_id, data)
    supabase_client.table("specs").insert(flat_data).execute()
    return from_flat_spec(flat_data)

def db_get_spec(spec_id: str) -> Optional[dict]:
    resp = supabase_client.table("specs").select("*").eq("id", spec_id).execute()
    if not resp.data:
        return None
    return from_flat_spec(resp.data[0])

def db_confirm_spec(spec_id: str) -> dict:
    # Update confirmed flag
    supabase_client.table("specs").update({"confirmed_by_user": True}).eq("id", spec_id).execute()
    spec_resp = supabase_client.table("specs").select("*").eq("id", spec_id).execute()
    if not spec_resp.data:
        raise Exception("Spec not found")
    spec_data = from_flat_spec(spec_resp.data[0])
    
    # Auto queue calls for all companies
    companies_resp = supabase_client.table("companies").select("*").execute()
    for company in companies_resp.data:
        existing_call = supabase_client.table("calls").select("*").eq("spec_id", spec_id).eq("company_id", company["id"]).execute()
        if not existing_call.data:
            supabase_client.table("calls").insert({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "spec_id": spec_id,
                "company_id": company["id"],
                "status": "queued",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
    return spec_data

def db_start_call(spec_id: str, company_id: str) -> dict:
    # Verify call exists or create
    call_resp = supabase_client.table("calls").select("*").eq("spec_id", spec_id).eq("company_id", company_id).execute()
    if call_resp.data:
        call = call_resp.data[0]
        call_id = call["id"]
        supabase_client.table("calls").update({
            "status": "calling",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", call_id).execute()
    else:
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        supabase_client.table("calls").insert({
            "id": call_id,
            "spec_id": spec_id,
            "company_id": company_id,
            "status": "calling",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
    
    comp_resp = supabase_client.table("companies").select("*").eq("id", company_id).execute()
    comp_name = comp_resp.data[0]["name"] if comp_resp.data else "Unknown"
    return {
        "call_id": call_id,
        "spec_id": spec_id,
        "company_id": company_id,
        "company_name": comp_name,
        "status": "calling"
    }

def db_get_calls(spec_id: str) -> List[Dict[str, Any]]:
    calls_resp = supabase_client.table("calls").select("*").eq("spec_id", spec_id).execute()
    companies_resp = supabase_client.table("companies").select("*").execute()
    comp_map = {c["id"]: c for c in companies_resp.data}
    
    results = []
    for call in calls_resp.data:
        company = comp_map.get(call["company_id"], {"name": "Unknown", "persona": "Unknown"})
        quote_resp = supabase_client.table("quotes").select("*").eq("call_id", call["id"]).execute()
        quote_data = None
        if quote_resp.data:
            q = quote_resp.data[0]
            items_resp = supabase_client.table("quote_items").select("*").eq("quote_id", q["id"]).execute()
            quote_data = {
                "id": q["id"],
                "outcome": q["outcome"],
                "pricing_model": q.get("pricing_model"),
                "total": q.get("total"),
                "opening_total": q.get("opening_total"),
                "final_total": q.get("final_total"),
                "moved_because": q.get("moved_because"),
                "red_flags": q.get("red_flags") or [],
                "red_flag_reasons": q.get("red_flag_reasons") or [],
                "line_items": [{"label": item["label"], "amount": item["amount"]} for item in items_resp.data]
            }
        results.append({
            "call_id": call["id"],
            "company_id": call["company_id"],
            "company_name": company["name"],
            "persona": company["persona"],
            "status": call["status"],
            "quote": quote_data,
            "updated_at": call.get("updated_at")
        })
    return results

def db_log_quote_item(call_id: str, label: str, amount: float, disclosed_voluntarily: bool, negotiable: bool) -> dict:
    call_resp = supabase_client.table("calls").select("*").eq("id", call_id).execute()
    if not call_resp.data:
        raise Exception(f"Call session {call_id} not found")
    call = call_resp.data[0]
    
    if call["status"] == "queued":
        supabase_client.table("calls").update({"status": "calling"}).eq("id", call_id).execute()
        
    quote_resp = supabase_client.table("quotes").select("*").eq("call_id", call_id).execute()
    if quote_resp.data:
        quote = quote_resp.data[0]
    else:
        quote_id = f"quote_{call_id}"
        supabase_client.table("quotes").insert({
            "id": quote_id,
            "call_id": call_id,
            "company_id": call["company_id"],
            "spec_id": call["spec_id"],
            "outcome": "quote",
            "pricing_model": "flat",
            "opening_total": 0.0,
            "final_total": 0.0,
            "total": 0.0,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        quote = {"id": quote_id, "opening_total": 0.0}
        
    supabase_client.table("quote_items").insert({
        "quote_id": quote["id"],
        "call_id": call_id,
        "label": label,
        "amount": amount,
        "disclosed_voluntarily": disclosed_voluntarily,
        "negotiable": negotiable,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    items_resp = supabase_client.table("quote_items").select("amount").eq("quote_id", quote["id"]).execute()
    calculated_total = sum(item["amount"] for item in items_resp.data)
    
    update_data = {
        "total": calculated_total,
        "final_total": calculated_total
    }
    if quote.get("opening_total") == 0.0:
        update_data["opening_total"] = calculated_total
        
    supabase_client.table("quotes").update(update_data).eq("id", quote["id"]).execute()
    return {
        "success": True,
        "current_quote_total": calculated_total
    }

def db_get_best_bid(spec_id: str, exclude_company: str = None) -> dict:
    # Fetch all quotes with outcome='quote'
    quotes_resp = supabase_client.table("quotes").select("*").eq("spec_id", spec_id).eq("outcome", "quote").execute()
    if not quotes_resp.data:
        return {"best_bid": None, "company_name": None}

    # Get company names for those quotes
    company_ids = list({q["company_id"] for q in quotes_resp.data if q.get("company_id")})
    if not company_ids:
        return {"best_bid": None, "company_name": None}
    companies_resp = supabase_client.table("companies").select("id, name").in_("id", company_ids).execute()
    comp_name_map = {c["id"]: c["name"] for c in companies_resp.data}

    best_bid = None
    best_company = None
    for q in quotes_resp.data:
        comp_name = comp_name_map.get(q["company_id"], "")
        if exclude_company and exclude_company.lower() in comp_name.lower():
            continue
        total = q.get("final_total") or q.get("total")
        if total is not None and total > 0:
            if best_bid is None or total < best_bid:
                best_bid = total
                best_company = comp_name
    return {
        "best_bid": best_bid,
        "company_name": best_company
    }

def db_log_outcome(call_id: str, data: dict, run_red_flags_fn) -> dict:
    call_resp = supabase_client.table("calls").select("*").eq("id", call_id).execute()
    if not call_resp.data:
        raise Exception(f"Call session {call_id} not found")
    call = call_resp.data[0]
    
    quote_resp = supabase_client.table("quotes").select("*").eq("call_id", call_id).execute()
    if quote_resp.data:
        quote = quote_resp.data[0]
    else:
        quote_id = f"quote_{call_id}"
        supabase_client.table("quotes").insert({
            "id": quote_id,
            "call_id": call_id,
            "company_id": call["company_id"],
            "spec_id": call["spec_id"],
            "outcome": data["outcome"],
            "opening_total": 0.0,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        quote = {"id": quote_id, "opening_total": 0.0}
        
    incoming_total = data.get("total") if data.get("total") is not None else data.get("final_total")
    update_data = {
        "outcome": data["outcome"],
        "pricing_model": data.get("pricing_model") or "flat",
        "moved_because": data.get("moved_because"),
        "conditions": data.get("conditions") or [],
        "notes": data.get("notes"),
        "callback_contact": data.get("callback_contact"),
        "callback_window": data.get("callback_window"),
        "transcript_url": data.get("transcript_url"),
        "recording_url": data.get("recording_url")
    }
    if incoming_total is not None:
        update_data["total"] = incoming_total
        update_data["final_total"] = incoming_total
    if data.get("opening_total") is not None:
        update_data["opening_total"] = data["opening_total"]
    elif quote.get("opening_total") is None or quote.get("opening_total") == 0.0:
        update_data["opening_total"] = incoming_total or 0.0
    if data.get("final_total") is not None:
        update_data["final_total"] = data["final_total"]
        update_data["total"] = data["final_total"]

    supabase_client.table("quotes").update(update_data).eq("id", quote["id"]).execute()
    
    # Load spec and items for red flags
    spec_resp = supabase_client.table("specs").select("*").eq("id", call["spec_id"]).execute()
    spec_dict = from_flat_spec(spec_resp.data[0])
    
    items_resp = supabase_client.table("quote_items").select("*").eq("quote_id", quote["id"]).execute()
    items_list = [{"label": item["label"], "amount": item["amount"]} for item in items_resp.data]
    
    quote_dict = {
        "total": update_data.get("total") or quote.get("total"),
        "final_total": update_data.get("final_total") or quote.get("final_total"),
        "opening_total": update_data.get("opening_total") or quote.get("opening_total"),
        "outcome": update_data["outcome"],
        "pricing_model": update_data["pricing_model"],
        "conditions": update_data["conditions"],
        "notes": update_data["notes"]
    }
    red_flags, red_flag_reasons = run_red_flags_fn(spec_dict, quote_dict, items_list)
    
    supabase_client.table("quotes").update({
        "red_flags": red_flags,
        "red_flag_reasons": red_flag_reasons
    }).eq("id", quote["id"]).execute()
    
    supabase_client.table("calls").update({
        "status": "done",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", call_id).execute()
    
    return {
        "success": True,
        "quote_id": quote["id"],
        "red_flags": red_flags,
        "red_flag_reasons": red_flag_reasons
    }


def init_db():
    """
    Initialize Supabase by ensuring the three companies exist.
    This is idempotent – run it once at startup.
    """
    try:
        # Check if companies already exist
        resp = supabase_client.table("companies").select("id").limit(1).execute()
        if not resp.data:
            logger.info("Seeding companies in Supabase...")
            companies = [
                {"id": "company_1", "name": "Apex Cleaning Co", "persona": "Premium"},
                {"id": "company_2", "name": "Budget Cleaners", "persona": "Lowballer"},
                {"id": "company_3", "name": "Sparkle & Shine", "persona": "Upseller"}
            ]
            supabase_client.table("companies").insert(companies).execute()
            logger.info("Companies seeded successfully.")
        else:
            logger.info("Companies already exist, skipping seed.")
    except Exception as e:
        logger.error(f"Error initializing Supabase: {e}")
        raise

# Call init_db when the module is loaded (optional)
# We'll call it explicitly from main.py on startup.