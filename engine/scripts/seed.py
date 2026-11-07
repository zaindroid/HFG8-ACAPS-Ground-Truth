"""`make seed` -- synthetic experts, a panel, a pulse and one sealed round, printed as a summary.

The store is in-process, so this is mainly a check that seeding works and a way to read the magic links.
The API seeds itself at startup (SEED_ON_START, default true).
"""
from __future__ import annotations

from engine import settings as settings_mod
from engine.seeding import seed_demo
from engine.store import Store, pseudonym_for


def main() -> int:
    settings = settings_mod.load()
    store = Store(k_min=settings.k_min)
    pulse_id = seed_demo(store, settings)

    print(f"pulse        {pulse_id}")
    print(f"experts      {len(store.experts)} (synthetic)")
    print(f"sealed       {store.n_answers(pulse_id)} answers")
    print(f"k_min        {store.k_min}")
    print()
    print("magic links (synthetic panel):")
    for token, (pulse, expert_id) in store.tokens.items():
        expert = store.experts[expert_id]
        state = "sealed" if store.answered(pulse, expert_id) else "open"
        print(f"  /app/e/{token}  {pseudonym_for(expert_id, settings.pseudonym_key):<16} "
              f"{expert.region:<12} {state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
