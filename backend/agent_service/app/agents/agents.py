import json
import random
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import MarketingState
from app.agents.llm import llm_available, get_llm
from app.agents.prompts import (
    ATHENA_SYSTEM, ATLAS_SYSTEM, SOPHIA_SYSTEM, MERCURY_SYSTEM,
    NOVA_SYSTEM, COMMAND_CENTRE_SYSTEM,
)
from app.agents.schemas import (
    AthenaOutput, AtlasOutput, SophiaOutput, MercuryOutput,
    NovaOutput, CommandCentreOutput,
)
from app.config import settings
from app.nlp import classify as nlp_classify
from app.utils.logging import logger


# ---------------------------------------------------------------------------
# Catalogues — used both by deterministic fallback AND by LLM-driven agents
# to resolve their classification choice into concrete payloads.
# ---------------------------------------------------------------------------
SEGMENT_CATALOG = {
    "inactive":     {"segment_name": "Inactive High-Value Customers", "criteria": {"max_days_since_order": 60, "min_spent": 5000, "lifecycle_stage": "churned"}, "estimated_reach": 2345},
    "repeat":       {"segment_name": "Repeat Purchase Candidates",    "criteria": {"min_orders": 2, "max_days_since_order": 90, "lifecycle_stage": "active"}, "estimated_reach": 5678},
    "reactivation": {"segment_name": "Reactivation Prospects",        "criteria": {"min_days_since_order": 30, "max_days_since_order": 90, "rfm_scores": ["3-3-3", "4-3-2"]}, "estimated_reach": 3456},
    "loyalty":      {"segment_name": "Loyal Customers",               "criteria": {"min_orders": 5, "min_spent": 10000, "rfm_scores": ["5-5-5", "5-4-5", "4-5-5"]}, "estimated_reach": 1234},
    "cross_sell":   {"segment_name": "Cross-sell Opportunities",      "criteria": {"min_orders": 1, "lifecycle_stage": "active"}, "estimated_reach": 4567},
    "welcome":      {"segment_name": "New Customers",                 "criteria": {"max_orders": 1, "days_since_last_order": 7, "lifecycle_stage": "new"}, "estimated_reach": 890},
}

STRATEGY_CATALOG = {
    "retention":    {"objective": "Increase retention",    "default_offer": "Exclusive loyalty discount", "approach": "Emphasize past value"},
    "reactivation": {"objective": "Re-activate dormant",   "default_offer": "Welcome back offer",         "approach": "Create urgency"},
    "cross_sell":   {"objective": "Cross-sell",            "default_offer": "Curated recommendations",   "approach": "Show complementary products"},
    "upsell":       {"objective": "Increase AOV",          "default_offer": "Premium upgrade",            "approach": "Highlight premium benefits"},
    "loyalty":      {"objective": "Loyalty engagement",    "default_offer": "VIP exclusive access",       "approach": "Make customer feel valued"},
}

CHANNEL_CATALOG = {
    "email":    {"score": 85, "expected_open_rate": 28, "strengths": "Scalable, trackable"},
    "sms":      {"score": 78, "expected_open_rate": 95, "strengths": "Immediate delivery"},
    "whatsapp": {"score": 92, "expected_open_rate": 88, "strengths": "High engagement"},
    "rcs":      {"score": 70, "expected_open_rate": 80, "strengths": "Rich media"},
}


def _agent_trace(state: MarketingState, agent_name: str, output: dict) -> dict:
    return {"agent_trace": [{"agent": agent_name, "output": output, "timestamp": datetime.utcnow().isoformat()}], "current_agent": agent_name}


async def _structured_call(system_prompt: str, user_content: str, schema_cls, temperature: float):
    """Wrapper around ChatGroq structured output. Returns a Pydantic model or raises."""
    llm = get_llm(temperature=temperature)
    bound = llm.with_structured_output(schema_cls)
    return await bound.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ])


