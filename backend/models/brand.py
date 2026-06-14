"""Pydantic models for Brand Profiles."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from typing import Any
from pydantic import BaseModel, Field, HttpUrl, field_validator


class WritingPerspective(str, Enum):
    FIRST_PERSON_SINGULAR = "first_person_singular"
    FIRST_PERSON_PLURAL = "first_person_plural"
    SECOND_PERSON = "second_person"
    THIRD_PERSON = "third_person"


class BrandVoice(str, Enum):
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    WITTY = "witty"
    EMPATHETIC = "empathetic"
    BOLD = "bold"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"


class Industry(str, Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    SAAS = "saas"
    MEDIA = "media"
    CONSULTING = "consulting"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    NONPROFIT = "nonprofit"
    LEGAL = "legal"
    OTHER = "other"


class BrandProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Brand or company name")
    tagline: str = Field(default="", max_length=200, description="One-liner describing what you do")
    industry: Industry | None = Field(default=Industry.OTHER)
    target_audience: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="e.g. ['CTOs', 'indie hackers', 'enterprise PMs']",
    )
    brand_voice: list[BrandVoice] = Field(
        default_factory=lambda: [BrandVoice.CONVERSATIONAL],
        description="Select up to 3 voice attributes",
    )
    writing_perspective: WritingPerspective | None = Field(default=WritingPerspective.FIRST_PERSON_SINGULAR)
    competitor_brands: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Used to differentiate positioning and tone",
    )
    avoid_topics: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Topics/words to never include in generated content",
    )
    sample_content: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Paste 1–3 example posts/blogs for voice matching",
    )
    website_url: str | None = Field(
        default=None,
        description="Auto-scraped for additional brand context",
    )
    custom_instructions: str = Field(
        default="",
        max_length=1000,
        description="Free-form extra instructions always injected into prompts",
    )

    @field_validator("sample_content", mode="before")
    @classmethod
    def validate_sample_content(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class BrandProfileCreate(BrandProfileBase):
    pass


class BrandProfileUpdate(BaseModel):
    name: str | None = None
    tagline: str | None = None
    industry: Industry | None = None
    target_audience: list[str] | None = None
    brand_voice: list[BrandVoice] | None = None
    writing_perspective: WritingPerspective | None = None
    competitor_brands: list[str] | None = None
    avoid_topics: list[str] | None = None
    sample_content: list[str] | None = None
    website_url: str | None = None
    custom_instructions: str | None = None


class BrandProfile(BrandProfileBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True

    def to_prompt_context(self) -> str:
        """Render brand profile as a formatted string for injection into prompts."""
        lines = [
            f"Brand: {self.name}",
        ]
        if self.tagline:
            lines.append(f"Tagline: {self.tagline}")
        lines.append(f"Industry: {self.industry.value.replace('_', ' ').title()}")
        if self.target_audience:
            lines.append(f"Target audience: {', '.join(self.target_audience)}")
        if self.brand_voice:
            voices = ", ".join(v.value for v in self.brand_voice)
            lines.append(f"Brand voice: {voices}")
        lines.append(
            f"Writing perspective: {self.writing_perspective.value.replace('_', ' ')}"
        )
        if self.competitor_brands:
            lines.append(
                f"Differentiate from: {', '.join(self.competitor_brands)}"
            )
        if self.avoid_topics:
            lines.append(f"NEVER mention or include: {', '.join(self.avoid_topics)}")
        if self.sample_content:
            lines.append("\nSample content for voice reference:")
            for i, sample in enumerate(self.sample_content, 1):
                lines.append(f"--- Example {i} ---\n{sample[:500]}...")
        if self.custom_instructions:
            lines.append(f"\nAdditional instructions: {self.custom_instructions}")
        return "\n".join(lines)
