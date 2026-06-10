"""Lexicons for deterministic segment classification.

A keyword/phrase dictionary tuned to the 6 segment definitions used by Atlas.
Each entry: (token-or-phrase, weight). Higher weight = stronger evidence.
Multi-word phrases are matched as bigrams/trigrams after normalization.

The lexicon is intentionally narrow — high precision over recall. When a goal
contains no strong signal, the classifier returns low confidence and Atlas
falls back to its catalog default.
"""
from __future__ import annotations

# Each segment is a list of (pattern, weight) tuples.
# Phrases (multi-word) are matched after tokenization; the matcher checks every
# n-gram (n = len(phrase tokens)) against the goal text.
SEGMENT_LEXICONS: dict[str, list[tuple[str, float]]] = {
    "inactive": [
        ("inactive",          3.0),
        ("churn",             3.0),
        ("churned",           3.0),
        ("dormant",           3.0),
        ("lapsed",            2.5),
        ("lost customer",     3.0),
        ("lost customers",    3.0),
        ("haven't bought",    3.0),
        ("have not bought",   3.0),
        ("haven't ordered",   3.0),
        ("have not ordered",  3.0),
        ("haven't purchased", 3.0),
        ("stopped buying",    3.0),
        ("stopped ordering",  3.0),
        ("no recent order",   2.5),
        ("no recent orders",  2.5),
        ("win back",          2.5),
        ("winback",           2.5),
        ("bring back",        2.0),
        ("recover",           1.5),
        ("re-engage",         1.5),
        ("reengage",          1.5),
    ],
    "repeat": [
        ("repeat",            3.0),
        ("repeat buyer",      3.0),
        ("repeat buyers",     3.0),
        ("repeat purchase",   3.0),
        ("frequent buyer",    2.5),
        ("frequent buyers",   2.5),
        ("frequent customer", 2.5),
        ("recent buyer",      2.0),
        ("recent buyers",     2.0),
        ("multiple orders",   2.5),
        ("active customer",   2.0),
        ("active customers",  2.0),
        ("regular customer",  2.0),
        ("regular customers", 2.0),
        ("recurring",         1.5),
    ],
    "reactivation": [
        ("reactivate",        3.0),
        ("reactivated",       3.0),
        ("reactivating",      3.0),
        ("reactivation",      3.0),
        ("re-activate",       3.0),
        ("re-engagement",     2.0),
        ("revive",            2.0),
        ("at risk",           2.5),
        ("at-risk",           2.5),
        ("about to churn",    3.0),
        ("slipping away",     2.5),
        ("declining",         1.5),
        ("less active",       2.0),
        ("getting cold",      2.0),
        ("starting to lapse", 2.5),
    ],
    "loyalty": [
        ("loyal",             3.0),
        ("loyalty",           3.0),
        ("vip",               3.0),
        ("v.i.p",             3.0),
        ("best customer",     3.0),
        ("best customers",    3.0),
        ("top customer",      3.0),
        ("top customers",     3.0),
        ("top spender",       3.0),
        ("top spenders",      3.0),
        ("high value",        2.5),
        ("high-value",        2.5),
        ("premium",           2.0),
        ("reward",            2.0),
        ("rewarding",         2.0),
        ("most valuable",     3.0),
        ("highest lifetime",  2.5),
        ("lifetime value",    1.5),
        ("ltv",               1.5),
        ("hall of fame",      2.0),
    ],
    "cross_sell": [
        ("cross sell",        3.0),
        ("cross-sell",        3.0),
        ("cross-selling",     3.0),
        ("upsell",            2.5),
        ("up-sell",           2.5),
        ("upselling",         2.5),
        ("complementary",     2.0),
        ("bundle",            1.5),
        ("bundles",           1.5),
        ("add on",            2.0),
        ("add-on",            2.0),
        ("recommend",         1.0),
        ("recommendation",    1.0),
        ("expand basket",     2.5),
        ("basket size",       2.0),
        ("new category",      2.0),
        ("related products",  2.0),
        ("accessories",       1.5),
    ],
    "welcome": [
        ("welcome",           3.0),
        ("new customer",      3.0),
        ("new customers",     3.0),
        ("first time",        3.0),
        ("first-time",        3.0),
        ("first purchase",    3.0),
        ("first order",       3.0),
        ("onboard",           2.5),
        ("onboarding",        2.5),
        ("signed up",         2.5),
        ("just joined",       2.5),
        ("just registered",   2.5),
        ("brand new",         2.5),
        ("newcomer",          2.5),
        ("newcomers",         2.5),
        ("greeting",          1.5),
        ("intro",             1.5),
    ],
}


# Words that act as intent verbs across the goal — used as a feature category
# for transparency, but also bias certain segments. Includes common conjugations
# so we don't need a stemmer (which would introduce false positives).
INTENT_VERBS: dict[str, list[str]] = {
    "retain":      ["retain", "retained", "retaining", "keep", "keeping", "maintain", "maintaining", "hold"],
    "reactivate":  ["reactivate", "reactivated", "reactivating", "revive", "reviving", "win", "winback", "bring"],
    "acquire":     ["acquire", "acquired", "acquiring", "convert", "converting", "attract", "attracting", "onboard", "onboarding", "welcome", "welcoming"],
    "reward":      ["reward", "rewarded", "rewarding", "celebrate", "celebrating", "thank", "appreciate"],
    "expand":      ["expand", "expanding", "grow", "growing", "increase", "increasing", "cross-sell", "upsell"],
}


# Patterns that indicate the operator referenced a customer-value tier.
VALUE_MARKERS: list[str] = [
    "high value", "high-value", "high spending", "high spenders",
    "vip", "premium", "top tier", "top-tier",
    "low value", "low-value", "budget", "discount seeker", "discount seekers",
]


# Tokens that flip the polarity of a downstream pattern. Currently a small set;
# the matcher applies negation suppression within a 3-token window.
NEGATION_TOKENS: set[str] = {"not", "no", "never", "without", "exclude", "excluding", "except"}


# Contractions we expand before tokenizing so "haven't" matches "have not".
CONTRACTIONS: dict[str, str] = {
    "haven't":   "have not",
    "hasn't":    "has not",
    "hadn't":    "had not",
    "don't":     "do not",
    "doesn't":   "does not",
    "didn't":    "did not",
    "won't":     "will not",
    "wouldn't":  "would not",
    "shouldn't": "should not",
    "couldn't":  "could not",
    "isn't":     "is not",
    "aren't":    "are not",
    "wasn't":    "was not",
    "weren't":   "were not",
    "can't":     "can not",
    "cannot":    "can not",
    "they're":   "they are",
    "we're":     "we are",
    "it's":      "it is",
    "that's":    "that is",
    "i'm":       "i am",
}