# ===========================================================================
# 1. ATHENA — Marketing Director (LLM)
# ===========================================================================
async def athena_agent(state: MarketingState) -> dict:
    goal = state.get("goal", "No goal specified")

    if llm_available():
        try:
            result: AthenaOutput = await _structured_call(
                ATHENA_SYSTEM,
                f"Marketing goal:\n{goal}",
                AthenaOutput,
                temperature=0.2,
            )
            output = {
                "reasoning": result.reasoning,
                "confidence_score": result.confidence_score,
                "supporting_data": {
                    "goal_interpretation": result.intent,
                    "target_outcome": result.target_outcome,
                    "required_specialists": result.required_specialists,
                },
                "predicted_outcome": {"description": "Campaign proposal with full reasoning chain", "expected_quality": "high"},
            }
            return {**_agent_trace(state, "Athena", output), "reasoning": result.reasoning, "confidence": result.confidence_score, "metadata": {"director_analysis": output}}
        except Exception as e:
            logger.warning("athena_llm_failed_falling_back", error=str(e))

    reasoning = f"As Marketing Director, analyzing goal: '{goal}'. Delegating to Atlas, Sophia, Mercury, Nova, Darwin, Apollo."
    output = {"reasoning": reasoning, "confidence_score": 0.92,
              "supporting_data": {"goal_interpretation": goal, "required_specialists": ["atlas", "sophia", "mercury", "nova", "darwin", "apollo"]},
              "predicted_outcome": {"description": "Campaign proposal with full reasoning chain", "expected_quality": "high"}}
    return {**_agent_trace(state, "Athena", output), "reasoning": reasoning, "confidence": 0.92, "metadata": {"director_analysis": output}}


# ===========================================================================
# 2. ATLAS — Segment Identifier (LLM with classification fallback)
# ===========================================================================
async def atlas_agent(state: MarketingState) -> dict:
    goal = state.get("goal", "")
    matched_key: str | None = None
    llm_reasoning: str | None = None
    llm_confidence: float | None = None

    # Step 1 — deterministic NLP classification (runs in <1ms, always available).
    nlp_prediction = nlp_classify(goal) if settings.NLP_CLASSIFIER_ENABLED else None

    # Step 2 — LLM classification (optional).
    if llm_available():
        try:
            result: AtlasOutput = await _structured_call(
                ATLAS_SYSTEM,
                (
                    f"Marketing goal:\n{goal}\n\n"
                    f"Available segments: inactive, repeat, reactivation, loyalty, cross_sell, welcome.\n"
                    "Choose exactly one."
                ),
                AtlasOutput,
                temperature=0.1,
            )
            matched_key = result.segment_key
            llm_reasoning = result.rationale
            llm_confidence = result.confidence_score
        except Exception as e:
            logger.warning("atlas_llm_failed_falling_back", error=str(e))

    # Step 3 — resolve disagreements / pick the final segment.
    nlp_override = False
    if matched_key is None:
        # No LLM result: trust the NLP classifier (or its NO_SIGNAL_DEFAULT).
        matched_key = nlp_prediction.segment_key if nlp_prediction else "inactive"
    elif nlp_prediction and nlp_prediction.segment_key != matched_key:
        # LLM and NLP disagree. Override the LLM only when NLP is highly confident.
        if nlp_prediction.confidence >= settings.NLP_OVERRIDE_THRESHOLD:
            logger.info(
                "atlas_nlp_overrode_llm",
                llm_choice=matched_key, nlp_choice=nlp_prediction.segment_key,
                nlp_confidence=nlp_prediction.confidence,
            )
            matched_key = nlp_prediction.segment_key
            nlp_override = True

    seg = SEGMENT_CATALOG[matched_key]
    reasoning = llm_reasoning or (nlp_prediction.rationale if nlp_prediction else None) \
        or f"Identified segment '{seg['segment_name']}' with ~{seg['estimated_reach']} customers matching: {json.dumps(seg['criteria'])}."
    confidence_val = llm_confidence if llm_confidence is not None else (
        nlp_prediction.confidence if nlp_prediction and nlp_prediction.confidence > 0 else 0.88
    )

    nlp_evidence = nlp_prediction.to_dict() if nlp_prediction else None
    supporting = {
        "matched_segment": seg,
        "segment_coverage_pct": round(seg["estimated_reach"] / 10000 * 100, 1),
        "segment_key": matched_key,
    }
    if nlp_evidence:
        supporting["nlp"] = {
            "predicted_segment": nlp_evidence["segment_key"],
            "confidence": nlp_evidence["confidence"],
            "raw_scores": nlp_evidence["raw_scores"],
            "matched_features": [m["pattern"] for m in nlp_evidence["winning_matches"]],
            "time_horizon_days": nlp_evidence["features"]["time_horizon_days"],
            "intent_categories": nlp_evidence["features"]["intent_categories"],
            "overrode_llm": nlp_override,
        }

    output = {
        "reasoning": reasoning,
        "confidence_score": confidence_val,
        "supporting_data": supporting,
        "predicted_outcome": {"estimated_reach": seg["estimated_reach"], "segment_name": seg["segment_name"]},
    }
    return {
        **_agent_trace(state, "Atlas", output),
        "audience": output,
        "segment": {"name": seg["segment_name"], "criteria": seg["criteria"], "estimated_reach": seg["estimated_reach"], "key": matched_key},
        "reasoning": reasoning,
        "confidence": min(state.get("confidence", 1.0), confidence_val),
    }


