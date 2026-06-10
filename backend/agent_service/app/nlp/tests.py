"""Sanity tests for the deterministic classifier.

Run directly: `python -m app.nlp.tests`
No pytest needed — keeps the demo path simple.
"""
from app.nlp.classifier import classify
from app.nlp.features import extract_features


CASES: list[tuple[str, str]] = [
    # (goal, expected_segment)
    ("Win back customers who haven't bought in 60 days",            "inactive"),
    ("Reward our VIP loyal customers with exclusive access",        "loyalty"),
    ("Onboard new customers with a welcome series",                 "welcome"),
    ("Cross-sell complementary accessories to recent buyers",       "cross_sell"),
    ("Reactivate customers who are starting to lapse",              "reactivation"),
    ("Encourage repeat purchases from active customers",            "repeat"),
    ("Run a campaign for our top spenders and highest LTV cohort",  "loyalty"),
    ("Bring back lost customers who stopped ordering 3 months ago", "inactive"),
    ("Welcome series for brand new signups",                        "welcome"),
    ("Customers dormant for 45 days should be reactivated",         "reactivation"),
]


def main() -> int:
    failures = 0
    for goal, expected in CASES:
        pred = classify(goal)
        ok = pred.segment_key == expected
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{mark}] '{goal[:60]:<60}' → {pred.segment_key:<13} (expected {expected:<13}, conf={pred.confidence})")

    # Spot-check feature extraction surface area too.
    f = extract_features("Win back high-value customers who haven't bought in 90 days")
    print(f"\nFeature extraction sanity:")
    print(f"  time_horizon_days = {f.time_horizon_days}")
    print(f"  intent_categories = {f.intent_categories}")
    print(f"  value_markers     = {f.value_markers}")
    print(f"  segment matches   = {[(m.segment, m.pattern) for m in f.segment_matches]}")

    print(f"\n{'-' * 60}")
    print(f"Result: {len(CASES) - failures}/{len(CASES)} cases passed.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
