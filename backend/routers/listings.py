import httpx
from fastapi import APIRouter, HTTPException

from database import supabase

# APIRouter == way of grouping related endpoints before attaching them to the main app
# Can think of APIRouter being a subset of the whole application. FastAPI() is the whole application
# prefix param: path that gets added in front of every route inside that router
# tags param: for documentation. FastAPI automatically generates Swagger docs at /docs, the tags controls
# how endpoints are grouped in those docs
router = APIRouter(prefix="/api/listings", tags=["listings"])

@router.get("/tags")
def get_all_tags():
    try:
        tags_response = (
            supabase.table("ListingTag")
            .select("name")
            .execute()
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code = 503,
            detail = "Unable to reach supabase while fetching tags"
        ) from exc

    return {
        "results": tags_response.data
    }

@router.get("")
def get_all_listings():
    try:
        listings_response = (
            supabase.table("Listings")
            .select("*")
            .order("created_at")
            .execute()
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to reach Supabase while fetching listings",
        ) from exc

    return {
        "results": listings_response.data
    }

@router.get("/withtags")
def get_all_listings_with_tags():
    try:
        raw_listings = get_all_listings()["results"]
        if not raw_listings:
            return {"results": []}

        unique_listing_ids = set()
        for raw_listing_entry in raw_listings:
            id = raw_listing_entry["id"]
            unique_listing_ids.add(id)

        tags_by_id = (supabase.table("Tagged")
                        .select("ListingId, TagName")
                        .in_("ListingId", list(unique_listing_ids))
                        .execute())
        id_to_tags = {}
        for id in unique_listing_ids:
            tags = []
            for entry in tags_by_id.data:
                if entry["ListingId"] == id:
                    tags.append(entry["TagName"])
            id_to_tags[id] = tags

        listings_with_tags = []
        for raw_listing in raw_listings:
            id = raw_listing["id"]
            tags = id_to_tags.get(id, [])
            raw_listing["tags"] = tags
            listings_with_tags.append(raw_listing)
        return {
            "results": listings_with_tags
        }
        
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code = 503,
            detail = "Unable to reach Supabase while fetching all listings with tags"
        ) from exc