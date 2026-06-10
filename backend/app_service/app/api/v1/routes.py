import uuid
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.security import get_current_user, create_access_token
from app.schemas import (
    AuthRequest, AuthResponse, CustomerResponse, CustomerListResponse,
    ProductResponse, OrderResponse, SegmentCreate, SegmentResponse,
    CampaignCreate, CampaignResponse, CampaignListResponse,
    MarketingGoalCreate, MarketingGoalResponse,
    CampaignPerformanceResponse, DashboardStatsResponse,
    ApprovalResponse, ApprovalAction, CallbackEvent, PipelineStatusResponse,
    ABTestCreate, ABTestResponse,
)
from app.services.customer_service import list_customers, get_customer, get_customer_orders, get_lifecycle_distribution
from app.services.campaign_service import create_campaign, get_campaign, list_campaigns, launch_campaign, create_marketing_goal, list_marketing_goals, list_opportunities
from app.services.segment_service import create_segment, get_segment, list_segments, snapshot_segment
from app.services.analytics_service import compute_campaign_performance, get_channel_performance, get_dashboard_stats, update_campaign_performance_from_callback
from app.services.approval_service import create_approval, list_approvals, respond_to_approval, get_approval
from app.services.telegram_service import process_telegram_callback
from app.clients.agent_client import call_agent_generate_campaign, call_agent_discover_opportunities, call_agent_command_centre
from app.clients.communication_client import dispatch_campaign_to_communication_service, simulate_campaign_lifecycle
from app.models.crm import Product, Segment, Customer
from app.models.campaign import Campaign, CampaignVariant, ApprovalRequest, CampaignOpportunity
from app.models.system import AgentRun, AgentDecision, TelegramEvent
from app.utils.logging import logger

router = APIRouter()


@router.post("/seed")
async def seed_database():
    from app.seed.seed import seed
    from app.database import create_tables
    await create_tables()
    await seed()
    return {"status": "seeded"}


@router.post("/auth/login")
async def login(data: AuthRequest):
    token = create_access_token({"sub": data.username, "role": "admin"})
    return AuthResponse(access_token=token, role="admin")


