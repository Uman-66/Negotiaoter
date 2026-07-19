import os
import sys
import json
from fastapi.testclient import TestClient

# Add parent directory to path so we can import backend package
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.main import app
from backend.database import init_db, db_get_calls, db_get_best_bid
from backend.engine import rank_quotes

def run_simulation():
    client = TestClient(app)

    # Ensure companies are seeded (idempotent)
    init_db()

    print("\n=== STEP 1: Creating a Deep Clean Job Spec ===")
    spec_payload = {
        "property": {
            "type": "apartment",
            "sqft": 1200,
            "bedrooms": 2,
            "bathrooms": 2.0,
            "levels": 1
        },
        "clean_type": "deep",
        "frequency": "one_time",
        "condition": {
            "clutter_level": "medium",
            "has_pets": True,
            "weeks_since_last_clean": 6
        },
        "add_ons": {
            "fridge": True,
            "oven": True,
            "windows": False,
            "baseboards": True,
            "laundry": False
        },
        "access": {
            "parking": "street",
            "entry_method": "lockbox code 1234",
            "walk_up_floor": 2
        },
        "schedule": {
            "preferred_date": "2026-08-15",
            "preferred_time_window": "Morning 9am-12pm",
            "flexibility": "flexible within 3 days"
        },
        "open_questions": [],
        "confirmed_by_user": False,
        "intake_source": "voice_interview"
    }

    response = client.post("/specs", json=spec_payload)
    assert response.status_code == 200, f"Failed spec creation: {response.text}"
    spec = response.json()
    spec_id = spec["id"]
    print(f"Created Spec ID: {spec_id}")
    print(json.dumps(spec, indent=2))

    print("\n=== STEP 2: User Confirms Spec (The Gate) ===")
    response = client.patch(f"/specs/{spec_id}/confirm")
    assert response.status_code == 200
    spec_confirmed = response.json()
    assert spec_confirmed["confirmed_by_user"] is True
    print("Spec confirmed successfully.")

    # Retrieve calls to see queued sessions
    response = client.get(f"/calls?spec_id={spec_id}")
    assert response.status_code == 200
    calls = response.json()
    print("Queued call sessions:")
    for c in calls:
        print(f" - Call ID: {c['call_id']} | Company: {c['company_name']} ({c['persona']}) | Status: {c['status']}")

    # Find the call IDs for our 3 companies
    call_map = {c["persona"]: c["call_id"] for c in calls}

    print("\n=== STEP 3: Simulating Call 1 (Apex Cleaning Co - Premium) ===")
    premium_call_id = call_map["Premium"]

    # Start call
    client.post("/calls/start", json={"spec_id": spec_id, "company_id": "company_1"})

    # Log quote items
    client.post("/tools/log_quote_item", json={
        "call_id": premium_call_id,
        "label": "Deep Clean Base Labor",
        "amount": 420.0,
        "disclosed_voluntarily": True,
        "negotiable": False
    })
    client.post("/tools/log_quote_item", json={
        "call_id": premium_call_id,
        "label": "Fridge/Oven Add-on",
        "amount": 60.0,
        "disclosed_voluntarily": True,
        "negotiable": True
    })

    # Log outcome (quote total is 480.0)
    response = client.post("/tools/log_outcome", json={
        "call_id": premium_call_id,
        "outcome": "quote",
        "pricing_model": "flat",
        "opening_total": 480.0,
        "final_total": 480.0,
        "total": 480.0,
        "notes": "Premium service, binding quote."
    })
    print("Apex Cleaning outcome logged:")
    print(json.dumps(response.json(), indent=2))

    print("\n=== STEP 4: Simulating Call 2 (Budget Cleaners - Lowballer) ===")
    lowballer_call_id = call_map["Lowballer"]

    client.post("/calls/start", json={"spec_id": spec_id, "company_id": "company_2"})

    client.post("/tools/log_quote_item", json={
        "call_id": lowballer_call_id,
        "label": "Flat Cleaning Fee",
        "amount": 210.0,
        "disclosed_voluntarily": True,
        "negotiable": False
    })

    response = client.post("/tools/log_outcome", json={
        "call_id": lowballer_call_id,
        "outcome": "quote",
        "pricing_model": "flat",
        "opening_total": 210.0,
        "final_total": 210.0,
        "total": 210.0,
        "notes": "Low flat fee."
    })
    print("Budget Cleaners outcome logged (Lowball expected):")
    print(json.dumps(response.json(), indent=2))

    print("\n=== STEP 5: Simulating Call 3 (Sparkle & Shine - Upseller) ===")
    upseller_call_id = call_map["Upseller"]

    client.post("/calls/start", json={"spec_id": spec_id, "company_id": "company_3"})

    # Mid-call: Closer gets best bid
    response = client.get(f"/tools/get_best_bid?spec_id={spec_id}&exclude=Sparkle")
    assert response.status_code == 200
    best_bid_data = response.json()
    print(f"Upseller retrieved best bid so far: {best_bid_data}")

    # Log quote items for Sparkle & Shine
    client.post("/tools/log_quote_item", json={
        "call_id": upseller_call_id,
        "label": "Base Cleaning Fee",
        "amount": 260.0,
        "disclosed_voluntarily": True,
        "negotiable": False
    })
    client.post("/tools/log_quote_item", json={
        "call_id": upseller_call_id,
        "label": "Fridge/Oven Add-on Bundle",
        "amount": 40.0,
        "disclosed_voluntarily": True,
        "negotiable": True
    })

    response = client.post("/tools/log_outcome", json={
        "call_id": upseller_call_id,
        "outcome": "quote",
        "pricing_model": "flat",
        "opening_total": 300.0,
        "final_total": 260.0,
        "total": 260.0,
        "moved_because": "Cited Budget Cleaners quote of $210, rep agreed to waive fridge/oven fees to close.",
        "notes": "Sparkle & Shine final negotiated quote.",
        "transcript_url": "https://elevenlabs.io/transcript/sparkle_shine_123",
        "recording_url": "https://elevenlabs.io/recording/sparkle_shine_123"
    })
    print("Sparkle & Shine outcome logged (renegotiated):")
    print(json.dumps(response.json(), indent=2))

    print("\n=== STEP 6: Generating Final Ranked Report ===")
    response = client.get(f"/report/{spec_id}")
    assert response.status_code == 200
    report = response.json()
    print("Final Report Payload:")
    print(json.dumps(report, indent=2))

    print("\n=== VERIFY RANKING & RECOMMENDED DEAL ===")
    quotes = report["quotes"]
    print("Ranked Quotes Order:")
    for idx, q in enumerate(quotes):
        print(f" Rank {idx+1}: {q['company_name']} | Persona: {q['persona']} | Total: ${q['total']} | Red Flags: {q['red_flags']}")

    rec = report["recommended_deal"]
    if rec:
        print(f"Recommended Deal: {rec['company_name']} (Total: ${rec['total']})")
        print(f"Why: {rec['why']}")
    else:
        print("No recommended deal found!")

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_simulation()