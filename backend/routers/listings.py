import json
import logging
import mimetypes
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from supabase import Client

from auth import get_authenticated_supabase_client
from models.listing import ListingCreationRequest, ListingUpdateRequest
from models.tag import Tag, TagRenameRequest
from models.relationships import AttachTagToListingsRequest, ListingTag

from database import supabase

# APIRouter == way of grouping related endpoints before attaching them to the main app
# Can think of APIRouter being a subset of the whole application. FastAPI() is the whole application
# prefix param: path that gets added in front of every route inside that router
# tags param: for documentation. FastAPI automatically generates Swagger docs at /docs, the tags controls
# how endpoints are grouped in those docs
router = APIRouter(prefix="/api/listings", tags=["listings"])
logger = logging.getLogger(__name__)

async def upload_listing_image(
    image: UploadFile,
    authenticated_supabase: Client,
) -> str:
    suffix = Path(image.filename or "").suffix
    prefix = uuid4().hex # generate unique prefix
    file_path = f"{prefix}{suffix}"
    content = await image.read()
    content_type = image.content_type or mimetypes.guess_type(file_path)[0]
    options = {"content-type": content_type} if content_type else None

    # upload to supabase
    authenticated_supabase.storage.from_("listing-images").upload(
        file_path,
        content,
        options,
    )

    # return public url from supabase
    return authenticated_supabase.storage.from_("listing-images").get_public_url(
        file_path
    )


def sync_listing_tags(
    authenticated_supabase: Client,
    listing_id: int,
    tags: list[str],
) -> None:
    # insert tags and relationships
    for tag_name in tags:
        authenticated_supabase.table("ListingTag").upsert(
            {"name": tag_name},
            on_conflict="name",
        ).execute()
        authenticated_supabase.table("Tagged").upsert({
            "TagName": tag_name,
            "ListingId": listing_id,
        }).execute()

    current_response = (
        authenticated_supabase.table("Tagged")
        .select("TagName")
        .eq("ListingId", listing_id)
        .execute()
    )
    desired_lowercase_tags = set([tag_name.lower() for tag_name in tags])
    for relationship in current_response.data:
        current_tag = relationship["TagName"]
        # remove stale relationships
        if current_tag.lower() not in desired_lowercase_tags:
            (
                authenticated_supabase.table("Tagged")
                .delete()
                .eq("ListingId", listing_id)
                .eq("TagName", current_tag)
                .execute()
            )

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


@router.post("")
async def create_listing(
    payload: str = Form(),
    image: UploadFile | None = File(default=None),
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        request = ListingCreationRequest.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc

    try:
        if request.product_id is not None:
            product = (
                authenticated_supabase.table("products")
                .select("id")
                .eq("id", request.product_id)
                .maybe_single()
                .execute()
            )
            if not product.data:
                raise HTTPException(status_code=422, detail="Selected product does not exist")

        image_url = request.image_url
        if image:
            image_url = await upload_listing_image(image, authenticated_supabase)

        listing = request.to_listing(image_url=image_url)
        listing_data = listing.to_dict(exclude_none=True)
        response = (
            authenticated_supabase.table("Listings")
            .insert(listing_data)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=502, detail="Supabase did not return the listing")
        created_listing = response.data[0]
        sync_listing_tags(authenticated_supabase, created_listing["id"], request.tags)
        if request.pricing_suggestion_id:
            try:
                (
                    authenticated_supabase.table("AiPricingSuggestions")
                    .update({
                        "accepted_listing_id": created_listing["id"],
                        "accepted_price": created_listing["price"],
                        "accepted_carousell_price": created_listing.get("carousell_price"),
                    })
                    .eq("id", request.pricing_suggestion_id)
                    .execute()
                )
            except Exception:
                logger.warning(
                    "Unable to record the accepted AI price",
                    exc_info=True,
                )
        return {"result": created_listing}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to create listing") from exc


@router.patch("/tags/{tag_name}")
def rename_tag(
    tag_name: str,
    request: TagRenameRequest,
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        response = (
            authenticated_supabase.table("ListingTag")
            .update({"name": request.name})
            .eq("name", tag_name)
            .execute()
        )
        return {"results": response.data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to rename tag") from exc


@router.get("/tags/{tag_name}/usage")
def get_tag_usage(tag_name: str):
    try:
        response = (
            supabase.table("Tagged")
            .select("*", count="exact", head=True)
            .eq("TagName", tag_name)
            .execute()
        )
        return {"count": response.count or 0}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to count tag usage") from exc


@router.delete("/tags/{tag_name}")
def delete_tag(
    tag_name: str,
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        (
            authenticated_supabase.table("Tagged")
            .delete()
            .ilike("TagName", tag_name)
            .execute()
        )
        response = (
            authenticated_supabase.table("ListingTag")
            .delete()
            .ilike("name", tag_name)
            .execute()
        )
        return {"results": response.data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to delete tag") from exc


@router.patch("/{listing_id}")
async def update_listing(
    listing_id: int,
    payload: str = Form(),
    image: UploadFile | None = File(default=None),
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        request = ListingUpdateRequest.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc

    try:
        listing_update = request.to_listing_update()
        if image:
            listing_update = listing_update.model_copy(
                update={
                    "image_url": await upload_listing_image(
                        image,
                        authenticated_supabase,
                    )
                }
            )
        listing_data = listing_update.to_dict(exclude_unset=True)
        response = (
            authenticated_supabase.table("Listings")
            .update(listing_data)
            .eq("id", listing_id)
            .execute()
        )
        if request.tags is not None:
            sync_listing_tags(authenticated_supabase, listing_id, request.tags)
        return {"result": response.data[0] if response.data else None}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to update listing") from exc


@router.delete("/{listing_id}")
def delete_listing(
    listing_id: int,
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    try:
        response = (
            authenticated_supabase.table("Listings")
            .delete()
            .eq("id", listing_id)
            .execute()
        )
        # Supabase "Tagged" table has on delete cascade, so no need to send a req to supabase client
        return {"results": response.data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to delete listing") from exc

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


@router.post("/tags/attach")
def attach_tag_to_listings(
    request: AttachTagToListingsRequest,
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    relationships = [
        ListingTag(listing_id=listing_id, tag_name=request.tag_name)
        .model_dump(by_alias=True)
        for listing_id in request.listing_ids
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
