"""
Brand management API routes.

Full CRUD for brand profiles:
- POST   /api/v1/brands              — Create brand
- GET    /api/v1/brands              — List all brands
- GET    /api/v1/brands/{brand_id}   — Get brand
- PUT    /api/v1/brands/{brand_id}   — Update brand
- DELETE /api/v1/brands/{brand_id}   — Delete brand
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from backend.models.brand import BrandProfile, BrandProfileCreate, BrandProfileUpdate
from backend.services.brand_service import brand_service

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post(
    "",
    response_model=BrandProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Create a brand profile",
)
async def create_brand(payload: BrandProfileCreate) -> BrandProfile:
    """
    Create a new brand profile.

    The brand profile is used to inject voice, tone, and audience context
    into all generated content.
    """
    return await brand_service.create(payload)


@router.get(
    "",
    response_model=list[BrandProfile],
    summary="List all brand profiles",
)
async def list_brands() -> list[BrandProfile]:
    """Return all saved brand profiles."""
    return await brand_service.list()


@router.get(
    "/{brand_id}",
    response_model=BrandProfile,
    summary="Get a brand profile",
)
async def get_brand(brand_id: UUID) -> BrandProfile:
    """Retrieve a single brand profile by ID."""
    brand = await brand_service.get(brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand {brand_id} not found",
        )
    return brand


@router.put(
    "/{brand_id}",
    response_model=BrandProfile,
    summary="Update a brand profile",
)
async def update_brand(brand_id: UUID, payload: BrandProfileUpdate) -> BrandProfile:
    """
    Update a brand profile with partial data.

    Only provided fields are updated; omitted fields retain their current values.
    """
    brand = await brand_service.update(brand_id, payload)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand {brand_id} not found",
        )
    return brand


@router.delete(
    "/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a brand profile",
)
async def delete_brand(brand_id: UUID) -> None:
    """Delete a brand profile by ID."""
    deleted = await brand_service.delete(brand_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand {brand_id} not found",
        )
