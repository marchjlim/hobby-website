from uuid import UUID

from models.base import SupabaseModel


class User(SupabaseModel):
    email: str
    is_admin: bool = False
    auth_user_id: UUID