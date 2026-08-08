from pydantic import BaseModel, Field

from models.base import SupabaseModel


class ListingTag(SupabaseModel):
    listing_id: int = Field(alias="ListingId")
    tag_name: str = Field(alias="TagName")


class AttachTagToListingsRequest(BaseModel):
    tag_name: str = Field(min_length=1)
    listing_ids: list[int] = Field(min_length=1)