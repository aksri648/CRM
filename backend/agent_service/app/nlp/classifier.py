"""Deterministic segment classifier.

Inputs: a marketing goal string.
Outputs: SegmentPrediction = (segment_key, confidence in 0..1, evidence dict).

How it works:

1. Run feature extraction (lexicons.py / features.py).
2. Sum the weights of all non-negated matches per segment.
3. Apply a small set of rule-based disambiguators that resolve known overlaps:
   - "inactive" vs "reactivation": if time_horizon_days is given, < 90 → reactivation,
     >= 90 → inactive. If only one segment has direct matches, pick it.
   - "loyalty" trumps "repeat" when value_markers are present.
   - "welcome" trumps everything when explicit first-purchase / new-customer
     language is used.
4. Normalize the winning score into a 0..1 confidence relative to the runner-up.
5. If no segment scores above the minimum threshold, return the catalog default
   ("inactive") with confidence 0.0 — Atlas knows to treat this as "no signal".

This module has NO external dependencies — pure stdlib. It runs in <1ms.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from app.nlp.features import GoalFeatures, SegmentMatch, extract_features


SEGMENT_KEYS = ("inactive", "repeat", "reactivation", "loyalty", "cross_sell", "welcome")

# Below this raw score we consider the goal "no signal" and decline to choose.
MIN_SIGNAL_SCORE = 1.5

# Boundary (in days) separating reactivation from inactive when both compete.
REACTIVATION_INACTIVE_BOUNDARY_DAYS = 90

# Default segment when no signal is detected — matches Atlas's prior behavior.
NO_SIGNAL_DEFAULT = "inactive"


@dataclass
class SegmentPrediction:
    segment_key: str
    confidence: float
    raw_scores: dict[str, float] = field(default_factory=dict)
    winning_matches: list[SegmentMatch] = field(default_factory=list)
    rationale: str = ""
    features: Optional[dict] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["winning_matches"] = [asdict(m) for m in self.winning_matches]
        return d


def _score_by_segment(features: GoalFeatures) -> dict[str, float]:
    """Sum weights per segment, ignoring negated matches."""
    scores: dict[str, float] = {k: 0.0 for k in SEGMENT_KEYS}
    for m in features.segment_matches:
        if m.negated:
            continue
        scores[m.segment] += m.weight
    return scores


def _apply_rules(scores: dict[str, float], features: GoalFeatures) -> tuple[dict[str, float], list[str]]:
    """Mutate the score dict with disambiguation rules. Returns (new_scores, rule_log)."""
    log: list[str] = []
    scores = dict(scores)  # copy so caller still has raw

    # Rule 1: time horizon < 90 days nudges reactivation over inactive.
    h = features.time_horizon_days
    if h is not None and scores["inactive"] > 0 and scores["reactivation"] > 0:
        if h < REACTIVATION_INACTIVE_BOUNDARY_DAYS:
            scores["reactivation"] += 2.0
            log.append(f"time_horizon={h}d < {REACTIVATION_INACTIVE_BOUNDARY_DAYS}d → boost reactivation")
        else:
            scores["inactive"] += 2.0
            log.append(f"time_horizon={h}d ≥ {REACTIVATION_INACTIVE_BOUNDARY_DAYS}d → boost inactive")
    elif h is not None and h < REACTIVATION_INACTIVE_BOUNDARY_DAYS and scores["reactivation"] == 0 and scores["inactive"] > 0:
        # "Customers dormant for 30 days" → reactivation, even without that word.
        scores["reactivation"] += 1.5
        log.append(f"time_horizon={h}d < {REACTIVATION_INACTIVE_BOUNDARY_DAYS}d → lift reactivation from zero")

    # Rule 2: value markers boost loyalty over repeat when both are in play.
    if features.value_markers:
        if scores["repeat"] > 0 and scores["loyalty"] >= 0:
            scores["loyalty"] += 1.5 + 0.5 * len(features.value_markers)
            log.append(f"value_markers={features.value_markers} → boost loyalty")

    # Rule 3: explicit welcome language wins outright.
    if scores["welcome"] >= 3.0:
        scores["welcome"] += 2.0
        log.append("strong welcome signal → lift welcome")

    # Rule 4: 'cross_sell' wins when goal references basket / category expansion
    # alongside any active-customer language (so "expand basket for repeat
    # customers" → cross_sell, not repeat).
    if scores["cross_sell"] >= 2.0 and scores["repeat"] > 0:
        scores["cross_sell"] += 1.0
        log.append("cross_sell + repeat coexist → prefer cross_sell")

    # Rule 5: intent verb 'acquire' / 'onboard' boost welcome.
    if "acquire" in features.intent_categories and scores["welcome"] >= 0:
        scores["welcome"] += 1.0
        log.append("intent=acquire → boost welcome")
    if "reactivate" in features.intent_categories and scores["reactivation"] >= 0:
        scores["reactivation"] += 1.0
        log.append("intent=reactivate → boost reactivation")
    if "reward" in features.intent_categories and scores["loyalty"] >= 0:
        scores["loyalty"] += 1.0
        log.append("intent=reward → boost loyalty")

    return scores, log


def _confidence_from_scores(scores: dict[str, float], winner_key: str) -> float:
    """Confidence = winner / (winner + runner_up), clipped to [0, 1].

    Pure separation: 1.0 if runner_up is 0 and winner ≥ MIN_SIGNAL_SCORE.
    Tied scores → 0.5. Sub-threshold winner → returned as 0.0 by caller.
    """
    winner = scores[winner_key]
    others = [v for k, v in scores.items() if k != winner_key]
    runner_up = max(others) if others else 0.0
    if winner + runner_up == 0:
        return 0.0
    return round(winner / (winner + runner_up), 3)


def _format_rationale(
    winner: str,
    winner_score: float,
    runner_up_key: Optional[str],
    runner_up_score: float,
    winning_matches: list[SegmentMatch],
    rule_log: list[str],
) -> str:
    patterns = ", ".join(sorted({m.pattern for m in winning_matches})) or "no direct lexicon hits"
    base = f"Classified as '{winner}' (score={winner_score:.1f}) on evidence: {patterns}."
    if runner_up_key:
        base += f" Runner-up '{runner_up_key}' scored {runner_up_score:.1f}."
    if rule_log:
        base += " Rules applied: " + "; ".join(rule_log) + "."
    return base


def classify(goal: str) -> SegmentPrediction:
    """Run the full pipeline and return a SegmentPrediction."""
    features = extract_features(goal)
    raw_scores = _score_by_segment(features)
    adjusted_scores, rule_log = _apply_rules(raw_scores, features)

    winner = max(adjusted_scores, key=lambda k: adjusted_scores[k])
    winner_score = adjusted_scores[winner]

    if winner_score < MIN_SIGNAL_SCORE:
        return SegmentPrediction(
            segment_key=NO_SIGNAL_DEFAULT,
            confidence=0.0,
            raw_scores=adjusted_scores,
            winning_matches=[],
            rationale=(
                f"No segment scored above the minimum signal threshold "
                f"({MIN_SIGNAL_SCORE}). Returning catalog default "
                f"'{NO_SIGNAL_DEFAULT}' with confidence 0."
            ),
            features=features.to_dict(),
        )

    winning_matches = [m for m in features.segment_matches if m.segment == winner and not m.negated]
    runner_others = {k: v for k, v in adjusted_scores.items() if k != winner}
    runner_key = max(runner_others, key=lambda k: runner_others[k]) if runner_others else None
    runner_score = runner_others[runner_key] if runner_key else 0.0
    confidence = _confidence_from_scores(adjusted_scores, winner)

    rationale = _format_rationale(
        winner, winner_score, runner_key, runner_score, winning_matches, rule_log
    )

    return SegmentPrediction(
        segment_key=winner,
        confidence=confidence,
        raw_scores=adjusted_scores,
        winning_matches=winning_matches,
        rationale=rationale,
        features=features.to_dict(),
    )


def classify_batch(goals: list[str]) -> list[SegmentPrediction]:
    return [classify(g) for g in goals]
