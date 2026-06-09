import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import ApprovalRequest, Campaign
from app.services.telegram_service import send_approval_notification


async def create_approval(db: AsyncSession, campaign_id: uuid.UUID,
                          request_type: str = "campaign_launch",
                          requested_by: str | None = None,
                          reasoning: dict | None = None) -> ApprovalRequest:
    approval = ApprovalRequest(campaign_id=campaign_id, request_type=request_type, requested_by=requested_by, reasoning=reasoning)
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    campaign = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = campaign.scalar_one_or_none()
    await send_approval_notification(campaign, approval)
    return approval


async def list_approvals(db: AsyncSession, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    query = select(ApprovalRequest).options(selectinload(ApprovalRequest.campaign)).order_by(ApprovalRequest.created_at.desc())
    if status:
        query = query.where(ApprovalRequest.status == status)
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    approvals = result.scalars().all()
    return {
        "approvals": [
            {"id": a.id, "campaign_id": a.campaign_id, "campaign_name": a.campaign.name if a.campaign else None,
             "request_type": a.request_type, "status": a.status, "requested_by": a.requested_by,
             "reasoning": a.reasoning, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in approvals
        ],
        "total": total, "page": page, "page_size": page_size,
    }


async def respond_to_approval(db: AsyncSession, approval_id: uuid.UUID, action: str, approved_by: str | None = None) -> ApprovalRequest | None:
    result = await db.execute(
        select(ApprovalRequest).options(selectinload(ApprovalRequest.campaign)).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval or approval.status != "pending":
        return None
    if action == "approve":
        approval.status = "approved"
        approval.approved_by = approved_by
        approval.approved_at = datetime.utcnow()
        if approval.campaign:
            approval.campaign.approval_status = "approved"
            approval.campaign.status = "approved"
    else:
        approval.status = "rejected"
        approval.approved_by = approved_by
        approval.approved_at = datetime.utcnow()
        if approval.campaign:
            approval.campaign.approval_status = "rejected"
    await db.commit()
    await db.refresh(approval)
    return approval


async def get_approval(db: AsyncSession, approval_id: uuid.UUID) -> ApprovalRequest | None:
    result = await db.execute(select(ApprovalRequest).options(selectinload(ApprovalRequest.campaign)).where(ApprovalRequest.id == approval_id))
    return result.scalar_one_or_none()
