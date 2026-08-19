from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from supabase import Client

from auth import require_admin
from services.listing_generation import (
    generate_listing_details,
    generate_product_pricing,
)


router = APIRouter(prefix="/api/ai", tags=["ai"])


class PricingSuggestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(ge=1)
    listing_name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list, max_length=50)


@router.post("/suggest-listing-details")
def suggest_listing_details(
    image: UploadFile = File(),
    authenticated_supabase: Client = Depends(require_admin),
):
    return generate_listing_details(image, authenticated_supabase)


@router.post("/suggest-listing-pricing")
def suggest_listing_pricing(
    request: PricingSuggestionRequest,
    authenticated_supabase: Client = Depends(require_admin),
):
    return generate_product_pricing(
        authenticated_supabase,
        request.product_id,
        request.listing_name,
        request.tags,
    )
