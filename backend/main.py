import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import (
    db_create_spec, db_get_spec, db_update_spec, db_confirm_spec, db_start_call,
    db_get_calls, db_log_quote_item, db_get_best_bid, db_log_outcome,
    init_db   # added
)
from .engine import run_red_flag_rules, rank_quotes
from .intake import extract_document_spec

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="The Negotiator Backend API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialize Supabase (seed companies) on startup ---
@app.on_event("startup")
def startup_event():
    init_db()

# ... (all the route definitions remain identical, no changes) ...
# I'll include them for completeness, but they are unchanged.

# Pydantic Schemas for Requests
class PropertySchema(BaseModel):
    type: str
    sqft: int
    bedrooms: int
    bathrooms: float
    levels: int = 1

class ConditionSchema(BaseModel):
    clutter_level: str
    has_pets: bool
    weeks_since_last_clean: int

class AddOnsSchema(BaseModel):
    fridge: bool = False
    oven: bool = False
    windows: bool = False
    baseboards: bool = False
    laundry: bool = False

class AccessSchema(BaseModel):
    parking: str
    entry_method: str
    walk_up_floor: int = 0

class ScheduleSchema(BaseModel):
    preferred_date: str
    preferred_time_window: str
    flexibility: Optional[str] = None

class JobSpecCreate(BaseModel):
    property: PropertySchema
    clean_type: str
    frequency: str
    condition: ConditionSchema
    add_ons: AddOnsSchema
    access: AccessSchema
    schedule: ScheduleSchema
    open_questions: List[str] = []
    confirmed_by_user: bool = False
    intake_source: str = "voice_interview"

class DocumentIntakeResponse(BaseModel):
    id: str
    missing_fields: List[str]

class CallStartRequest(BaseModel):
    spec_id: str
    company_id: str

class QuoteItemCreate(BaseModel):
    call_id: str
    label: str
    amount: float
    disclosed_voluntarily: bool = True
    negotiable: bool = False

class OutcomeRequest(BaseModel):
    call_id: str
    outcome: str # quote, callback, declined
    pricing_model: Optional[str] = "flat"
    total: Optional[float] = None
    opening_total: Optional[float] = None
    final_total: Optional[float] = None
    moved_because: Optional[str] = None
    conditions: List[str] = []
    notes: Optional[str] = None
    callback_contact: Optional[str] = None
    callback_window: Optional[str] = None
    transcript_url: Optional[str] = None
    recording_url: Optional[str] = None


# --- Routes (unchanged) ---

@app.post("/specs", response_model=Dict[str, Any])
def create_spec(payload: JobSpecCreate):
    try:
        spec_dict = db_create_spec(payload.model_dump())
        return spec_dict
    except Exception as e:
        logger.error(f"Error creating spec: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/specs/{id}", response_model=Dict[str, Any])
