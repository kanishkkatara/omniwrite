"""Request/response models for the generation API."""
from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Platform(str, Enum):
    BLOG = "blog"
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    LINKEDIN_COMMENT = "linkedin_comment"


class ContentLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ModelMode(str, Enum):
    TEST = "test"
    PRODUCTION = "production"
    LOCAL = "local"
    GROQ = "groq"


class ReadingLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class CTAType(str, Enum):
    SUBSCRIBE = "subscribe"
    CONTACT = "contact"
    DOWNLOAD = "download"
    LEARN_MORE = "learn_more"
    FOLLOW = "follow"
    NONE = "none"


class GenerateRequest(BaseModel):
    """Request body for POST /api/v1/generate"""

    # Content brief
    topic: str = Field(..., min_length=3, max_length=500, description="The main topic or story")
    additional_context: str = Field(default="", max_length=2000)
    source_urls: list[str] = Field(default_factory=list, max_length=5)
    sample_draft: str | None = Field(
        default=None,
        max_length=10000,
        description="Paste an existing draft to transform/adapt",
    )
    key_points: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Specific points you want covered",
    )

    # Content settings
    platforms: list[Platform] = Field(
        default_factory=lambda: [Platform.BLOG, Platform.LINKEDIN, Platform.REDDIT],
    )
    length: ContentLength = ContentLength.MEDIUM
    seo_keywords: list[str] = Field(default_factory=list, max_length=10)
    reading_level: ReadingLevel = ReadingLevel.INTERMEDIATE
    cta_type: CTAType = CTAType.NONE
    language: str = Field(default="en", max_length=10)

    # Platform-specific
    reddit_subreddit: str | None = Field(
        default=None,
        description="Target subreddit for tone calibration (without r/)",
    )
    linkedin_audience: str | None = None

    # Advanced
    model_mode: ModelMode = ModelMode.TEST
    test_model: str | None = Field(default=None, description="Custom model name override for TEST mode")
    production_model: str | None = Field(default=None, description="Custom model name override for PRODUCTION mode")
    creativity: float = Field(default=0.7, ge=0.0, le=1.0, description="Maps to temperature")
    skip_research: bool = Field(default=False, description="Skip web research, use brief only")
    skip_outline_approval: bool = Field(
        default=False,
        description="Skip outline review step (async/batch mode)",
    )
    variants: int = Field(default=1, ge=1, le=5, description="Number of hook variants to generate")

    # Brand reference
    brand_id: UUID | None = None


class ContentOutput(BaseModel):
    platform: Platform
    content: str
    word_count: int
    metadata: dict = Field(default_factory=dict)


class GenerationCost(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_seconds: float


class GenerateResponse(BaseModel):
    job_id: UUID
    status: str  # pending | researching | strategizing | outlining | writing | editing | done | error
    outputs: dict[str, ContentOutput] = Field(default_factory=dict)
    outline: str | None = None
    cost_summary: GenerationCost | None = None
    error: str | None = None


class ApproveOutlineRequest(BaseModel):
    approved: bool = True
    edited_outline: str | None = Field(
        default=None,
        description="User-edited version of the outline to use instead",
    )


class RegenerateRequest(BaseModel):
    platform: Platform
    feedback: str | None = Field(
        default=None,
        description="Optional instruction for what to change",
    )
    model_mode: ModelMode = ModelMode.TEST
