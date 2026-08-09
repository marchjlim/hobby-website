from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from auth import get_authenticated_access_token, get_authenticated_supabase_client
from database import supabase
from models.user import EmailExistsRequest


router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/email-exists")
def email_exists(request: EmailExistsRequest):
    try:
        response = (
            supabase.table("Users")
            .select("auth_user_id", count="exact", head=True)
            .eq("email", request.email)
            .execute()
        )
        return {"exists": bool(response.count)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to check email") from exc


@router.get("/me")
def get_current_user(
    access_token: str = Depends(get_authenticated_access_token),
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    auth_user = supabase.auth.get_user(access_token).user
    try:
        response = (
            authenticated_supabase.table("Users")
            .select("email,is_admin,auth_user_id")
            .eq("auth_user_id", str(auth_user.id))
            .maybe_single()
            .execute()
        )
        return {"user": response.data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to fetch user profile") from exc


@router.put("/me")
def upsert_current_user(
    access_token: str = Depends(get_authenticated_access_token),
    authenticated_supabase: Client = Depends(get_authenticated_supabase_client),
):
    """Create a profile without allowing the caller to choose admin status."""
    auth_user = supabase.auth.get_user(access_token).user
    email = auth_user.email
    if not email:
        raise HTTPException(status_code=400, detail="Authenticated user has no email")

    try:
        existing = (
            authenticated_supabase.table("Users")
            .select("auth_user_id")
            .eq("auth_user_id", str(auth_user.id))
            .maybe_single()
            .execute()
        )
        if existing.data:
            response = (
                authenticated_supabase.table("Users")
                .update({"email": email})
                .eq("auth_user_id", str(auth_user.id))
                .execute()
            )
        else:
            response = (
                authenticated_supabase.table("Users")
                .insert({
                    "email": email,
                    "is_admin": False,
                    "auth_user_id": str(auth_user.id),
                })
                .execute()
            )
        return {"user": response.data[0] if response.data else None}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to save user profile") from exc
