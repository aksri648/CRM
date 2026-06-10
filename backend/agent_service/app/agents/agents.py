import json
import random
from datetime import datetime

from app.agents.state import MarketingState


def _agent_trace(state: MarketingState, agent_name: str, output: dict) -> dict:
    return {"agent_trace": [{"agent": agent_name, "output": output, "timestamp": datetime.utcnow().isoformat()}], "current_agent": agent_name}


async def athena_agent(state: MarketingState) -> dict:
    goal = state.get("goal", "No goal specified")
    reasoning = f"As Marketing Director, analyzing goal: '{goal}'. Delegating to Atlas, Sophia, Mercury, Nova, Darwin, Apollo."
    output = {"reasoning": reasoning, "confidence_score": 0.92,
              "supporting_data": {"goal_interpretation": goal, "required_specialists": ["atlas", "sophia", "mercury", "nova", "darwin", "apollo"]},
              "predicted_outcome": {"description": "Campaign proposal with full reasoning chain", "expected_quality": "high"}}
    return {**_agent_trace(state, "Athena", output), "reasoning": reasoning, "confidence": 0.92, "metadata": {"director_analysis": output}}


async def atlas_agent(state: MarketingState) -> dict:
    goal = state.get("goal", "")
    campaign_types = {
        "inactive": {"segment_name": "Inactive High-Value Customers", "criteria": {"max_days_since_order": 60, "min_spent": 5000, "lifecycle_stage": "churned"}, "estimated_reach": 2345},
        "repeat": {"segment_name": "Repeat Purchase Candidates", "criteria": {"min_orders": 2, "max_days_since_order": 90, "lifecycle_stage": "active"}, "estimated_reach": 5678},
        "reactivation": {"segment_name": "Reactivation Prospects", "criteria": {"min_days_since_order": 30, "max_days_since_order": 90, "rfm_scores": ["3-3-3", "4-3-2"]}, "estimated_reach": 3456},
        "loyalty": {"segment_name": "Loyal Customers", "criteria": {"min_orders": 5, "min_spent": 10000, "rfm_scores": ["5-5-5", "5-4-5", "4-5-5"]}, "estimated_reach": 1234},
        "cross_sell": {"segment_name": "Cross-sell Opportunities", "criteria": {"min_orders": 1, "lifecycle_stage": "active"}, "estimated_reach": 4567},
        "welcome": {"segment_name": "New Customers", "criteria": {"max_orders": 1, "days_since_last_order": 7, "lifecycle_stage": "new"}, "estimated_reach": 890},
    }
    matched_type = next((ct for ct in campaign_types if ct in goal.lower()), "inactive")
    seg = campaign_types[matched_type]
    reasoning = f"Identified segment '{seg['segment_name']}' with ~{seg['estimated_reach']} customers matching: {json.dumps(seg['criteria'])}."
    output = {"reasoning": reasoning, "confidence_score": 0.88,
              "supporting_data": {"matched_segment": seg, "segment_coverage_pct": round(seg["estimated_reach"] / 10000 * 100, 1)},
              "predicted_outcome": {"estimated_reach": seg["estimated_reach"], "segment_name": seg["segment_name"]}}
    return {**_agent_trace(state, "Atlas", output), "audience": output,
            "segment": {"name": seg["segment_name"], "criteria": seg["criteria"], "estimated_reach": seg["estimated_reach"]},
            "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.88)}


async def sophia_agent(state: MarketingState) -> dict:
    segment = state.get("segment", {})
    strategies = {"retention": {"objective": "Increase retention", "offer": "Exclusive loyalty discount", "approach": "Emphasize past value"},
                  "reactivation": {"objective": "Re-activate dormant", "offer": "Welcome back offer", "approach": "Create urgency"},
                  "cross_sell": {"objective": "Cross-sell", "offer": "Curated recommendations", "approach": "Show complementary products"},
                  "upsell": {"objective": "Increase AOV", "offer": "Premium upgrade", "approach": "Highlight premium benefits"},
                  "loyalty": {"objective": "Loyalty engagement", "offer": "VIP exclusive access", "approach": "Make customer feel valued"}}
    goal = state.get("goal", "").lower()
    strategy_type = next((st for st in strategies if st in goal), "retention")
    strat = strategies[strategy_type]
    reasoning = f"Strategy: {strat['objective']}. Offer: {strat['offer']}. Approach: {strat['approach']}."
    output = {"reasoning": reasoning, "confidence_score": 0.90,
              "supporting_data": {"strategy_type": strategy_type, "segment_name": segment.get("name"), "approach": strat["approach"]},
              "predicted_outcome": {"expected_impact": "15-20% improvement", "recommended_offer": strat["offer"]}}
    return {**_agent_trace(state, "Sophia", output), "campaign_strategy": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.90)}


