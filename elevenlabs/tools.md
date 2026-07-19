# ElevenLabs tool contract — Home Cleaning

Replace `BACKEND_URL` with the public HTTPS URL of the FastAPI service. Each caller session must receive `spec_id`, `call_id`, `company_name`, and `job_spec_json` as dynamic variables before it starts.

## save_job_spec

- `POST BACKEND_URL/specs`
- The interviewer sends the complete nested cleaning spec defined in `schemas/job_spec.schema.json` after user confirmation.

## log_quote_item

- `POST BACKEND_URL/api/calls/{call_id}/quote-items`
- Body: `label` (string), `amount` (number), `disclosed_voluntarily` (boolean), `negotiable` (boolean).

## get_best_bid

- `GET BACKEND_URL/api/best-bid?spec_id={spec_id}&exclude={company_name}`
- Returns `{ "best_bid": number | null, "company_name": string | null }`. Never mention a bid when it returns null.

## log_outcome

- `POST BACKEND_URL/api/calls/{call_id}/outcome`
- Body: `outcome` (`quote`, `callback`, or `declined`), `opening_total`, `final_total`, `conditions`, `notes`, `callback_contact`, `callback_window`, `transcript_url`, `recording_url`.

The backend queues call sessions when `/specs/{spec_id}/confirm` is called. Start each company’s session through `POST /calls/start` before giving its `call_id` to ElevenLabs.