# ===========================================================================
# 3. SOPHIA — Strategy designer (LLM)
# ===========================================================================
async def sophia_agent(state: MarketingState) -> dict:
    goal = state.get("goal", "")
    segment = state.get("segment", {}) or {}
    seg_name = segment.get("name", "Unknown segment")
    matched_strategy: str | None = None
    custom_offer: str | None = None
    approach_text: str | None = None
    llm_reasoning: str | None = None
    llm_confidence: float | None = None

    if llm_available():
        try:
            result: SophiaOutput = await _structured_call(
                SOPHIA_SYSTEM,
                (
                    f"Goal: {goal}\n"
                    f"Chosen segment: {seg_name}\n"
                    f"Segment criteria: {json.dumps(segment.get('criteria', {}))}\n"
                    f"Estimated reach: {segment.get('estimated_reach', 0)} customers\n\n"
                    f"Pick strategy and write a SPECIFIC offer for this segment."
                ),
                SophiaOutput,
                temperature=0.3,
            )
            matched_strategy = result.strategy_type
            custom_offer = result.custom_offer
            approach_text = result.approach
            llm_reasoning = result.reasoning
            llm_confidence = result.confidence_score
        except Exception as e:
            logger.warning("sophia_llm_failed_falling_back", error=str(e))

    if matched_strategy is None:
        matched_strategy = next((st for st in STRATEGY_CATALOG if st in goal.lower()), "retention")

    strat = STRATEGY_CATALOG[matched_strategy]
    offer = custom_offer or strat["default_offer"]
    approach = approach_text or strat["approach"]
    reasoning = llm_reasoning or f"Strategy: {strat['objective']}. Offer: {offer}. Approach: {approach}."
    confidence_val = llm_confidence if llm_confidence is not None else 0.90

    output = {
        "reasoning": reasoning,
        "confidence_score": confidence_val,
        "supporting_data": {"strategy_type": matched_strategy, "segment_name": seg_name, "approach": approach, "offer": offer},
        "predicted_outcome": {"expected_impact": "15-20% improvement", "recommended_offer": offer},
    }
    return {**_agent_trace(state, "Sophia", output), "campaign_strategy": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), confidence_val)}


