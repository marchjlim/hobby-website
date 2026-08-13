from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.errors import AuthApiError
from supabase import Client

from database import create_authenticated_client, supabase


# HTTPBearer is a FastAPI security dependency. It knows how to read an http header formatted asd
# Authorization: Bearer <token>. It doesn't validate anything, only parses
# Eg Authorization: Bearer abc123 ->
# HTTPAuthorizationCredentials(scheme = "Bearer", credentials = "abc123")
bearer_scheme = HTTPBearer(auto_error=False)

# FastAPI Dependency injection: examines function params marked with Depends(...)
# then runs those dependencies before the endpoint and passing their return values into the params
def get_authenticated_access_token(
    # 'credentials' has the type HTTPAuthorizationCredentials | None, and FastAPI should obtain it using bearer_scheme.
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    """Extract and validate the caller's Supabase access token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = credentials.credentials

    try:
        # Validate with Supabase Auth instead of trusting an unverified token.
        supabase.auth.get_user(access_token)
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return access_token


def get_authenticated_supabase_client(
    access_token: Annotated[str, Depends(get_authenticated_access_token)],
) -> Client:
    """Return a request-scoped client carrying the validated user's JWT."""
    return create_authenticated_client(access_token)

def require_admin(
    access_token: Annotated[str, Depends(get_authenticated_access_token)],
    client: Annotated[Client, Depends(get_authenticated_supabase_client)],
) -> Client:
    auth_user = supabase.auth.get_user(access_token).user
    profile = (
        client.table("Users")
        .select("is_admin")
        .eq("auth_user_id", str(auth_user.id))
        .maybe_single()
        .execute()
    )
    if not profile.data or not profile.data["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return client
