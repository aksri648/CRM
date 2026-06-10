"""Feature extraction for marketing-goal text.

Pure functions. No I/O. The output of `extract_features` is fed into
SegmentClassifier and is also serialized into the agent response so the
proposal UI can display the extracted features as evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.nlp.lexicons import (
    CONTRACTIONS,
    INTENT_VERBS,
    NEGATION_TOKENS,
    SEGMENT_LEXICONS,
    VALUE_MARKERS,
)


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+|\d+")
_DURATION_RE = re.compile(
    r"(\d+)\s*(day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)
_NUMBER_WORDS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "thirty": 30, "sixty": 60, "ninety": 90,
}
_DURATION_TO_DAYS: dict[str, int] = {
    "day": 1, "days": 1,
    "week": 7, "weeks": 7,
    "month": 30, "months": 30,
    "year": 365, "years": 365,
}


def normalize(text: str) -> str:
    """Lowercase + expand contractions + collapse whitespace.

    Keeps hyphens (so 'cross-sell' stays one token) but strips other punctuation
    that would split phrases. Conservative: doesn't lemmatize — we rely on the
    lexicon covering common surface forms (buyer/buyers, etc.).
    """
    out = text.lower()
    for src, dst in CONTRACTIONS.items():
        out = out.replace(src, dst)
    # Strip punctuation but keep hyphens, apostrophes (already handled), digits.
    out = re.sub(r"[^a-z0-9\s\-']+", " ", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def tokenize(normalized: str) -> list[str]:
    return _TOKEN_RE.findall(normalized)


def ngrams(tokens: list[str], n: int) -> list[str]:
    if n <= 1 or len(tokens) < n:
        return tokens if n == 1 else []
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def extract_time_horizon_days(normalized: str) -> Optional[int]:
    """Find the largest explicit duration mentioned, in days.

    'haven't bought in 60 days' → 60
    'three months' → 90
    Returns None if no duration is mentioned.
    """
    best: Optional[int] = None
    for m in _DURATION_RE.finditer(normalized):
        count = int(m.group(1))
        unit = m.group(2).lower()
        days = count * _DURATION_TO_DAYS[unit]
        if best is None or days > best:
            best = days
    # number-word duration: "three months", "ninety days"
    tokens = tokenize(normalized)
    for i, tok in enumerate(tokens[:-1]):
        if tok in _NUMBER_WORDS:
            unit = tokens[i + 1]
            if unit in _DURATION_TO_DAYS:
                days = _NUMBER_WORDS[tok] * _DURATION_TO_DAYS[unit]
                if best is None or days > best:
                    best = days
    return best


def find_intent_verbs(tokens: list[str]) -> list[str]:
    """Return the intent categories whose verbs appear in the token list."""
    token_set = set(tokens)
    out: list[str] = []
    for category, verbs in INTENT_VERBS.items():
        if any(v in token_set for v in verbs):
            out.append(category)
    return out


def find_value_markers(normalized: str) -> list[str]:
    return [m for m in VALUE_MARKERS if m in normalized]


def find_negations(tokens: list[str]) -> list[int]:
    """Return positions of negation tokens — used to suppress nearby matches."""
    return [i for i, t in enumerate(tokens) if t in NEGATION_TOKENS]


def is_negated(token_index: int, negation_positions: list[int], window: int = 5) -> bool:
    """True if any negation token sits within `window` tokens to the LEFT of the match.

    Window expanded from 3→5 to handle prepended negation phrases such as:
    'Exclude customers who are loyal'  (exclude=idx 0, loyal=idx 4, distance=4).
    Only left-side is checked: right-side negations ('loyal customers — not here')
    are rare and would cause false positives on intra-phrase negators like
    'have not bought' (where 'not' is PART of the phrase, not a negator of it).
    """
    return any(0 <= token_index - p <= window for p in negation_positions)



@dataclass
class SegmentMatch:
    """One matched lexicon entry with its weight and surface form."""
    segment: str
    pattern: str
    weight: float
    negated: bool = False


@dataclass
class GoalFeatures:
    """Structured features extracted from a goal."""
    raw: str
    normalized: str
    tokens: list[str]
    segment_matches: list[SegmentMatch] = field(default_factory=list)
    time_horizon_days: Optional[int] = None
    intent_categories: list[str] = field(default_factory=list)
    value_markers: list[str] = field(default_factory=list)
    negation_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["segment_matches"] = [asdict(m) for m in self.segment_matches]
        return d


def _match_segment_patterns(
    tokens: list[str],
    normalized: str,
    negation_positions: list[int],
) -> list[SegmentMatch]:
    """For each segment, find every lexicon pattern present in the text.

    Multi-word phrases are searched on the normalized string (so spacing matches
    consistently). Single tokens are checked against the token list and inspect
    negation context.
    """
    matches: list[SegmentMatch] = []
    for segment, patterns in SEGMENT_LEXICONS.items():
        for pattern, weight in patterns:
            if " " in pattern or "-" in pattern:
                # Phrase: substring search on normalized text (boundary-aware).
                if re.search(rf"(?<![a-z0-9])" + re.escape(pattern) + r"(?![a-z0-9])", normalized):
                    # Approximate negation check: find first occurrence in tokens.
                    first_token = pattern.split()[0].strip("-")
                    try:
                        idx = tokens.index(first_token)
                        negated = is_negated(idx, negation_positions)
                    except ValueError:
                        negated = False
                    matches.append(SegmentMatch(segment, pattern, weight, negated))
            else:
                # Single token.
                if pattern in tokens:
                    idx = tokens.index(pattern)
                    negated = is_negated(idx, negation_positions)
                    matches.append(SegmentMatch(segment, pattern, weight, negated))
                else:
                    # Handle 'non-<pattern>' as a negated match (e.g. 'non-vip' → loyalty, negated).
                    non_form = f"non-{pattern}"
                    if non_form in tokens:
                        matches.append(SegmentMatch(segment, pattern, weight, negated=True))
    return matches


def extract_features(text: str) -> GoalFeatures:
    """Run the full feature pipeline and return a GoalFeatures object."""
    normalized = normalize(text)
    tokens = tokenize(normalized)
    negation_positions = find_negations(tokens)
    return GoalFeatures(
        raw=text,
        normalized=normalized,
        tokens=tokens,
        segment_matches=_match_segment_patterns(tokens, normalized, negation_positions),
        time_horizon_days=extract_time_horizon_days(normalized),
        intent_categories=find_intent_verbs(tokens),
        value_markers=find_value_markers(normalized),
        negation_count=len(negation_positions),
    )