# ===========================================================================
# 4. MERCURY — Channel selector (LLM)
# ===========================================================================
async def mercury_agent(state: MarketingState) -> dict:
    goal = state.get("goal", "")
    segment = state.get("segment", {}) or {}
    strategy = state.get("campaign_strategy", {}) or {}
    strategy_type = (strategy.get("supporting_data", {}) or {}).get("strategy_type", "unknown")
    seg_name = segment.get("name", "Unknown segment")

    matched_channel: str | None = None
    expected_open_rate: int | None = None
    llm_reasoning: str | None = None
    llm_confidence: float | None = None

    if llm_available():
        try:
            result: MercuryOutput = await _structured_call(
                MERCURY_SYSTEM,
                (
                    f"Goal: {goal}\n"
                    f"Segment: {seg_name}\n"
                    f"Strategy: {strategy_type}\n\n"
                    "Choose the single best channel."
                ),
                MercuryOutput,
                temperature=0.2,
            )
            matched_channel = result.channel
            expected_open_rate = result.expected_open_rate_pct
            llm_reasoning = result.rationale
            llm_confidence = result.confidence_score
        except Exception as e:
            logger.warning("mercury_llm_failed_falling_back", error=str(e))

    if matched_channel is None:
        goal_l = goal.lower()
        if "urgent" in goal_l or "reactivation" in goal_l:
            matched_channel = "sms"
        elif "loyalty" in goal_l:
            matched_channel = "whatsapp"
        else:
            matched_channel = "email"

    ch_info = CHANNEL_CATALOG[matched_channel]
    open_rate = expected_open_rate if expected_open_rate is not None else ch_info["expected_open_rate"]
    reasoning = llm_reasoning or f"Recommended channel: {matched_channel.upper()} (score: {ch_info['score']}/100). Expected open rate: {open_rate}%."
    confidence_val = llm_confidence if llm_confidence is not None else 0.87

    output = {
        "reasoning": reasoning,
        "confidence_score": confidence_val,
        "supporting_data": {"recommended_channel": {"name": matched_channel, **ch_info}},
        "predicted_outcome": {"expected_open_rate": open_rate, "expected_ctr": random.randint(12, 25), "channel": matched_channel},
    }
    return {**_agent_trace(state, "Mercury", output), "channel": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), confidence_val)}


# ===========================================================================
# 5. NOVA — Copywriter (LLM) — highest user-perceived quality
# ===========================================================================
async def nova_agent(state: MarketingState) -> dict:
    channel_data = state.get("channel", {}) or {}
    predicted = channel_data.get("predicted_outcome", {}) if isinstance(channel_data, dict) else {}
    channel_name = predicted.get("channel", "email") if isinstance(predicted, dict) else "email"

    segment = state.get("segment", {}) or {}
    seg_name = segment.get("name", "Valued Customers")
    strategy = state.get("campaign_strategy", {}) or {}
    strategy_sup = strategy.get("supporting_data", {}) if isinstance(strategy, dict) else {}
    strategy_type = strategy_sup.get("strategy_type", "retention")
    offer = strategy_sup.get("offer", "an exclusive offer")
    goal = state.get("goal", "")

    variants: list[dict] = []
    llm_reasoning: str | None = None
    llm_confidence: float | None = None

    if llm_available():
        try:
            result: NovaOutput = await _structured_call(
                NOVA_SYSTEM,
                (
                    f"Goal: {goal}\n"
                    f"Segment: {seg_name}\n"
                    f"Strategy: {strategy_type}\n"
                    f"Offer to feature: {offer}\n"
                    f"Channel: {channel_name}\n\n"
                    "Write three variants (emotional, urgency, social_proof). Use the {first_name} placeholder."
                ),
                NovaOutput,
                temperature=0.85,
            )
            variants = [v.model_dump() for v in result.variants]
            llm_reasoning = result.reasoning
            llm_confidence = result.confidence_score
        except Exception as e:
            logger.warning("nova_llm_failed_falling_back", error=str(e))

    if not variants:
        variants = [
            {"variant_type": "A", "style": "emotional", "subject_line": f"{seg_name}, you're truly one of a kind",
             "message_body": f"Hey {{first_name}},\n\nAs one of our most valued {seg_name.lower()}, enjoy an exclusive reward on your next purchase.", "cta_text": "Claim Your Reward"},
            {"variant_type": "B", "style": "urgency", "subject_line": f"Limited time: Special offer for {seg_name}",
             "message_body": f"Hi {{first_name}},\n\nThis exclusive offer for our {seg_name.lower()} won't last forever. Shop now and save big.", "cta_text": "Shop Now"},
            {"variant_type": "C", "style": "social_proof", "subject_line": f"Join {random.randint(1000, 5000)}+ happy customers",
             "message_body": f"Hey {{first_name}},\n\nJoin thousands of satisfied customers who've discovered their perfect match.", "cta_text": "See What's Popular"},
        ]

    reasoning = llm_reasoning or f"Created {len(variants)} variants for {channel_name} targeting {seg_name}."
    confidence_val = llm_confidence if llm_confidence is not None else 0.91
    output = {
        "reasoning": reasoning,
        "confidence_score": confidence_val,
        "supporting_data": {"channel": channel_name, "variant_count": len(variants), "styles_used": [v.get("style") for v in variants]},
        "predicted_outcome": {"best_performing_variant": "A expected to resonate most"},
    }
    return {**_agent_trace(state, "Nova", output), "message_variants": variants, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), confidence_val)}