@router.get("/health")
async def health():
    from app.clients.agent_client import get_agent_health
    from app.clients.communication_client import get_communication_health
    agent_ok = await get_agent_health()
    comm_ok = await get_communication_health()
    return {
        "status": "healthy",
        "service": "app-service",
        "dependencies": {"agent_service": "up" if agent_ok else "down", "communication_service": "up" if comm_ok else "down"},
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    stats = await get_dashboard_stats(db)
    return DashboardStatsResponse(**stats)


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers_endpoint(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = None, lifecycle_stage: str | None = None,
    sort_by: str = "created_at", sort_desc: bool = True,
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    return await list_customers(db, page, page_size, search, lifecycle_stage, sort_by, sort_desc)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer_endpoint(customer_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    customer = await get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


@router.get("/customers/{customer_id}/orders")
async def get_customer_orders_endpoint(customer_id: uuid.UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await get_customer_orders(db, customer_id, page, page_size)


@router.get("/customers/lifecycle/distribution")
async def lifecycle_distribution(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await get_lifecycle_distribution(db)


@router.post("/segments", response_model=SegmentResponse)
async def create_segment_endpoint(data: SegmentCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    segment = await create_segment(db, data)
    return SegmentResponse.model_validate(segment)


@router.get("/segments")
async def list_segments_endpoint(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await list_segments(db, page, page_size)


@router.get("/segments/{segment_id}", response_model=SegmentResponse)
async def get_segment_endpoint(segment_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    segment = await get_segment(db, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return SegmentResponse.model_validate(segment)


@router.post("/segments/{segment_id}/snapshot")
async def snapshot_segment_endpoint(segment_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    snapshot = await snapshot_segment(db, segment_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Segment not found")
    return {"snapshot_id": str(snapshot.id), "customer_count": snapshot.customer_count}


@router.get("/products")
async def list_products(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), category: str | None = None, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = select(Product).where(Product.is_active == True)
    if category:
        query = query.where(Product.category == category)
    query = query.order_by(Product.name)
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()
    return {"products": [ProductResponse.model_validate(p) for p in products], "total": total, "page": page, "page_size": page_size}


@router.post("/marketing-goals", response_model=MarketingGoalResponse)
async def create_goal(data: MarketingGoalCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    goal = await create_marketing_goal(db, data)
    return MarketingGoalResponse.model_validate(goal)


@router.get("/marketing-goals")
async def list_goals(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    goals = await list_marketing_goals(db)
    return [MarketingGoalResponse.model_validate(g) for g in goals]


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign_endpoint(data: CampaignCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    campaign = await create_campaign(db, data, user=current_user.get("sub"))
    return CampaignResponse.model_validate(campaign)


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns_endpoint(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: str | None = None, channel: str | None = None, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await list_campaigns(db, page, page_size, status, channel)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign_endpoint(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return CampaignResponse.model_validate(campaign)


@router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign_endpoint(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    campaign = await get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.approval_status != "approved":
        raise HTTPException(status_code=400, detail="Campaign must be approved before launch")

    segment = await db.execute(select(Segment).where(Segment.id == campaign.segment_id))
    segment = segment.scalar_one_or_none()
    customer_ids = []
    if segment:
        from app.services.segment_service import evaluate_segment_criteria
        customers = await evaluate_segment_criteria(db, segment.criteria)
        customer_ids = [c.id for c in customers[:100]]

    variant = campaign.variants[0] if campaign.variants else None

    try:
        dispatch_result = await dispatch_campaign_to_communication_service(
            campaign_id=campaign.id,
            customer_ids=customer_ids,
            channel=campaign.channel,
            variant_id=variant.id if variant else None,
            subject_line=variant.subject_line if variant else None,
            message_body=variant.message_body if variant else None,
        )
        campaign.status = "launched"
        campaign.launched_at = datetime.utcnow()
        await db.commit()

        import asyncio
        asyncio.create_task(simulate_campaign_lifecycle(campaign.id))

        return {
            "campaign": CampaignResponse.model_validate(campaign),
            "dispatch": dispatch_result,
            "customers_targeted": len(customer_ids),
        }
    except Exception as e:
        logger.error("campaign_launch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Campaign launch failed: {str(e)}")


@router.get("/campaigns/{campaign_id}/performance", response_model=CampaignPerformanceResponse)
async def campaign_performance(campaign_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    perf = await compute_campaign_performance(db, campaign_id)
    if not perf:
        return CampaignPerformanceResponse()
    return CampaignPerformanceResponse.model_validate(perf)


@router.get("/analytics/channels")
async def channel_performance(channel: str | None = None, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    perf = await get_channel_performance(db, channel)
    return [
        {"channel": p.channel, "sent_count": p.sent_count, "delivered_count": p.delivered_count,
         "open_count": p.open_count, "click_count": p.click_count, "conversion_count": p.conversion_count,
         "revenue": float(p.revenue), "delivery_rate": p.delivery_rate, "open_rate": p.open_rate,
         "click_through_rate": p.click_through_rate, "conversion_rate": p.conversion_rate}
        for p in perf
    ]


@router.post("/agents/generate-campaign")
async def generate_campaign(data: dict, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    goal = data.get("goal", "")
    if not goal:
        raise HTTPException(status_code=400, detail="Goal is required")

    agent_run = AgentRun(run_type="campaign_generation", input_data={"goal": goal}, status="running")
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)

    try:
        agent_result = await call_agent_generate_campaign(goal, str(agent_run.id))
        proposal = agent_result.get("proposal", {})
        agent_trace = agent_result.get("agent_trace", [])
        segment_info = agent_result.get("segment", {})
        channel_info = agent_result.get("channel_info", {})

        for entry in agent_trace:
            decision = AgentDecision(
                agent_run_id=agent_run.id,
                agent_name=entry.get("agent", "unknown"),
                output_data=entry.get("output"),
                reasoning=entry.get("output", {}).get("reasoning", ""),
                confidence_score=entry.get("output", {}).get("confidence_score"),
                supporting_data=entry.get("output", {}).get("supporting_data"),
                predicted_outcome=entry.get("output", {}).get("predicted_outcome"),
            )
            db.add(decision)

        segment = Segment(
            name=proposal.get("segment", "AI Generated Segment"),
            criteria=segment_info.get("criteria", {}),
            customer_count=segment_info.get("estimated_reach", 0),
        )
        db.add(segment)
        await db.flush()

        campaign = Campaign(
            name=f"AI: {goal[:50]}",
            description=goal,
            segment_id=segment.id,
            channel=channel_info.get("channel", "email"),
            status="draft", ai_generated=True,
            reasoning=agent_result.get("reasoning"),
            expected_reach=segment_info.get("estimated_reach"),
            expected_ctr=channel_info.get("expected_ctr"),
            expected_revenue=channel_info.get("expected_revenue"),
            approval_status="pending", created_by=current_user.get("sub"),
        )
        db.add(campaign)
        await db.flush()

        variants = agent_result.get("message_variants", [])
        for i, v in enumerate(variants):
            db.add(CampaignVariant(
                campaign_id=campaign.id, name=v.get("variant_type", f"Variant {i}"),
                variant_type=v.get("variant_type", chr(65 + i)),
                subject_line=v.get("subject_line", ""), message_body=v.get("message_body", ""),
                cta_text=v.get("cta_text", ""), style=v.get("style", "standard"),
            ))

        agent_run.status = "completed"
        agent_run.output_data = {"campaign_id": str(campaign.id)}
        agent_run.completed_at = datetime.utcnow()
        await db.commit()

        approval = await create_approval(db, campaign.id, requested_by=current_user.get("sub"), reasoning=proposal)

        return {
            "run_id": str(agent_run.id), "campaign_id": str(campaign.id),
            "approval_id": str(approval.id), "proposal": proposal,
            "agent_trace": agent_trace,
        }

    except Exception as e:
        agent_run.status = "failed"
        agent_run.error = str(e)
        agent_run.completed_at = datetime.utcnow()
        await db.commit()
        logger.error("campaign_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")


@router.post("/agents/discover-opportunities")
async def discover_opportunities(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    agent_run = AgentRun(run_type="opportunity_discovery", status="running")
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)

    try:
        agent_result = await call_agent_discover_opportunities(str(agent_run.id))
        all_opportunities = agent_result.get("opportunities", [])
        agent_trace = agent_result.get("agent_trace", [])

        for entry in agent_trace:
            db.add(AgentDecision(
                agent_run_id=agent_run.id,
                agent_name=entry.get("agent", "unknown"),
                output_data=entry.get("output"),
                reasoning=entry.get("output", {}).get("reasoning", ""),
                confidence_score=entry.get("output", {}).get("confidence_score"),
            ))

        created = []
        for opp_data in all_opportunities:
            from app.models.campaign import CampaignOpportunity
            opp = CampaignOpportunity(
                title=opp_data.get("title", "AI Discovered Opportunity"),
                description=opp_data.get("description", ""),
                opportunity_type=opp_data.get("opportunity_type", "general"),
                expected_revenue=opp_data.get("expected_revenue"),
                expected_reach=opp_data.get("expected_reach"),
                recommended_channel=opp_data.get("recommended_channel"),
                rationale=opp_data, status="pending",
            )
            db.add(opp)
            created.append(opp)

        agent_run.status = "completed"
        agent_run.output_data = {"opportunities_created": len(created)}
        agent_run.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "run_id": str(agent_run.id), "opportunities_created": len(created),
            "opportunities": [{"id": str(o.id), "title": o.title, "type": o.opportunity_type,
                               "expected_revenue": float(o.expected_revenue) if o.expected_revenue else None, "status": o.status}
                              for o in created],
            "agent_trace": agent_trace,
        }

    except Exception as e:
        agent_run.status = "failed"
        agent_run.error = str(e)
        agent_run.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Opportunity discovery failed: {str(e)}")


@router.post("/agents/command-centre")
async def command_centre(data: dict, current_user: dict = Depends(get_current_user)):
    try:
        result = await call_agent_command_centre(data.get("query", ""))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command centre query failed: {str(e)}")


@router.get("/approvals")
async def list_approvals_endpoint(status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await list_approvals(db, status, page, page_size)


@router.post("/approvals/{approval_id}/respond")
async def respond_to_approval_endpoint(approval_id: uuid.UUID, data: ApprovalAction, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    approval = await respond_to_approval(db, approval_id, data.action, approved_by=current_user.get("sub"))
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found or already processed")
    return {"status": approval.status, "campaign_id": str(approval.campaign_id)}


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    event = TelegramEvent(event_type="telegram_callback", payload=body)
    db.add(event)
    if "callback_query" in body:
        cb = body["callback_query"]
        callback_data = cb.get("data", "")
        if callback_data:
            parsed = await process_telegram_callback(callback_data)
            action, approval_id = parsed.get("action"), parsed.get("approval_id")
            if action in ("approve", "reject") and approval_id:
                try:
                    await respond_to_approval(db, uuid.UUID(approval_id), action, approved_by="telegram")
                except Exception as e:
                    logger.error("telegram_approval_error", error=str(e))
    await db.commit()
    return {"ok": True}


@router.get("/opportunities")
async def list_opportunities_endpoint(status: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await list_opportunities(db, status, page, page_size)
    return {
        "opportunities": [{"id": str(o.id), "title": o.title, "description": o.description,
                           "opportunity_type": o.opportunity_type,
                           "expected_revenue": float(o.expected_revenue) if o.expected_revenue else None,
                           "expected_reach": o.expected_reach, "recommended_channel": o.recommended_channel,
                           "rationale": o.rationale, "status": o.status,
                           "created_at": o.created_at.isoformat() if o.created_at else None}
                          for o in result["opportunities"]],
        "total": result["total"], "page": result["page"], "page_size": result["page_size"],
    }


@router.post("/callbacks/events")
async def receive_callback(data: CallbackEvent, db: AsyncSession = Depends(get_db)):
    await update_campaign_performance_from_callback(db, data.campaign_id, data.event_type, data.metadata)
    return {"status": "processed", "event_type": data.event_type}


@router.get("/pipeline/status", response_model=PipelineStatusResponse)
async def pipeline_status(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return PipelineStatusResponse(worker_status="healthy")


@router.post("/scheduler/trigger/{job_type}")
async def trigger_scheduler(job_type: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if job_type == "analytics-refresh":
        from app.services.scheduler_service import run_analytics_refresh
        await run_analytics_refresh()
        return {"job_type": job_type, "status": "triggered"}
    raise HTTPException(status_code=400, detail=f"Unknown job type: {job_type}")


@router.get("/proposals")
async def list_proposals(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(
        select(AgentRun).where(AgentRun.run_type.in_(["campaign_generation", "opportunity_discovery"]))
        .order_by(AgentRun.created_at.desc()).limit(20)
    )
    runs = result.scalars().all()
    return [{"run_id": str(r.id), "run_type": r.run_type, "status": r.status,
             "created_at": r.created_at.isoformat() if r.created_at else None,
             "input": r.input_data, "output": r.output_data, "error": r.error} for r in runs]


@router.get("/ab-tests")
async def list_ab_tests(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: str | None = None, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    from app.models.campaign import ABTest
    query = select(ABTest)
    if status:
        query = query.where(ABTest.status == status)
    query = query.order_by(ABTest.created_at.desc())
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tests = result.scalars().all()
    return {
        "ab_tests": [ABTestResponse.model_validate(t).model_dump() for t in tests],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/ab-tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(test_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    from app.models.campaign import ABTest
    result = await db.execute(select(ABTest).where(ABTest.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return test


@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(data: ABTestCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    from app.models.campaign import ABTest
    test = ABTest(
        campaign_id=data.campaign_id, name=data.name, hypothesis=data.hypothesis,
        audience_split=data.audience_split, success_metric=data.success_metric,
        min_confidence=data.min_confidence, status="running",
        started_at=datetime.utcnow(),
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return test


@router.get("/")
async def root():
    return {
        "service": "Xeno App Service",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth/login", "health": "/api/v1/health",
            "dashboard": "/api/v1/dashboard/stats", "customers": "/api/v1/customers",
            "segments": "/api/v1/segments", "campaigns": "/api/v1/campaigns",
            "analytics": "/api/v1/analytics/channels",
            "agents": "/api/v1/agents/generate-campaign",
            "approvals": "/api/v1/approvals", "opportunities": "/api/v1/opportunities",
        },
    }
