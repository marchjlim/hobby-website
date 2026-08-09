from uuid import UUID

from pydantic import BaseModel

from models.base import SupabaseModel


class User(SupabaseModel):
    email: str
    is_admin: bool = False
    auth_user_id: UUID


class EmailExistsRequest(BaseModel):
    email: str
