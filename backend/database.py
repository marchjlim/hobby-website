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