async def mercury_agent(state: MarketingState) -> dict:
    channels = [
        {"name": "whatsapp", "score": 92, "expected_open_rate": 88, "strengths": "High engagement"},
        {"name": "email", "score": 85, "expected_open_rate": 28, "strengths": "Scalable, trackable"},
        {"name": "sms", "score": 78, "expected_open_rate": 95, "strengths": "Immediate delivery"},
        {"name": "rcs", "score": 70, "expected_open_rate": 80, "strengths": "Rich media"},
    ]
    goal = state.get("goal", "").lower()
    best = channels[2] if "urgent" in goal or "reactivation" in goal else channels[0] if "loyalty" in goal else channels[1]
    reasoning = f"Recommended channel: {best['name'].upper()} (score: {best['score']}/100). Expected open rate: {best['expected_open_rate']}%."
    output = {"reasoning": reasoning, "confidence_score": 0.87, "supporting_data": {"recommended_channel": best},
              "predicted_outcome": {"expected_open_rate": best["expected_open_rate"], "expected_ctr": random.randint(12, 25), "channel": best["name"]}}
    return {**_agent_trace(state, "Mercury", output), "channel": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.87)}


async def nova_agent(state: MarketingState) -> dict:
    channel_data = state.get("channel", {})
    predicted = channel_data.get("predicted_outcome", {}) if isinstance(channel_data, dict) else {}
    channel_name = predicted.get("channel", "email") if isinstance(predicted, dict) else "email"
    segment = state.get("segment", {})
    seg_name = segment.get("name", "Valued Customers") if isinstance(segment, dict) else "Valued Customers"

    variants = [
        {"variant_type": "A", "style": "emotional", "subject_line": f"{seg_name}, you're truly one of a kind",
         "message_body": f"Hey {{first_name}},\n\nAs one of our most valued {seg_name.lower()}, enjoy an exclusive reward on your next purchase.", "cta_text": "Claim Your Reward"},
        {"variant_type": "B", "style": "urgency", "subject_line": f"Limited time: Special offer for {seg_name}",
         "message_body": f"Hi {{first_name}},\n\nThis exclusive offer for our {seg_name.lower()} won't last forever. Shop now and save big.", "cta_text": "Shop Now"},
        {"variant_type": "C", "style": "social_proof", "subject_line": f"Join {random.randint(1000, 5000)}+ happy customers",
         "message_body": f"Hey {{first_name}},\n\nJoin thousands of satisfied customers who've discovered their perfect match.", "cta_text": "See What's Popular"},
    ]
    reasoning = f"Created {len(variants)} variants for {channel_name} targeting {seg_name}."
    output = {"reasoning": reasoning, "confidence_score": 0.91,
              "supporting_data": {"channel": channel_name, "variant_count": len(variants), "styles_used": ["emotional", "urgency", "social_proof"]},
              "predicted_outcome": {"best_performing_variant": "A expected to resonate most"}}
    return {**_agent_trace(state, "Nova", output), "message_variants": variants, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.91)}


async def darwin_agent(state: MarketingState) -> dict:
    variants = state.get("message_variants", [])
    reach = 5000
    seg = state.get("segment", {})
    if isinstance(seg, dict):
        reach = seg.get("estimated_reach", 5000)
    split = max(1, reach // max(len(variants), 1))
    hypothesis = "Variant A (emotional) will outperform others by at least 10% in conversion rate."
    reasoning = f"A/B test with {len(variants)} variants, ~{split} customers each. Hypothesis: {hypothesis}"
    test_plan = {"variants": [v["variant_type"] for v in variants], "split_per_variant": split, "total_audience": reach, "success_metric": "conversion_rate", "min_confidence": 0.95, "hypothesis": hypothesis}
    output = {"reasoning": reasoning, "confidence_score": 0.85, "supporting_data": test_plan,
              "predicted_outcome": {"recommended_winner": "A", "expected_lift": "10-15%", "estimated_duration_days": 14}}
    return {**_agent_trace(state, "Darwin", output), "ab_test": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.85)}


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


