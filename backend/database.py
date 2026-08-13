import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


env_path = Path(__file__).resolve().parent / ".env"

print("Environment path:", env_path)
print("File exists:", env_path.is_file())
loaded = load_dotenv(env_path)

print("File loaded:", loaded)
print("URL available:", bool(os.getenv("SUPABASE_URL")))
print("Key available:", bool(os.getenv("SUPABASE_ANON_KEY")))

supabase_url = os.getenv("SUPABASE_URL")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_anon_key:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_ANON_KEY must be configured in backend/.env"
    )

supabase: Client = create_client(supabase_url, supabase_anon_key)
print("Successfully initiated supabase client")


def create_authenticated_client(access_token: str) -> Client:
    # Authentication headers are mutable, so create a separate client for each
    # HTTP request instead of placing a user's token on the shared public client.
    client = create_client(supabase_url, supabase_anon_key)
    auth_header = f"Bearer {access_token}"
    # Storage and any other Supabase subclients must receive the same user JWT.
    client.options.headers["Authorization"] = auth_header
    client.auth._headers["Authorization"] = auth_header
    # PostgREST forwards this JWT to PostgreSQL, where Supabase RLS evaluates
    # the request as the signed-in user rather than as the anon role.
    client.postgrest.auth(access_token)
    return client
