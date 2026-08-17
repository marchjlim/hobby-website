from datetime import datetime

from pydantic import BaseModel, Field

from models.base import SupabaseModel


class Listing(SupabaseModel):
    id: int | None = None
    name: str
    image_url: str | None = None
    description: str | None = None
    price: float
    link: str | None = None
    is_preorder: bool = False
    deposit: float | None = None
    arrival_date: str | None = None
    is_restocking: bool = False
    carousell_price: float | None = None
    telegram_link: str | None = None
    created_at: datetime | None = None


class ListingUpdate(SupabaseModel):
    """Partial Listings row used for PATCH operations."""

    name: str | None = Field(default=None, min_length=1)
    image_url: str | None = None
    price: float | None = Field(default=None, ge=0)
    link: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    is_preorder: bool | None = None
    deposit: float | None = Field(default=None, ge=0)
    arrival_date: str | None = None
    is_restocking: bool | None = None
    carousell_price: float | None = Field(default=None, ge=0)
    telegram_link: str | None = None


class ListingCreationRequest(BaseModel):
    name: str = Field(min_length=1)
    image_url: str | None = None
    price: float = Field(ge=0)
    link: str | None = None
    is_preorder: bool = False
    description: str | None = Field(default=None, max_length=1000)
    deposit: float | None = Field(default=None, ge=0)
    arrival_date: str | None = None
    is_restocking: bool = False
    carousell_price: float | None = Field(default=None, ge=0)
    telegram_link: str | None = None
    tags: list[str] = Field(default_factory=list)

    def to_listing(self, *, image_url: str | None = None) -> Listing:
        """Convert API creation data into a Listings table model."""
        return Listing(
            name=self.name,
            image_url=image_url if image_url is not None else self.image_url,
            price=self.price,
            link=self.link,
            is_preorder=self.is_preorder,
            deposit=self.deposit,
            arrival_date=self.arrival_date,
            description=self.description,
            is_restocking=self.is_restocking,
            carousell_price=self.carousell_price,
            telegram_link=self.telegram_link,
        )


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
    description: str | None = Field(default=None, max_length=1000)
    telegram_link: str | None = None
    tags: list[str] | None = None

    def to_listing_update(self) -> ListingUpdate:
        """Convert only explicitly supplied listing fields into a partial row."""
        listing_fields = ListingUpdate.model_fields
        supplied_listing_data = {
            field_name: getattr(self, field_name)
            for field_name in self.model_fields_set
            if field_name in listing_fields
        }
        return ListingUpdate.model_validate(supplied_listing_data)