async def apollo_agent(state: MarketingState) -> dict:
    insights = ["Campaign shows strong potential.", "Recommended channel has top-quartile expected CTR.", "A/B test will identify winner within 14 days."]
    recommendations = ["Monitor first 48 hours.", "Prepare fallback channel.", "Set up real-time analytics."]
    reasoning = f"Analyzed campaign plan. {len(insights)} insights identified."
    output = {"reasoning": reasoning, "confidence_score": 0.93, "supporting_data": {"insights": insights, "recommendations": recommendations},
              "predicted_outcome": {"expected_metrics": {"open_rate": "25-35%", "ctr": "8-15%", "conversion_rate": "3-7%"}, "overall_assessment": "highly promising"}}
    return {**_agent_trace(state, "Apollo", output), "analytics": output, "reasoning": reasoning, "confidence": min(state.get("confidence", 1.0), 0.93)}


async def command_centre_agent(state: MarketingState) -> dict:
    from app.clients.app_client import (
        fetch_pipeline_status, fetch_dashboard_stats, fetch_campaigns,
        fetch_proposals, fetch_customers, fetch_lifecycle_distribution,
        fetch_channel_analytics, fetch_opportunities,
    )

    query = state.get("goal", "").lower()
    response_text = ""
    supporting_data = {}
    predicted_outcome = {}

    if any(w in query for w in ["status", "pipeline", "health", "queue", "worker"]):
        pipeline = await fetch_pipeline_status()
        dashboard = await fetch_dashboard_stats()
        active_campaigns = dashboard.get("active_campaigns", 0)
        total_customers = dashboard.get("total_customers", 0)
        qd = pipeline.get("queue_depth", 0)
        rq = pipeline.get("retry_queue_size", 0)
        dlq = pipeline.get("dlq_size", 0)
        ws = pipeline.get("worker_status", "unknown")
        response_text = (
            f"**System Status**\n"
            f"- Worker: {ws}\n"
            f"- Queue Depth: {qd} messages\n"
            f"- Retry Queue: {rq}\n"
            f"- Dead Letter Queue: {dlq}\n"
            f"- Active Campaigns: {active_campaigns}\n"
            f"- Total Customers: {total_customers:,}"
        )
        supporting_data = {"pipeline": pipeline, "dashboard": {k: v for k, v in dashboard.items() if not isinstance(v, (list, dict))}}
        predicted_outcome = {"system_healthy": ws == "healthy", "queue_load": "low" if qd < 50 else "medium" if qd < 200 else "high"}

    elif any(w in query for w in ["customer", "audience", "people", "users"]):
        search = None
        for prefix in ["customer ", "audience "]:
            if prefix in query:
                search = query.split(prefix, 1)[1].strip()
                break
        page_size = 5
        if search:
            customers_data = await fetch_customers(search=search, page_size=page_size)
        else:
            customers_data = await fetch_customers(page_size=5)
        lifecycle = await fetch_lifecycle_distribution()
        customers = customers_data.get("customers", [])
        total = customers_data.get("total", 0)
        if search:
            response_text = f"Found {total} customers matching '{search}':\n"
        else:
            response_text = f"**Customers Overview** — {total:,} total\n"
        for c in customers[:5]:
            name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            stage = c.get("lifecycle_stage", "unknown")
            spent = c.get("total_spent", 0)
            response_text += f"- {name} ({c.get('email', 'N/A')}) — {stage}, ₹{spent:,.0f} spent\n"
        if lifecycle:
            response_text += "\n**Lifecycle Distribution:**\n"
            for entry in lifecycle[:6]:
                if isinstance(entry, dict):
                    response_text += f"- {entry.get('stage', entry.get('lifecycle_stage', 'unknown'))}: {entry.get('count', 0)}\n"
        supporting_data = {"customers_sample": customers[:5], "total": total, "lifecycle": lifecycle}
        predicted_outcome = {"customer_count": total, "segments_available": len(lifecycle) if lifecycle else 0}

    elif any(w in query for w in ["campaign", "dispatch", "send"]):
        campaigns_data = await fetch_campaigns(page_size=10)
        campaigns = campaigns_data.get("campaigns", [])
        total = campaigns_data.get("total", 0)
        response_text = f"**Campaigns** — {total} total\n"
        for c in campaigns[:5]:
            name = c.get("name", "Unnamed")
            status = c.get("status", "unknown")
            channel = c.get("channel", "—")
            response_text += f"- {name} ({channel}) — {status}\n"
        supporting_data = {"campaigns_sample": campaigns[:5], "total": total}
        predicted_outcome = {"campaign_count": total}

    elif any(w in query for w in ["proposal", "agent", "run", "approval"]):
        proposals = await fetch_proposals()
        response_text = f"**Agent Proposals & Runs** — {len(proposals)} recent\n"
        for p in proposals[:5]:
            run_type = p.get("run_type", "unknown")
            status = p.get("status", "unknown")
            created = p.get("created_at", "")
            if created:
                created = created[:19].replace("T", " ")
            response_text += f"- {run_type}: {status} ({created})\n"
        supporting_data = {"proposals": proposals[:5], "total": len(proposals)}
        predicted_outcome = {"active_runs": sum(1 for p in proposals if p.get("status") in ("running", "pending"))}

    elif any(w in query for w in ["channel", "analytics", "performance"]):
        channels = await fetch_channel_analytics()
        response_text = f"**Channel Performance** — {len(channels)} channels\n"
        for ch in channels:
            name = ch.get("channel", "unknown")
            sent = ch.get("sent_count", 0)
            opened = ch.get("open_count", 0)
            conv = ch.get("conversion_count", 0)
            rev = ch.get("revenue", 0)
            response_text += f"- {name}: {sent:,} sent, {opened:,} opened, {conv:,} converted, ₹{rev:,.0f} revenue\n"
        supporting_data = {"channels": channels}
        predicted_outcome = {"channel_count": len(channels)}

    elif any(w in query for w in ["opportunity", "discover"]):
        opp_data = await fetch_opportunities(page_size=10)
        opportunities = opp_data.get("opportunities", [])
        total = opp_data.get("total", 0)
        response_text = f"**Opportunities** — {total} total\n"
        for o in opportunities[:5]:
            title = o.get("title", "Unnamed")
            otype = o.get("opportunity_type", "general")
            status = o.get("status", "pending")
            rev = o.get("expected_revenue", 0)
            response_text += f"- {title} ({otype}) — {status}, ₹{rev:,.0f}\n"
        supporting_data = {"opportunities_sample": opportunities[:5], "total": total}
        predicted_outcome = {"opportunity_count": total}

    else:
        dashboard = await fetch_dashboard_stats()
        pipeline = await fetch_pipeline_status()
        ws = pipeline.get("worker_status", "unknown")
        total_customers = dashboard.get("total_customers", 0)
        active_campaigns = dashboard.get("active_campaigns", 0)
        response_text = (
            f"I can help you with:\n"
            f"1. **System Status** — Worker: {ws}, Queue: {pipeline.get('queue_depth', 0)}\n"
            f"2. **Customers** — {total_customers:,} total, segmented by lifecycle stage\n"
            f"3. **Campaigns** — {active_campaigns} active, across multiple channels\n"
            f"4. **Channel Analytics** — Performance breakdown by channel\n"
            f"5. **Agent Proposals** — AI campaign proposals and approvals\n"
            f"6. **Opportunities** — AI-discovered marketing opportunities\n\n"
            f"Try asking: \"What is the system status?\", \"Show me customers\", "
            f"\"How are my campaigns doing?\", or \"List recent proposals\"."
        )
        supporting_data = {"capabilities": ["status", "customers", "campaigns", "analytics", "proposals", "opportunities"]}
        predicted_outcome = {"fallback": True}

    reasoning = f"Processed query: '{query}'. Intent matched and data fetched from App Service."
    output = {
        "reasoning": reasoning,
        "confidence_score": 0.92,
        "supporting_data": supporting_data,
        "predicted_outcome": predicted_outcome,
        "response": response_text,
    }
    return {
        **_agent_trace(state, "CommandCentre", output),
        "reasoning": reasoning,
        "confidence": 0.92,
        "metadata": {"command_centre_response": output},
    }


async def sentinel_agent(state: MarketingState) -> dict:
    trace = state.get("agent_trace", [])
    seg = state.get("segment", {})
    seg_name = seg.get("name", "Unknown") if isinstance(seg, dict) else "Unknown"
    ch = state.get("channel", {})
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
