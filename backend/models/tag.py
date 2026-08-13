from pydantic import Field

from models.base import SupabaseModel


class Tag(SupabaseModel):
    name: str = Field(min_length=1)


class TagRenameRequest(SupabaseModel):
    name: str = Field(min_length=1)
