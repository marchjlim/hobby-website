import httpx
from fastapi import APIRouter, HTTPException, Query

from database import supabase


router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search_listings_by_tag(tag: str = Query(min_length=1)):
    normalized_tag = tag.strip()

    if not normalized_tag:
        raise HTTPException(status_code=400, detail="Tag cannot be empty")

    try:
        tagged_response = (
            supabase.table("Tagged")
            .select("ListingId")
            .ilike("TagName", normalized_tag)
            .execute()
        )

        listing_ids = [row["ListingId"] for row in tagged_response.data]

        if not listing_ids:
            return {
                "tag": normalized_tag,
                "results": [],
                "total": 0,
            }

        listings_response = (
            supabase.table("Listings")
            .select("*")
            .in_("id", listing_ids)
            .execute()
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to reach Supabase while searching listings",
        ) from exc

    return {
        "tag": normalized_tag,
        "results": listings_response.data,
        "total": len(listings_response.data),
    }
