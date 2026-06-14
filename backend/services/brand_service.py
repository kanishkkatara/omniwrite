"""
Brand Service.

Business-logic layer for brand profile CRUD operations.
Converts between Pydantic models and database records.
"""
from __future__ import annotations

import json
import logging
from uuid import UUID

from backend.models.brand import BrandProfile, BrandProfileCreate, BrandProfileUpdate
from backend.services.storage import brand_store

logger = logging.getLogger(__name__)


def _record_to_model(record) -> BrandProfile:
    """Convert a BrandProfileTable record to a BrandProfile Pydantic model."""
    data = json.loads(record.data_json)
    # Ensure ID is set from the DB record
    data["id"] = str(record.id)
    data["created_at"] = record.created_at.isoformat()
    data["updated_at"] = record.updated_at.isoformat()
    return BrandProfile.model_validate(data)


class BrandService:
    """Service layer for brand profile management."""

    async def create(self, brand_create: BrandProfileCreate) -> BrandProfile:
        """
        Create a new brand profile.

        Args:
            brand_create: Validated brand creation data.

        Returns:
            The persisted BrandProfile with ID and timestamps.
        """
        data = brand_create.model_dump(mode="json")
        record = await brand_store.create(data)
        result = _record_to_model(record)
        logger.info("Created brand: %s (id=%s)", result.name, result.id)
        return result

    async def get(self, brand_id: UUID) -> BrandProfile | None:
        """
        Retrieve a brand profile by ID.

        Args:
            brand_id: UUID of the brand.

        Returns:
            BrandProfile if found, None otherwise.
        """
        record = await brand_store.get(brand_id)
        if not record:
            return None
        return _record_to_model(record)

    async def list(self) -> list[BrandProfile]:
        """
        List all brand profiles.

        Returns:
            List of all BrandProfile objects (may be empty).
        """
        records = await brand_store.list_all()
        return [_record_to_model(r) for r in records]

    async def update(self, brand_id: UUID, update: BrandProfileUpdate) -> BrandProfile | None:
        """
        Update a brand profile with partial data.

        Args:
            brand_id: UUID of the brand to update.
            update: Partial update data (None fields are ignored).

        Returns:
            Updated BrandProfile if found, None otherwise.
        """
        updates = update.model_dump(exclude_none=True, mode="json")
        if not updates:
            # Nothing to update — return current
            return await self.get(brand_id)

        record = await brand_store.update(brand_id, updates)
        if not record:
            return None
        result = _record_to_model(record)
        logger.info("Updated brand: %s (id=%s)", result.name, brand_id)
        return result

    async def delete(self, brand_id: UUID) -> bool:
        """
        Delete a brand profile.

        Args:
            brand_id: UUID of the brand to delete.

        Returns:
            True if deleted, False if not found.
        """
        deleted = await brand_store.delete(brand_id)
        if deleted:
            logger.info("Deleted brand: id=%s", brand_id)
        return deleted


# ── Singleton ─────────────────────────────────────────────────────────────────
brand_service = BrandService()
