from __future__ import annotations

import argparse
from getpass import getpass
import json
import mimetypes
import sys
import time
from pathlib import Path
from urllib.parse import urlparse



DEFAULT_API_URL = "http://127.0.0.1:8000"
MAX_RETRIES = 5
RETRY_BASE_SECONDS = 5
RETRYABLE_STATUSES = {429, 502, 503}


def select_listings(listings: list[dict], overwrite: bool, limit: int | None) -> list[dict]:
    selected = [
        listing
        for listing in listings
        if listing.get("image_url") and (overwrite or not listing.get("description"))
    ]
    return selected[:limit] if limit is not None else selected


def request_with_retry(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
    for attempt in range(MAX_RETRIES):
        response = client.request(method, url, **kwargs)
        if response.status_code not in RETRYABLE_STATUSES or attempt == MAX_RETRIES - 1:
            return response
        delay = RETRY_BASE_SECONDS * 2 ** attempt
        print(
            f"HTTP {response.status_code}; retrying in {delay} seconds "
            f"({attempt + 2}/{MAX_RETRIES})",
            file=sys.stderr,
        )
        time.sleep(delay)
    raise AssertionError("unreachable")


def image_filename(image_url: str, content_type: str) -> str:
    filename = Path(urlparse(image_url).path).name
    if filename:
        return filename
    return "listing" + (mimetypes.guess_extension(content_type) or ".jpg")


def verify_description_only(before: dict, after: dict, description: str) -> None:
    if after.get("description") != description:
        raise ValueError("description was not updated to the generated value")

    changed = [
        key
        for key, value in after.items()
        if key != "description" and key in before and before[key] != value
    ]
    if changed:
        raise ValueError(f"unexpected fields changed: {', '.join(changed)}")


def sign_in() -> str:
    email = input("Supabase admin email: ").strip()
    password = getpass("Supabase password: ")
    if not email or not password:
        raise ValueError("Email and password are required")

    backend_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_dir))
    from database import supabase

    response = supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    return response.session.access_token


def backfill(
    api_url: str,
    access_token: str,
    apply: bool,
    overwrite: bool,
    limit: int | None,
) -> int:
    import httpx

    headers = {"Authorization": f"Bearer {access_token}"}
    failures = 0

    with httpx.Client(timeout=60, follow_redirects=True) as client:
        listings_response = client.get(f"{api_url}/api/listings/withtags")
        listings_response.raise_for_status()
        listings = select_listings(
            listings_response.json().get("results", []),
            overwrite,
            limit,
        )

        print(f"{'Updating' if apply else 'Previewing'} {len(listings)} listings")
        for listing in listings:
            listing_id = listing["id"]
            try:
                image_response = client.get(listing["image_url"])
                image_response.raise_for_status()
                content_type = image_response.headers.get(
                    "content-type",
                    "image/jpeg",
                ).split(";", 1)[0]

                ai_response = request_with_retry(
                    client,
                    "POST",
                    f"{api_url}/api/ai/suggest-listing-details",
                    headers=headers,
                    files={
                        "image": (
                            image_filename(listing["image_url"], content_type),
                            image_response.content,
                            content_type,
                        )
                    },
                )
                ai_response.raise_for_status()
                description = ai_response.json()["description"].strip()
                if not description:
                    raise ValueError("Gemini returned an empty description")
                print(f"[{listing_id}] {listing['name']}: {description}")

                if apply:
                    update_payload = {"description": description}
                    if set(update_payload) != {"description"}:
                        raise ValueError("update payload contains fields besides description")
                    update_response = client.patch(
                        f"{api_url}/api/listings/{listing_id}",
                        headers=headers,
                        files={
                            "payload": (
                                None,
                                json.dumps(update_payload),
                            )
                        },
                    )
                    update_response.raise_for_status()
                    updated_listing = update_response.json().get("result")
                    if not updated_listing:
                        raise ValueError("update returned no listing")
                    verify_description_only(listing, updated_listing, description)
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                failures += 1
                print(f"[{listing_id}] failed: {exc}", file=sys.stderr)

    print(f"Completed with {failures} failure(s)")
    return 1 if failures else 0


def self_test() -> None:
    listings = [
        {"id": 1, "image_url": "one.jpg", "description": None},
        {"id": 2, "image_url": "two.jpg", "description": "Done"},
        {"id": 3, "image_url": None, "description": None},
    ]
    assert [item["id"] for item in select_listings(listings, False, None)] == [1]
    assert [item["id"] for item in select_listings(listings, True, 1)] == [1]
    assert image_filename("https://example.com/path/box.png", "image/png") == "box.png"
    assert [RETRY_BASE_SECONDS * 2 ** attempt for attempt in range(4)] == [5, 10, 20, 40]

    before = {"id": 1, "name": "Kit", "description": None}
    verify_description_only(
        before,
        {"id": 1, "name": "Kit", "description": "Generated"},
        "Generated",
    )
    try:
        verify_description_only(
            before, {"id": 1, "name": "Changed", "description": "Generated"}, "Generated"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unexpected field change was not detected")
    print("Self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate missing listing descriptions through the deployed API.",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--apply", action="store_true", help="Write descriptions")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    access_token = sign_in()
    return backfill(
        args.api_url.rstrip("/"),
        access_token,
        args.apply,
        args.overwrite,
        args.limit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