def update_spec(id: str, payload: JobSpecCreate):
    updated = db_update_spec(id, payload.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Spec not found")
    return updated

@app.post("/intake/doc", response_model=DocumentIntakeResponse)
async def intake_document(file: UploadFile = File(...)):
    """Extract a cleaning spec from a PDF/image, persist it as a draft, then require review."""
    try:
        spec_data, missing_fields = await extract_document_spec(file)
        saved = db_create_spec(spec_data)
        return {"id": saved["id"], "missing_fields": missing_fields}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document intake failed")
        raise HTTPException(status_code=500, detail=f"Document intake failed: {e}")

@app.get("/health")
def health():
    return {"ok": True, "service": "the-negotiator"}

@app.patch("/specs/{id}/confirm", response_model=Dict[str, Any])
def confirm_spec(id: str):
    try:
        spec_dict = db_confirm_spec(id)
        return spec_dict
    except Exception as e:
        logger.error(f"Error confirming spec: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/specs/{id}", response_model=Dict[str, Any])
def get_spec(id: str):
    spec_dict = db_get_spec(id)
    if not spec_dict:
        raise HTTPException(status_code=404, detail="Spec not found")
    return spec_dict

@app.post("/calls/start", response_model=Dict[str, Any])
def start_call(payload: CallStartRequest):
    try:
        call_info = db_start_call(payload.spec_id, payload.company_id)
        return call_info
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/calls", response_model=List[Dict[str, Any]])
def get_calls(spec_id: str):
    try:
        return db_get_calls(spec_id)
    except Exception as e:
        logger.error(f"Error fetching calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/log_quote_item", response_model=Dict[str, Any])
def log_quote_item(payload: QuoteItemCreate):
    try:
        result = db_log_quote_item(
            call_id=payload.call_id,
            label=payload.label,
            amount=payload.amount,
            disclosed_voluntarily=payload.disclosed_voluntarily,
            negotiable=payload.negotiable
        )
        return result
    except Exception as e:
        logger.error(f"Error logging quote item: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/calls/{call_id}/quote-items")
def api_log_quote_item(call_id: str, payload: Dict[str, Any]):
    item_payload = QuoteItemCreate(
        call_id=call_id,
        label=payload.get("label"),
        amount=payload.get("amount"),
        disclosed_voluntarily=payload.get("disclosed_voluntarily", True),
        negotiable=payload.get("negotiable", False)
    )
    return log_quote_item(item_payload)

@app.get("/tools/get_best_bid", response_model=Dict[str, Any])
def get_best_bid(
    spec_id: str, 
    exclude_company: Optional[str] = Query(None, alias="exclude")
):
    try:
        return db_get_best_bid(spec_id=spec_id, exclude_company=exclude_company)
    except Exception as e:
        logger.error(f"Error fetching best bid: {e}")
        return {"best_bid": None, "company_name": None}

@app.get("/api/best-bid")
def api_get_best_bid(
    spec_id: Optional[str] = None, 
    exclude: Optional[str] = None
):
    if not spec_id:
        return {"best_bid": None, "company_name": None}
    return get_best_bid(spec_id=spec_id, exclude_company=exclude)

@app.post("/tools/log_outcome", response_model=Dict[str, Any])
def log_outcome(payload: OutcomeRequest):
    try:
        result = db_log_outcome(
            call_id=payload.call_id,
            data=payload.model_dump(),
            run_red_flags_fn=run_red_flag_rules
        )
        return result
    except Exception as e:
        logger.error(f"Error logging outcome: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/calls/{call_id}/outcome")
def api_log_outcome(call_id: str, payload: Dict[str, Any]):
    outcome_payload = OutcomeRequest(
        call_id=call_id,
        outcome=payload.get("outcome", "quote"),
        pricing_model=payload.get("pricing_model"),
        total=payload.get("total") or payload.get("final_total"),
        opening_total=payload.get("opening_total") or payload.get("initial_total"),
        final_total=payload.get("final_total"),
        moved_because=payload.get("moved_because"),
        conditions=payload.get("conditions", []),
        notes=payload.get("notes"),
        callback_contact=payload.get("callback_contact"),
        callback_window=payload.get("callback_window"),
        transcript_url=payload.get("transcript_url"),
        recording_url=payload.get("recording_url")
    )
    return log_outcome(outcome_payload)

@app.get("/report/{spec_id}", response_model=Dict[str, Any])
def get_report(spec_id: str):
    spec = db_get_spec(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
        
    calls_list = db_get_calls(spec_id)
    
    serialized_quotes = []
    for call in calls_list:
        q = call.get("quote")
        if q:
            red_flag_reasons = q.get("red_flag_reasons") or [
                flag.replace("_", " ").capitalize() for flag in q.get("red_flags") or []
            ]
            serialized_quotes.append({
                "id": q["id"],
                "company_id": call["company_id"],
                "company_name": call["company_name"],
                "persona": call["persona"],
                "outcome": q["outcome"],
                "pricing_model": q.get("pricing_model"),
                "opening_total": q.get("opening_total"),
                "final_total": q.get("final_total"),
                "total": q.get("total"),
                "moved_because": q.get("moved_because"),
                "conditions": q.get("conditions") or [],
                "red_flags": q.get("red_flags") or [],
                "red_flag_reasons": red_flag_reasons,
                "callback_contact": q.get("callback_contact"),
                "callback_window": q.get("callback_window"),
                "notes": q.get("notes"),
                "transcript_url": q.get("transcript_url"),
                "recording_url": q.get("recording_url"),
                "line_items": q.get("line_items") or []
            })
            
    ranked_quotes = rank_quotes(serialized_quotes)
    
    recommended_deal = None
    for rq in ranked_quotes:
        if rq["outcome"] == "quote":
            price_drop = 0.0
            if rq.get("opening_total") and rq.get("final_total"):
                price_drop = rq["opening_total"] - rq["final_total"]
                
            why_text = f"We recommend {rq['company_name']} because they offer the best rate of ${rq['total']}."
            if price_drop > 0:
                why_text += f" We negotiated them down by ${price_drop:.2f} (from ${rq['opening_total']} to ${rq['final_total']}) using competing bids."
            if rq["red_flags"]:
                why_text += " Note that this quote has warning flags: " + ", ".join(rq["red_flag_reasons"])
            else:
                why_text += " This quote has zero red flags and itemized fees were fully verified."

            recommended_deal = {
                "quote_id": rq["id"],
                "company_name": rq["company_name"],
                "total": rq["total"],
                "price_drop": price_drop,
                "why": why_text
            }
            break

    return {
        "spec": spec,
        "quotes": ranked_quotes,
        "recommended_deal": recommended_deal
    }
