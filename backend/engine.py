import os
import yaml
from typing import List, Dict, Any, Tuple

# Path to verticals/cleaning.yaml
CLEANING_YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "verticals", "cleaning.yaml"
)

def load_cleaning_config() -> Dict[str, Any]:
    if not os.path.exists(CLEANING_YAML_PATH):
        # Return fallback configuration if file doesn't exist
        return {
            "benchmarks": {
                "standard": {"low": 120, "median": 180, "high": 280},
                "deep": {"low": 200, "median": 350, "high": 500},
                "move_out": {"low": 250, "median": 425, "high": 600}
            }
        }
    with open(CLEANING_YAML_PATH, "r") as f:
        return yaml.safe_load(f)

def run_red_flag_rules(spec_data: Dict[str, Any], quote_data: Dict[str, Any], line_items: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """
    Evaluates red flags on a quote based on the job spec and quote details.
    Returns:
        red_flags (list of strings): IDs of triggered flags.
        red_flag_reasons (list of strings): User-facing explanation/warning for each triggered flag.
    """
    cfg = load_cleaning_config()
    benchmarks = cfg.get("benchmarks", {})
    
    red_flags = []
    red_flag_reasons = []
    
    clean_type = spec_data.get("clean_type", "standard")
    # Normalize clean_type key for benchmarks dict
    bench_key = clean_type.replace("-", "_")
    if bench_key not in benchmarks:
        bench_key = "standard"
        
    median = benchmarks.get(bench_key, {}).get("median", 180)
    total = quote_data.get("total") or quote_data.get("final_total") or quote_data.get("opening_total")
    outcome = quote_data.get("outcome", "")
    pricing_model = quote_data.get("pricing_model", "")
    conditions = quote_data.get("conditions", []) or []
    notes = quote_data.get("notes", "") or ""
    
    # 1. Lowball flag: total < 70% of median for clean type
    if outcome == "quote" and total is not None:
        if total < 0.70 * median:
            red_flags.append("lowball")
            red_flag_reasons.append(
                f"Lowball quote ({total} < 70% of median {median} for {clean_type} clean). "
                "Industry guidance treats this as a warning sign of future on-arrival price increases or low quality."
            )
            
    # 2. Standard clean on first time job flag
    # If clean_type is standard and frequency is one_time and weeks_since_last_clean > 4
    weeks = spec_data.get("condition", {}).get("weeks_since_last_clean", 0)
    frequency = spec_data.get("frequency", "")
    if clean_type == "standard" and frequency == "one_time" and weeks > 4:
        red_flags.append("standard_first_time")
        red_flag_reasons.append(
            "Standard clean quoted for a first-time clean (last clean was over 4 weeks ago). "
            "High risk that cleaners will claim it requires a deep clean on arrival and upcharge you."
        )
        
    # 3. Uncapped hourly flag: pricing model is hourly and total is not set
    if outcome == "quote" and pricing_model == "hourly" and (total is None or total <= 0):
        red_flags.append("uncapped_hourly")
        red_flag_reasons.append(
            "Uncapped hourly rate with no maximum total price guarantee."
        )
        
    # 4. Refuses to itemize flag: outcome is quote but we have 0 line items
    if outcome == "quote" and len(line_items) == 0:
        red_flags.append("no_itemization")
        red_flag_reasons.append(
            "Refuses to itemize fees. A quote without a breakdown of services makes unexpected charges likely."
        )
        
    # 5. Cash only flag: conditions or notes mention cash-only or no written receipt/quote
    cash_signals = ["cash only", "cash-only", "requires cash", "cash deposit"]
    notes_lower = notes.lower()
    conds_lower = [str(c).lower() for c in conditions]
    
    is_cash_only = any(sig in notes_lower for sig in cash_signals) or any(
        any(sig in c for sig in cash_signals) for c in conds_lower
    )
    if is_cash_only:
        red_flags.append("cash_only")
        red_flag_reasons.append(
            "Requires cash payment. Cash-only demands correlate with a lack of formal dispute options and potential scams."
        )
        
    return red_flags, red_flag_reasons

def rank_quotes(quotes_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks quotes:
    - Sorting criteria:
      1. Outcome must be 'quote' first. 'callback' and 'declined' go to the bottom.
      2. Non-flagged quotes are placed above flagged quotes (flagged demoted).
      3. Within those groups, sort by total ascending.
      4. Items with no total (e.g. callback/declined) are sorted at the very end.
    """
    def get_sort_key(q: Dict[str, Any]):
        outcome = q.get("outcome", "")
        # Group 1: successful quotes
        # Group 2: callbacks
        # Group 3: declines
        outcome_rank = 0
        if outcome == "quote":
            outcome_rank = 0
        elif outcome == "callback":
            outcome_rank = 1
        else:
            outcome_rank = 2
            
        has_flags = 1 if len(q.get("red_flags", []) or []) > 0 else 0
        total = q.get("total") or q.get("final_total") or q.get("opening_total")
        if total is None:
            total = float("inf")
            
        return (outcome_rank, has_flags, total)

    sorted_quotes = sorted(quotes_list, key=get_sort_key)
    return sorted_quotes