# ===========================================================================
# 6. DARWIN — A/B test designer (deterministic — pure arithmetic)
# ===========================================================================
async def darwin_agent(state: MarketingState) -> dict:
    variants = state.get("message_variants", []) or []
    reach = 5000
    seg = state.get("segment", {}) or {}
    if isinstance(seg, dict):
        reach = seg.get("estimated_reach", 5000)
    split = max(1, reach // max(len(variants), 1))
    hypothesis = "Variant A (emotional) will outperform others by at least 10% in conversion rate."
    reasoning = f"A/B test with {len(variants)} variants, ~{split} customers each. Hypothesis: {hypothesis}"
    test_plan = {"variants": [v["variant_type"] for v in variants], "split_per_variant": split, "total_audience": reach, "success_metric": "conversion_rate", "min_confidence": 0.95, "hypothesis": hypothesis}
    output = {"reasoning": reasoning, "confidence_score": 0.85, "supporting_data": test_plan,
              "predicted_outcome": {"recommended_winner": "A", "expected_lift": "10-15%", "estimated_duration_days": 14}}
    return {**_agent_trace(state, "Darwin", output), "ab_test": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.85)}


# ===========================================================================
# 7. ORION — Opportunity discovery (deterministic — needs real data first)
# ===========================================================================
async def orion_agent(state: MarketingState) -> dict:
    opportunities = [
        {"opportunity_type": "seasonal_promotion", "title": "Upcoming Festival Season Campaign", "description": "Customers spend 30% more during festivals.", "expected_revenue": 125000, "expected_reach": 8500, "recommended_channel": "whatsapp", "confidence": 0.82},
        {"opportunity_type": "churn_prevention", "title": "At-Risk Customer Reactivation", "description": "2,340 customers showing churn signals.", "expected_revenue": 45000, "expected_reach": 2340, "recommended_channel": "sms", "confidence": 0.78},
        {"opportunity_type": "cross_sell", "title": "Cross-sell Accessories", "description": "3,456 customers who haven't purchased accessories.", "expected_revenue": 32000, "expected_reach": 3456, "recommended_channel": "email", "confidence": 0.85},
    ]
    best = max(opportunities, key=lambda o: o["expected_revenue"])
    reasoning = f"Discovered {len(opportunities)} opportunities. Top: '{best['title']}' (₹{best['expected_revenue']:,})."
    output = {"reasoning": reasoning, "confidence_score": 0.84, "supporting_data": {"opportunities_found": len(opportunities), "top_opportunity": best, "all_opportunities": opportunities},
              "predicted_outcome": {"total_opportunity_value": sum(o["expected_revenue"] for o in opportunities), "total_estimated_reach": sum(o["expected_reach"] for o in opportunities)}}
    return {**_agent_trace(state, "Orion", output), "audience": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.84)}


