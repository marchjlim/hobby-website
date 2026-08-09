from datetime import datetime

from pydantic import BaseModel, Field

from models.base import SupabaseModel


class Listing(SupabaseModel):
    id: int | None = None
    name: str
    image_url: str | None = None
    price: float
    link: str | None = None
    is_preorder: bool = False
    deposit: float | None = None
    arrival_date: str | None = None
    is_restocking: bool = False
    carousell_price: float | None = None
    telegram_link: str | None = None
    created_at: datetime | None = None


class ListingCreationRequest(BaseModel):
    name: str = Field(min_length=1)
    image_url: str | None = None
    price: float = Field(ge=0)
    link: str | None = None
    is_preorder: bool = False
    deposit: float | None = Field(default=None, ge=0)
    arrival_date: str | None = None
    is_restocking: bool = False
    carousell_price: float | None = Field(default=None, ge=0)
    telegram_link: str | None = None
    tags: list[str] = Field(default_factory=list)


class ListingUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    image_url: str | None = None
    price: float | None = Field(default=None, ge=0)
    link: str | None = None
    is_preorder: bool | None = None
    deposit: float | None = Field(default=None, ge=0)
    arrival_date: str | None = None
    is_restocking: bool | None = None
    carousell_price: float | None = Field(default=None, ge=0)
    telegram_link: str | None = None
    tags: list[str] | None = None
