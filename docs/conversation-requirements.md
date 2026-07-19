# The Four Conversation Requirements — how we address them

The brief requires these four points be handled explicitly and shown in the demo. This doc is the source of truth; the implementing lines live in `prompts/caller.md`.

## 1. Who is the agent speaking for?
Discloses on open: "Hi, I'm an AI assistant calling on behalf of a customer moving from X to Y…"
"Am I talking to a robot?" → honest confirmation plus a value pivot: the agent has the full inventory, so it can give exact details most callers can't. Eval case 3 verifies the quote survives disclosure.

## 2. How does it survive friction?
Short turns (1–2 sentences), barge-in tolerated, interruption-then-resume behavior, vague answers pushed to itemization at most twice, "someone will call back" converted into a named callback window. Eval cases 6 and 7.

## 3. Where does the honesty line sit?
The agent may leverage competing bids — but only bids that exist in the quotes DB, at their exact amounts, fetched via `get_best_bid` at the moment of use. It never invents inventory, never fakes a bid, never misrepresents the job, and never books anything. Eval cases 4 and 5. This is enforced structurally (the tool is the only source of bid data), not just by prompt.

## 4. How does every call end?
One `log_outcome` per call with a structured result: `itemized_quote`, `callback_commitment` (name + window), or `declined_documented`. "They said around two thousand" is a failed call. Eval case 10.
