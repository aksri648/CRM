"""Deterministic NLP classifier for campaign-audience segmentation.

Public entry points:
    extract_features(text)   -> GoalFeatures
    classify(text)           -> SegmentPrediction
    classify_batch(texts)    -> list[SegmentPrediction]

The classifier is pure-Python, dependency-free, and runs in <1ms per call.
Used by Atlas as a fallback when LLM is unavailable, and exposed as
POST /api/v1/nlp/classify for direct callers and debugging.
"""
from app.nlp.classifier import (
    SegmentPrediction,
    classify,
    classify_batch,
    SEGMENT_KEYS,
)
from app.nlp.features import GoalFeatures, SegmentMatch, extract_features

__all__ = [
    "GoalFeatures",
    "SegmentMatch",
    "SegmentPrediction",
    "SEGMENT_KEYS",
    "extract_features",
    "classify",
    "classify_batch",
]