# ===========================================================================
# 8. APOLLO — Analytics & insights (deterministic — needs real history first)
# ===========================================================================
async def apollo_agent(state: MarketingState) -> dict:
    insights = ["Campaign shows strong potential.", "Recommended channel has top-quartile expected CTR.", "A/B test will identify winner within 14 days."]
    recommendations = ["Monitor first 48 hours.", "Prepare fallback channel.", "Set up real-time analytics."]
    reasoning = f"Analyzed campaign plan. {len(insights)} insights identified."
    output = {"reasoning": reasoning, "confidence_score": 0.93, "supporting_data": {"insights": insights, "recommendations": recommendations},
              "predicted_outcome": {"expected_metrics": {"open_rate": "25-35%", "ctr": "8-15%", "conversion_rate": "3-7%"}, "overall_assessment": "highly promising"}}
    return {**_agent_trace(state, "Apollo", output), "analytics": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.93)}


# ===========================================================================
# 9. COMMAND CENTRE — Conversational status agent (LLM with data context)
# ===========================================================================
def _trim_for_context(payload, key_limit: int = 12, value_chars: int = 400):
    """Aggressively trim large payloads so we don't blow the LLM context window."""
    if isinstance(payload, dict):
        return {k: _trim_for_context(v, key_limit, value_chars) for k, v in list(payload.items())[:key_limit]}
    if isinstance(payload, list):
        return [_trim_for_context(item, key_limit, value_chars) for item in payload[:8]]
    if isinstance(payload, str) and len(payload) > value_chars:
        return payload[:value_chars] + "…"
    return payload


async def command_centre_agent(state: MarketingState) -> dict:
    from app.clients.app_client import (
        fetch_pipeline_status, fetch_dashboard_stats, fetch_campaigns,
        fetch_proposals, fetch_customers, fetch_lifecycle_distribution,
        fetch_channel_analytics, fetch_opportunities, fetch_segments,
        fetch_ab_tests,
    )

    query = state.get("goal", "") or ""
    query_l = query.lower()
    context: dict = {}
    intent = "general"
    conversation_history = state.get("metadata", {}).get("conversation_history", []) or []

    # Step 1: intent detection (keyword-based + LLM fallback)
    if any(w in query_l for w in ["status", "pipeline", "health", "queue", "worker", "system"]):
        intent = "status"
        context["pipeline"] = await fetch_pipeline_status()
        context["dashboard"] = await fetch_dashboard_stats()
    elif any(w in query_l for w in ["customer", "audience", "people", "users", "user", "contact"]):
        intent = "customers"
        search = None
        for prefix in ["customer ", "audience ", "find ", "search ", "show me "]:
            if prefix in query_l:
                search = query_l.split(prefix, 1)[1].strip()
                break
        context["customers"] = await fetch_customers(search=search, page_size=10) if search else await fetch_customers(page_size=10)
        context["lifecycle_distribution"] = await fetch_lifecycle_distribution()
    elif any(w in query_l for w in ["campaign", "dispatch", "send", "message", "notification"]):
        intent = "campaigns"
        context["campaigns"] = await fetch_campaigns(page_size=10)
    elif any(w in query_l for w in ["proposal", "agent", "run", "approval", "pending"]):
        intent = "proposals"
        context["proposals"] = await fetch_proposals()
    elif any(w in query_l for w in ["channel", "analytics", "performance", "metric", "conversion"]):
        intent = "analytics"
        context["channel_analytics"] = await fetch_channel_analytics()
    elif any(w in query_l for w in ["opportunity", "discover", "recommend", "suggestion"]):
        intent = "opportunities"
        context["opportunities"] = await fetch_opportunities(page_size=10)
    elif any(w in query_l for w in ["segment", "group", "filter", "target"]):
        intent = "segments"
        context["segments"] = await fetch_segments(page_size=10)
    elif any(w in query_l for w in ["test", "experiment", "ab", "variant", "split"]):
        intent = "ab_tests"
        context["ab_tests"] = await fetch_ab_tests(page_size=10)
    elif any(w in query_l for w in ["revenue", "sales", "income", "money", "profit"]):
        intent = "revenue"
        context["dashboard"] = await fetch_dashboard_stats()
        context["channel_analytics"] = await fetch_channel_analytics()
    elif any(w in query_l for w in ["report", "summary", "overview", "what's happening", "how are"]):
        intent = "overview"
        context["dashboard"] = await fetch_dashboard_stats()
        context["pipeline"] = await fetch_pipeline_status()
        context["campaigns"] = await fetch_campaigns(page_size=5)
    else:
        intent = "general"
        context["dashboard"] = await fetch_dashboard_stats()
        context["pipeline"] = await fetch_pipeline_status()
        context["campaigns"] = await fetch_campaigns(page_size=5)
        context["customers"] = await fetch_customers(page_size=5)
        context["segments"] = await fetch_segments(page_size=5)

    trimmed = _trim_for_context(context)
    response_text = ""
    llm_confidence = 0.92

    # Step 2: render response. Prefer LLM, fall back to deterministic templates.
    if llm_available():
        try:
            # Build conversation context for LLM
            history_text = ""
            if conversation_history:
                recent = conversation_history[-6:]  # Last 3 exchanges
                history_text = "\n\n".join([
                    f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('text', m.get('content', ''))}"
                    for m in recent
                ])
                history_text = f"\n\nConversation history:\n{history_text}"

            result: CommandCentreOutput = await _structured_call(
                COMMAND_CENTRE_SYSTEM,
                (
                    f"Operator question: {query}{history_text}\n\n"
                    f"Detected intent: {intent}\n\n"
                    f"Live system data (JSON):\n{json.dumps(trimmed, default=str)}"
                ),
                CommandCentreOutput,
                temperature=0.2,
            )
            response_text = result.response
            llm_confidence = result.confidence_score
        except Exception as e:
            logger.warning("command_centre_llm_failed_falling_back", error=str(e))

    if not response_text:
        response_text = _deterministic_command_centre_response(intent, context)

    output = {
        "reasoning": f"Detected intent '{intent}'. Fetched live data from App Service. Composed response{' via LLM' if llm_available() and response_text else ''}.",
        "confidence_score": llm_confidence,
        "supporting_data": trimmed,
        "predicted_outcome": {"intent": intent},
        "response": response_text,
    }
    return {
        **_agent_trace(state, "CommandCentre", output),
        "reasoning": output["reasoning"],
        "confidence": llm_confidence,
        "metadata": {"command_centre_response": output},
    }


