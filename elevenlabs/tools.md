# Agent Tool Definitions (paste into ElevenLabs dashboard)

Webhook tools. Person D replaces `BACKEND_URL` with the deployed backend and maps these into the dashboard's tool form. Names, descriptions, and parameter schemas below are the contract — keep them in sync with `schemas/quote.schema.json` and the text simulator (`sim/negotiate.py`), which mocks the same three tools.

## log_quote_item

- **Description:** Log one itemized fee or charge the moving company just quoted, immediately when you hear it. Call once per line item (base labor, truck fee, stairs fee, fuel, materials, insurance, etc).
- **Method/URL:** POST `BACKEND_URL/api/calls/{call_id}/quote-items`
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "label": { "type": "string", "description": "What the charge is for, e.g. 'stairs fee'" },
    "amount": { "type": "number", "description": "Dollar amount" },
    "disclosed_voluntarily": { "type": "boolean", "description": "false if you had to press for it" },
    "negotiable": { "type": "boolean", "description": "true if the rep indicated flexibility" }
  },
  "required": ["label", "amount"]
}
```

## get_best_bid

- **Description:** Get the current best competing itemized bid from other companies, to use as negotiation leverage. Returns null if no competing bid exists yet — in that case you must NOT imply one exists.
- **Method/URL:** GET `BACKEND_URL/api/best-bid?exclude={company_name}`
- **Parameters:** none (company excluded server-side via call context)
- **Returns:** `{ "best_bid": 1850, "company": "...", "binding": true }` or `{ "best_bid": null }`

## log_outcome

- **Description:** Record the structured outcome of this call. MUST be called exactly once before the call ends. Never end a call without it.
- **Method/URL:** POST `BACKEND_URL/api/calls/{call_id}/outcome`
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "outcome": { "type": "string", "enum": ["itemized_quote", "callback_commitment", "declined_documented"] },
    "initial_total": { "type": "number", "description": "First total quoted, before negotiation" },
    "final_total": { "type": "number", "description": "Total after negotiation" },
    "binding": { "type": "boolean" },
    "conditions": { "type": "array", "items": { "type": "string" }, "description": "e.g. 'weekday move only', 'cash deposit required'" },
    "callback_contact": { "type": "string", "description": "Name, if outcome is callback_commitment" },
    "callback_window": { "type": "string", "description": "Time window, if callback_commitment" },
    "notes": { "type": "string" }
  },
  "required": ["outcome"]
}
```
