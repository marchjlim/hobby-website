from __future__ import annotations

import argparse
from getpass import getpass
import os
from pathlib import Path
import sys
import time

import httpx
from dotenv import load_dotenv
from supabase import Client


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
EMBEDDING_DIMENSIONS = 768
DEFAULT_BATCH_SIZE = 25
MAX_ATTEMPTS = 5
RETRYABLE_STATUSES = {429, 502, 503, 504}
PRODUCT_FIELDS = (
    "id,canonical_name,grade,scale,msrp,msrp_currency,"
    "original_release_date,last_reproduction_date"
)


def build_embedding_text(product: dict) -> str:
    title = product["canonical_name"]
    parts = [title]
    if product.get("grade"):
        parts.append(f"Grade: {product['grade']}")
    if product.get("scale"):
        parts.append(f"Scale: {product['scale']}")
    text = '. '.join(parts) + '.'
    return f'title: {title} | text: {text}'


def build_embedding_requests(products: list[dict]) -> list[dict]:
    return [
        {
            "model": f"models/{EMBEDDING_MODEL}",
            "content": {"parts": [{"text": build_embedding_text(product)}]},
            "outputDimensionality": EMBEDDING_DIMENSIONS,
        }
        for product in products
    ]


def fetch_missing_products(client: Client, limit: int) -> list[dict]:
    return (
        client.table("products")
        .select(PRODUCT_FIELDS)
        .is_("embedding", "null")
        .order("id")
        .limit(limit)
        .execute()
        .data
    )


def count_missing_products(client: Client) -> int:
    response = (
        client.table("products")
        .select("id", count="exact", head=True)
        .is_("embedding", "null")
        .execute()
    )
    return response.count or 0


def embed_products(
    http: httpx.Client,
    api_key: str,
    products: list[dict],
) -> list[list[float]]:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{EMBEDDING_MODEL}:batchEmbedContents"
    )
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = http.post(
                url,
                headers={"x-goog-api-key": api_key},
                json={"requests": build_embedding_requests(products)},
            )
        except httpx.RequestError:
            if attempt == MAX_ATTEMPTS - 1:
                raise
        else:
            if response.status_code not in RETRYABLE_STATUSES:
                response.raise_for_status()
                break
            if attempt == MAX_ATTEMPTS - 1:
                response.raise_for_status()

        delay = 4 ** attempt
        print(
            f"Gemini temporarily unavailable; retrying in {delay}s "
            f"({attempt + 2}/{MAX_ATTEMPTS})",
            file=sys.stderr,
        )
        time.sleep(delay)
    else:
        raise AssertionError("unreachable")

    embeddings = [item["values"] for item in response.json()["embeddings"]]
    if len(embeddings) != len(products):
        raise ValueError("Gemini returned a different number of embeddings")
    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)}"
            )
    return embeddings


def sign_in() -> Client:
    email = input("Supabase admin email: ").strip()
    password = getpass("Supabase password: ")
    if not email or not password:
        raise ValueError("Email and password are required")

    sys.path.insert(0, str(BACKEND_DIR))
    from database import create_authenticated_client, supabase

    response = supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    return create_authenticated_client(response.session.access_token)


def preview(client: Client, limit: int | None) -> int:
    missing = count_missing_products(client)
    selected = min(missing, limit) if limit is not None else missing
    print(f"{selected} of {missing} products would be embedded")
    for product in fetch_missing_products(client, min(selected, 5)):
        print(f"[{product['id']}] {build_embedding_text(product)}")
    print("Run again with --apply to generate and store embeddings")
    return 0


def backfill(
    client: Client,
    api_key: str,
    batch_size: int,
    limit: int | None,
) -> int:
    completed = 0
    with httpx.Client(timeout=60) as http:
        while limit is None or completed < limit:
            current_batch_size = (
                batch_size if limit is None else min(batch_size, limit - completed)
            )
            products = fetch_missing_products(client, current_batch_size)
            if not products:
                break

            embeddings = embed_products(http, api_key, products)
            rows = [
                {**product, "embedding": embedding}
                for product, embedding in zip(products, embeddings, strict=True)
            ]
            client.table("products").upsert(rows, on_conflict="id").execute()
            completed += len(rows)
            print(f"Embedded {completed} products")

    print(f"Backfill complete: {completed} products embedded")
    return 0


def self_test() -> None:
    product = {
        "id": 1,
        "canonical_name": "MG 1/100 ZAKU II",
        "grade": "MG",
        "scale": "1/100",
    }
    assert build_embedding_text(product) == (
        'title: MG 1/100 ZAKU II | text: '
        'MG 1/100 ZAKU II. Grade: MG. Scale: 1/100.'
    )
    request = build_embedding_requests([product])[0]
    assert 'taskType' not in request
    assert 'title' not in request
    assert request["outputDimensionality"] == EMBEDDING_DIMENSIONS
    assert request["content"]["parts"][0]["text"] == build_embedding_text(product)

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": [{"values": [0.0] * EMBEDDING_DIMENSIONS}]}

    class Http:
        def post(self, *_args, **_kwargs):
            return Response()

    embeddings = embed_products(Http(), "test-key", [product])
    assert len(embeddings[0]) == EMBEDDING_DIMENSIONS
    print("Self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Gemini embeddings for products missing them.",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    client = sign_in()
    if not args.apply:
        return preview(client, args.limit)

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY must be configured in backend/.env')
    return backfill(client, api_key, args.batch_size, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