def _deterministic_command_centre_response(intent: str, context: dict) -> str:
    """Original keyword-templated rendering, kept as a fallback when the LLM is unavailable."""
    if intent == "status":
        pipeline = context.get("pipeline", {}) or {}
        dashboard = context.get("dashboard", {}) or {}
        return (
            f"**System Status**\n"
            f"- Worker: {pipeline.get('worker_status', 'unknown')}\n"
            f"- Queue Depth: {pipeline.get('queue_depth', 0)} messages\n"
            f"- Retry Queue: {pipeline.get('retry_queue_size', 0)}\n"
            f"- Dead Letter Queue: {pipeline.get('dlq_size', 0)}\n"
            f"- Active Campaigns: {dashboard.get('active_campaigns', 0)}\n"
            f"- Total Customers: {dashboard.get('total_customers', 0):,}"
        )
    if intent == "customers":
        customers_data = context.get("customers", {}) or {}
        lifecycle = context.get("lifecycle_distribution", []) or []
        customers = customers_data.get("customers", [])
        total = customers_data.get("total", 0)
        lines = [f"**Customers Overview** — {total:,} total"]
        for c in customers[:5]:
            name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            lines.append(f"- {name} ({c.get('email', 'N/A')}) — {c.get('lifecycle_stage', 'unknown')}, ₹{c.get('total_spent', 0):,.0f} spent")
        if lifecycle:
            lines.append("\n**Lifecycle Distribution:**")
            for entry in lifecycle[:6]:
                if isinstance(entry, dict):
                    lines.append(f"- {entry.get('stage', entry.get('lifecycle_stage', 'unknown'))}: {entry.get('count', 0)}")
        return "\n".join(lines)
    if intent == "campaigns":
        campaigns_data = context.get("campaigns", {}) or {}
        campaigns = campaigns_data.get("campaigns", [])
        total = campaigns_data.get("total", 0)
        lines = [f"**Campaigns** — {total} total"]
        for c in campaigns[:5]:
            lines.append(f"- {c.get('name', 'Unnamed')} ({c.get('channel', '—')}) — {c.get('status', 'unknown')}")
        return "\n".join(lines)
    if intent == "proposals":
        proposals = context.get("proposals", []) or []
        lines = [f"**Agent Proposals & Runs** — {len(proposals)} recent"]
        for p in proposals[:5]:
            created = (p.get("created_at") or "")[:19].replace("T", " ")
            lines.append(f"- {p.get('run_type', 'unknown')}: {p.get('status', 'unknown')} ({created})")
        return "\n".join(lines)
    if intent == "analytics":
        channels = context.get("channel_analytics", []) or []
        lines = [f"**Channel Performance** — {len(channels)} channels"]
        for ch in channels:
            lines.append(
                f"- {ch.get('channel', 'unknown')}: {ch.get('sent_count', 0):,} sent, "
                f"{ch.get('open_count', 0):,} opened, {ch.get('conversion_count', 0):,} converted, "
                f"₹{ch.get('revenue', 0):,.0f} revenue"
            )
        return "\n".join(lines)
    if intent == "opportunities":
        opp_data = context.get("opportunities", {}) or {}
        opportunities = opp_data.get("opportunities", [])
        total = opp_data.get("total", 0)
        lines = [f"**Opportunities** — {total} total"]
        for o in opportunities[:5]:
            lines.append(f"- {o.get('title', 'Unnamed')} ({o.get('opportunity_type', 'general')}) — {o.get('status', 'pending')}, ₹{o.get('expected_revenue', 0):,.0f}")
        return "\n".join(lines)

    pipeline = context.get("pipeline", {}) or {}
    dashboard = context.get("dashboard", {}) or {}
    return (
        f"I can help you with:\n"
        f"1. **System Status** — Worker: {pipeline.get('worker_status', 'unknown')}, Queue: {pipeline.get('queue_depth', 0)}\n"
        f"2. **Customers** — {dashboard.get('total_customers', 0):,} total, segmented by lifecycle stage\n"
        f"3. **Campaigns** — {dashboard.get('active_campaigns', 0)} active, across multiple channels\n"
        f"4. **Channel Analytics** — Performance breakdown by channel\n"
        f"5. **Agent Proposals** — AI campaign proposals and approvals\n"
        f"6. **Opportunities** — AI-discovered marketing opportunities\n\n"
        f"Try asking: \"What is the system status?\", \"Show me customers\", "
        f"\"How are my campaigns doing?\", or \"List recent proposals\"."
    )


