"""
SQLModel-based async storage layer for omniwrite.

Provides:
- BrandProfileTable: persisted brand profiles
- JobTable: generation job records with status and outputs
- BrandStore: CRUD for brand profiles
- JobStore: job lifecycle management
- get_engine(), create_tables()
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None


# ── SQLModel table definitions ────────────────────────────────────────────────


class BrandProfileTable(SQLModel, table=True):
    """Persisted brand profile record."""

    __tablename__ = "brand_profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    data_json: str = Field(default="{}")  # Serialised BrandProfile JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class JobTable(SQLModel, table=True):
    """Generation job record."""

    __tablename__ = "jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    status: str = Field(default="pending", index=True)
    brand_id: UUID | None = Field(default=None, index=True)
    request_json: str = Field(default="{}")
    outputs_json: str = Field(default="{}")
    state_json: str = Field(default="{}")  # Full AgentState snapshot
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Engine setup ──────────────────────────────────────────────────────────────


def get_engine() -> AsyncEngine:
    """Return the singleton async engine, creating it if needed."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        from backend.core.config import get_settings

        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
    return _engine


async def create_tables() -> None:
    """Create all SQLModel tables if they don't exist."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables created/verified")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions."""
    engine = get_engine()
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:  # type: ignore[attr-defined]
        yield session


# ── BrandStore ────────────────────────────────────────────────────────────────


class BrandStore:
    """CRUD operations for brand profiles."""

    async def create(self, brand_data: dict[str, Any]) -> BrandProfileTable:
        """Persist a new brand profile."""
        async for session in get_session():
            record = BrandProfileTable(
                name=brand_data.get("name", ""),
                data_json=json.dumps(brand_data),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.debug("Created brand: %s", record.id)
            return record

    async def get(self, brand_id: UUID) -> BrandProfileTable | None:
        """Fetch a brand profile by ID."""
        async for session in get_session():
            result = await session.get(BrandProfileTable, brand_id)
            return result

    async def list_all(self) -> list[BrandProfileTable]:
        """Return all brand profiles."""
        async for session in get_session():
            results = await session.exec(select(BrandProfileTable))
            return list(results.all())

    async def update(self, brand_id: UUID, updates: dict[str, Any]) -> BrandProfileTable | None:
        """Update a brand profile by merging in new data."""
        async for session in get_session():
            record = await session.get(BrandProfileTable, brand_id)
            if not record:
                return None
            existing = json.loads(record.data_json)
            existing.update(updates)
            record.data_json = json.dumps(existing)
            record.name = existing.get("name", record.name)
            record.updated_at = datetime.now(UTC)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    async def delete(self, brand_id: UUID) -> bool:
        """Delete a brand profile. Returns True if deleted, False if not found."""
        async for session in get_session():
            record = await session.get(BrandProfileTable, brand_id)
            if not record:
                return False
            await session.delete(record)
            await session.commit()
            return True


# ── JobStore ──────────────────────────────────────────────────────────────────


class JobStore:
    """Job lifecycle management."""

    async def create_job(
        self,
        request_data: dict[str, Any],
        brand_id: UUID | None = None,
    ) -> JobTable:
        """Create a new job record with pending status."""
        async for session in get_session():
            job = JobTable(
                status="pending",
                brand_id=brand_id,
                request_json=json.dumps(request_data),
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            logger.debug("Created job: %s", job.id)
            return job

    async def get_job(self, job_id: UUID) -> JobTable | None:
        """Fetch a job by ID."""
        async for session in get_session():
            return await session.get(JobTable, job_id)

    async def update_job_status(self, job_id: UUID, status: str, error: str | None = None) -> None:
        """Update job status and optionally set an error message."""
        async for session in get_session():
            job = await session.get(JobTable, job_id)
            if job:
                job.status = status
                job.error = error
                job.updated_at = datetime.now(UTC)
                session.add(job)
                await session.commit()

    async def update_job_outputs(
        self,
        job_id: UUID,
        outputs: dict[str, Any],
        state_snapshot: dict[str, Any] | None = None,
    ) -> None:
        """Store serialised outputs (and optionally full state) on the job."""
        async for session in get_session():
            job = await session.get(JobTable, job_id)
            if job:
                job.outputs_json = json.dumps(outputs)
                if state_snapshot:
                    job.state_json = json.dumps(state_snapshot)
                job.updated_at = datetime.now(UTC)
                session.add(job)
                await session.commit()

    async def update_job_state(self, job_id: UUID, state_snapshot: dict[str, Any]) -> None:
        """Update the full state snapshot for a job."""
        async for session in get_session():
            job = await session.get(JobTable, job_id)
            if job:
                job.state_json = json.dumps(state_snapshot, default=str)
                job.updated_at = datetime.now(UTC)
                session.add(job)
                await session.commit()


# ── Singletons ────────────────────────────────────────────────────────────────
brand_store = BrandStore()
job_store = JobStore()
