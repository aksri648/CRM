"""Pydantic schemas enforced via Groq function calling.

Each LLM-driven agent uses .with_structured_output(SchemaCls) so the model is
forced to return a valid object — no JSON-parsing flakiness.
"""
from typing import Literal

from pydantic import BaseModel, Field


SEGMENT_KEYS = Literal["inactive", "repeat", "reactivation", "loyalty", "cross_sell", "welcome"]
STRATEGY_KEYS = Literal["retention", "reactivation", "cross_sell", "upsell", "loyalty"]
CHANNEL_KEYS = Literal["email", "sms", "whatsapp", "rcs"]
VARIANT_STYLES = Literal["emotional", "urgency", "social_proof"]


class AthenaOutput(BaseModel):
    """Marketing director — interprets the user's goal."""
    intent: str = Field(description="The user's core marketing intent in 5-15 words")
    target_outcome: str = Field(description="What success looks like for this campaign in one sentence")
    required_specialists: list[str] = Field(
        description="Which specialists to delegate to, subset of: atlas, sophia, mercury, nova, darwin, apollo"
    )
    reasoning: str = Field(description="Why these specialists, in 2-3 sentences")
    confidence_score: float = Field(ge=0.0, le=1.0)


class AtlasOutput(BaseModel):
    """Segment analyst — picks the audience."""
    segment_key: SEGMENT_KEYS = Field(description="Which predefined segment best matches the goal")
    rationale: str = Field(description="Why this segment fits, referencing specific phrases from the goal")
    confidence_score: float = Field(ge=0.0, le=1.0)


class SophiaOutput(BaseModel):
    """Strategy designer — chooses the campaign approach."""
    strategy_type: STRATEGY_KEYS = Field(description="The strategic approach to take")
    custom_offer: str = Field(description="A specific, compelling incentive tailored to the segment + goal")
    approach: str = Field(description="How the messaging should be framed in one sentence")
    reasoning: str = Field(description="Why this strategy fits the segment")
    confidence_score: float = Field(ge=0.0, le=1.0)


class MercuryOutput(BaseModel):
    """Channel selector — picks where to reach the audience."""
    channel: CHANNEL_KEYS = Field(description="Best channel for this segment and strategy")
    rationale: str = Field(description="Why this channel beats the alternatives for this audience")
    expected_open_rate_pct: int = Field(ge=0, le=100, description="Realistic expected open rate, 0-100")
    confidence_score: float = Field(ge=0.0, le=1.0)


class NovaVariant(BaseModel):
    variant_type: Literal["A", "B", "C"]
    style: VARIANT_STYLES
    subject_line: str = Field(
        max_length=80,
        description="Subject line under 80 chars. Use the {first_name} placeholder for personalization where natural.",
    )
    message_body: str = Field(
        description=(
            "2-4 short paragraphs. Use {first_name} placeholder for the recipient's name. "
            "Match the variant style (emotional / urgency / social_proof). "
            "Do not include subject line or signature."
        )
    )
    cta_text: str = Field(max_length=30, description="2-4 word call-to-action button text")


class NovaOutput(BaseModel):
    """Copywriter — produces three variants for A/B testing."""
    variants: list[NovaVariant] = Field(
        min_length=3,
        max_length=3,
        description="Exactly three variants: one emotional, one urgency, one social_proof",
    )
    reasoning: str = Field(description="How the variants differ in approach")
    confidence_score: float = Field(ge=0.0, le=1.0)


class CommandCentreOutput(BaseModel):
    """Free-form natural-language response built from pre-fetched system data."""
    response: str = Field(
        description=(
            "A concise, natural-language answer to the user's question. "
            "Use the provided context data. Prefer short paragraphs over long ones. "
            "Use bullet points with `-` if listing multiple items. "
            "Round large numbers (e.g. 12,345). Be specific — cite numbers from the context."
        )
    )
    confidence_score: float = Field(ge=0.0, le=1.0)