# ===========================================================================
# 10. SENTINEL — Compliance gate (deterministic — it's a state transition)
# ===========================================================================
async def sentinel_agent(state: MarketingState) -> dict:
    trace = state.get("agent_trace", []) or []
    seg = state.get("segment", {}) or {}
    seg_name = seg.get("name", "Unknown") if isinstance(seg, dict) else "Unknown"
    ch = state.get("channel", {}) or {}
    ch_name = ch.get("predicted_outcome", {}).get("channel", "Unknown") if isinstance(ch, dict) else "Unknown"
    confidence = state.get("confidence", 0.0)

    proposal = {"goal": state.get("goal"), "segment": seg_name, "channel": ch_name, "confidence_score": round(confidence, 2),
                "agent_count": len(trace), "requires_approval": True,
                "proposal_summary": f"AI campaign targeting {seg_name} via {ch_name}. Confidence: {confidence:.0%}. Requires approval."}
    reasoning = f"Sentinel review: {len(trace)} agents. Target: {seg_name} via {ch_name}. Confidence: {confidence:.0%}. Rules enforced: no autonomous launch."
    output = {"reasoning": reasoning, "confidence_score": 1.0,
              "supporting_data": {"agents_involved": [t.get("agent") for t in trace], "compliance_check": "passed"},
              "predicted_outcome": {"proposal_ready": True, "approval_required": True}}
    return {**_agent_trace(state, "Sentinel", output), "proposal": proposal, "approval_status": "pending", "reasoning": reasoning, "confidence": 1.0}
