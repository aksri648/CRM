import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CommunicationCreate(BaseModel):
    campaign_id: uuid.UUID
    customer_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    channel: str
    subject_line: str | None = None
    message_body: str | None = None


class CommunicationResponse(BaseModel):
    id: uuid.UUID; campaign_id: uuid.UUID; customer_id: uuid.UUID
    variant_id: uuid.UUID | None = None; channel: str; status: str
    subject_line: str | None = None; message_body: str | None = None
    sent_at: datetime | None = None; delivered_at: datetime | None = None
    opened_at: datetime | None = None; clicked_at: datetime | None = None
    converted_at: datetime | None = None; failed_at: datetime | None = None
    failure_reason: str | None = None; retry_count: int = 0
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class CampaignDispatchRequest(BaseModel):
    campaign_id: uuid.UUID; customer_ids: list[uuid.UUID]
    variant_id: uuid.UUID | None = None; channel: str
    subject_line: str | None = None; message_body: str | None = None


class CampaignDispatchResponse(BaseModel):
    campaign_id: uuid.UUID; total_communications: int; queued_count: int; status: str


class EventCreate(BaseModel):
    communication_id: uuid.UUID
    event_type: str
    timestamp: datetime | None = None
    metadata: dict | None = Field(default=None, alias="metadata")
    model_config = ConfigDict(populate_by_name=True)


class EventResponse(BaseModel):
    id: uuid.UUID
    communication_id: uuid.UUID
    event_type: str
    timestamp: datetime | None = None
    metadata: dict | None = Field(
        default=None,
        validation_alias="event_metadata",
        serialization_alias="metadata",
    )
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CallbackRequest(BaseModel):
    communication_id: uuid.UUID; campaign_id: uuid.UUID
    customer_id: uuid.UUID; event_type: str
    timestamp: datetime | None = None; metadata: dict | None = None
