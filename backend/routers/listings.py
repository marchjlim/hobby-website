import httpx
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from auth import get_authenticated_supabase_client
from models.tag import Tag
from models.relationships import AttachTagToListingsRequest, ListingTag

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

@router.post("/tag")
def upsert_tag(
    tag: Tag,
    # Reject missing or invalid JWTs before the write operation runs.
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        tag_data = tag.model_dump() # supabase expects dict representation of database row
        response = (
            authenticated_supabase.table("ListingTag")
                    .upsert(tag_data)
                    .execute()
        )
        return {
            "results": response.data
        }
    except httpx.HTTPError as exc:
        raise HTTPException(
                status_code = 503,
                detail = f"Unable to reach Supabase while upserting tag: {tag}"
            ) from exc

@router.post("/{listing_id}/tag")
def add_tag_to_listing(
    listing_id: int,
    tag: Tag,
    # Reject missing or invalid JWTs before the write operation runs.
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        tag_name = tag.name
        listing_tag = ListingTag(listing_id = listing_id, tag_name = tag_name)
        listing_tag_data = listing_tag.model_dump(by_alias = True)
        response = (
            authenticated_supabase.table("Tagged")
                    .upsert(listing_tag_data)
                    .execute()
        )
        return {
            "results": response.data
        }
    except httpx.HTTPError as exc:
        raise HTTPException(
                status_code = 503,
                detail = f"Unable to reach Supabase while upserting listing tag relationship: {listing_tag}"
            ) from exc

@router.post("/tags/attach")
def attach_tag_to_listings(
    request: AttachTagToListingsRequest,
    # Reuse one authenticated client for this request's database work.
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    deduped_listing_ids = set(request.listing_ids)
    relationships = [
        ListingTag(listing_id=listing_id, tag_name=request.tag_name)
        .model_dump(by_alias=True)
        for listing_id in deduped_listing_ids
    ]

    try:
        response = (
            authenticated_supabase.table("Tagged")
            .upsert(relationships)
            .execute()
        )
        return {"results": response.data}
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to reach Supabase while attaching tag "
                f"{request.tag_name} to listings"
            ),
        ) from exc