"""Every fixture must parse, carry served_from + generated_at, and never expose an aggregate with n < 5."""
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1] / "fixtures"
bad = []
for p in sorted(root.glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    if p.name.endswith("_request.json"):
        continue
    if "served_from" not in d or "generated_at" not in d:
        bad.append(f"{p.name}: missing served_from/generated_at")
    # The disclosure rule is about aggregates: never publish a mean or a distribution computed
    # from fewer than five answers. A round that *refused* to aggregate reports its own n, which
    # is the opposite of a leak -- it is the engine saying it did nothing.
    refused = d.get("reveal_status") == "insufficient_panel"
    aggregated = any(key in d for key in ("mean", "distribution", "weighted_mean"))
    if refused and aggregated:
        bad.append(f"{p.name}: an insufficient panel must carry no aggregate")
    if "n" in d and isinstance(d["n"], int) and d["n"] < 5 and not refused:
        bad.append(f"{p.name}: aggregate with n < 5")
print("\n".join(bad) or f"{len(list(root.glob('*.json')))} fixtures ok")
sys.exit(1 if bad else 0)
