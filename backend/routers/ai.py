import base64
from collections import defaultdict
import json
import logging
import os
from statistics import median

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from supabase import Client

from auth import require_admin
from database import supabase


router = APIRouter(prefix="/api/ai", tags=["ai"])
logger = logging.getLogger(__name__)

MAX_PREDICTION_IMAGE_BYTES = 4 * 1024 * 1024
ALLOWED_PREDICTION_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_TAG_SUGGESTIONS = 5
MAX_COMPARABLE_LISTINGS = 15
MIN_COMPARABLE_PRICES = 2

TAG_WEIGHTS = {
    "hg": 3,
    "rg": 3,
    "mg": 3,
    "pg": 3,
    "re/100": 3,
    "1/144": 3,
    "1/100": 3,
    "1/60": 3,
    "p-bandai": 2,
    "premium bandai": 2,
    "event limited": 2,
    "gundam base limited": 2,
    "standard release": 2,
    "clear color": 2,
    "special coating": 2,
    "titanium finish": 2,
    "in-stock": 0,
    "in stock": 0,
    "preorder": 0,
    "pre-order": 0,
    "restocking": 0,
    "restock": 0,
}


class SuggestedTag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: str
    confidence: float = Field(ge=0, le=1)


class ListingDetailsSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Grade, scale, and product name from the packaging")
    description: str = Field(max_length=1000)
    tag_suggestions: list[SuggestedTag] = Field(max_length=MAX_TAG_SUGGESTIONS)


class PricingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggested_price: float | None = Field(default=None, ge=0)
    suggested_carousell_price: float | None = Field(default=None, ge=0)
    rationale: str = Field(max_length=500)


def build_prompt(allowed_tags: list[str]) -> str:
    rules = [
        "- Grade tags such as HG, RG, MG, or PG refer to the product grade printed on the box. Select at most one grade.",
        "- 'Clear Color' applies only when the product or packaging explicitly indicates a transparent/clear-color edition.",
        "- 'Gundam Base Limited' applies only when the packaging indicates it.",
        "- 'Event limited' applies when the box contains 'Limited Item'",
        "- 'P-bandai' usually applies when the box is monochrome/greyscale and has no 'Limited item'",
        "- 'Standard Release' usually applies when the item is not event limited, P-Bandai, or Gundam Base Limited.",
    ]
    instructions = (
        "Suggest a listing name formatted as grade, scale, then product name. "
        "Include visible edition text. Write a concise 2-3 sentence sales description "
        "based on visible product facts; do not claim condition, completeness, or authenticity. "
        f"Suggest up to {MAX_TAG_SUGGESTIONS} tags for this Gundam box image. "
        "Use only exact tags from this allowed list: "
        + json.dumps(allowed_tags)
    )
    return instructions + "\n\nRules:\n" + "\n".join(rules)


def parse_gemini_response(response_data: dict, schema: type[BaseModel]) -> BaseModel:
    output_text = next(
        part["text"]
        for part in response_data["candidates"][0]["content"]["parts"]
        if "text" in part and not part.get("thought")
    )
    return schema.model_validate_json(output_text)


def get_allowed_tags() -> list[str]:
    response = supabase.table("ListingTag").select("name").execute()
    return [row["name"] for row in response.data]


def tag_weight(tag: str) -> int:
    return TAG_WEIGHTS.get(tag.casefold(), 1)


def rank_price_comparables(
    listings: list[dict],
    relationships: list[dict],
    requested_tags: list[str],
) -> list[dict]:
    canonical_tags = {tag.casefold(): tag for tag in requested_tags}
    matches_by_listing = defaultdict(set)
    for relationship in relationships:
        tag = canonical_tags.get(str(relationship["TagName"]).casefold())
        if tag and tag_weight(tag) > 0:
            matches_by_listing[relationship["ListingId"]].add(tag)

    ranked = []
    for listing in listings:
        matched_tags = matches_by_listing.get(listing["id"], set())
        if not matched_tags:
            continue
        ranked.append({
            "id": listing["id"],
            "name": listing["name"],
            "price": listing.get("price"),
            "carousell_price": listing.get("carousell_price"),
            "created_at": listing.get("created_at"),
            "matched_tags": sorted(matched_tags),
            "match_score": sum(tag_weight(tag) for tag in matched_tags),
        })

    return sorted(
        ranked,
        key=lambda listing: (
            listing["match_score"],
            len(listing["matched_tags"]),
            listing.get("created_at") or "",
        ),
        reverse=True,
    )[:MAX_COMPARABLE_LISTINGS]


def get_price_comparables(tags: list[str]) -> list[dict]:
    if not tags:
        return []

    try:
        relationships = (
            supabase.table("Tagged")
            .select("ListingId,TagName")
            .in_("TagName", tags)
            .execute()
            .data
        )
        listing_ids = sorted({row["ListingId"] for row in relationships})
        if not listing_ids:
            return []
        listings = (
            supabase.table("Listings")
            .select("id,name,price,carousell_price,created_at")
            .in_("id", listing_ids)
            .execute()
            .data
        )
        return rank_price_comparables(listings, relationships, tags)
    except Exception:
        logger.exception("Unable to fetch tag-matched comparable listings")
        return []


def get_product_metadata(name: str) -> dict | None:
    try:
        response = (
            supabase.table("products")
            .select(
                "id,canonical_name,grade,scale,msrp,msrp_currency,"
                "original_release_date,last_reproduction_date"
            )
            .ilike("canonical_name", name)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception:
        logger.info("Product catalogue is unavailable or has no migration", exc_info=True)
        return None


def median_price(comparables: list[dict], field: str) -> float | None:
    prices = [
        float(listing[field])
        for listing in comparables
        if listing.get(field) is not None
    ]
    if len(prices) < MIN_COMPARABLE_PRICES:
        return None
    return round(float(median(prices)), 2)


def calculate_pricing(
    comparables: list[dict],
    product_metadata: dict | None = None,
) -> dict:
    suggested_price = median_price(comparables, "price")
    suggested_carousell_price = median_price(comparables, "carousell_price")
    website_count = sum(item.get("price") is not None for item in comparables)
    carousell_count = sum(
        item.get("carousell_price") is not None for item in comparables
    )
    matched_tags = sorted({
        tag
        for comparable in comparables
        for tag in comparable["matched_tags"]
    })

    msrp_used = False
    if (
        suggested_price is None
        and product_metadata
        and product_metadata.get("msrp") is not None
        and product_metadata.get("msrp_currency") == "SGD"
    ):
        suggested_price = round(float(product_metadata["msrp"]), 2)
        msrp_used = True

    if website_count >= MIN_COMPARABLE_PRICES or carousell_count >= MIN_COMPARABLE_PRICES:
        rationale = (
            f"Median of {website_count} website and {carousell_count} Carousell "
            f"prices, ranked by shared tags: {', '.join(matched_tags)}."
        )
    elif msrp_used:
        rationale = "Not enough comparables; the website price falls back to SGD MSRP."
    else:
        rationale = (
            f"Not enough comparable prices; at least {MIN_COMPARABLE_PRICES} "
            "tag-matched listings are required."
        )

    if product_metadata:
        reproduction = product_metadata.get("last_reproduction_date") or "unknown"
        rationale += (
            f" Catalogue MSRP: {product_metadata.get('msrp_currency')} "
            f"{product_metadata.get('msrp')}; last reproduction: {reproduction}."
        )

    return {
        "suggested_price": suggested_price,
        "suggested_carousell_price": suggested_carousell_price,
        "pricing_rationale": rationale,
        "comparable_count": len(comparables),
        "pricing_comparables": comparables,
        "product_metadata": product_metadata,
    }


def build_pricing_prompt(
    name: str,
    tags: list[str],
    pricing: dict,
) -> str:
    evidence = {
        "listing_name": name,
        "tags": tags,
        "comparables": pricing["pricing_comparables"],
        "product_metadata": pricing["product_metadata"],
        "baseline": {
            "website_price": pricing["suggested_price"],
            "carousell_price": pricing["suggested_carousell_price"],
        },
    }
    return (
        "Act as a pricing analyst for a Singapore Gundam store. Recommend SGD website "
        "and Carousell prices using only the retrieved evidence below. Consider tag "
        "similarity, MSRP, release recency, and comparable prices. Do not invent market "
        "facts. Return null for a channel with no supporting price evidence. Briefly "
        "explain which evidence affected the recommendation.\n\nRetrieved evidence:\n"
        + json.dumps(evidence, default=str)
    )


def apply_pricing_analysis(pricing: dict, analysis: PricingAnalysis) -> dict:
    result = dict(pricing)
    for output_key, comparable_key in (
        ("suggested_price", "price"),
        ("suggested_carousell_price", "carousell_price"),
    ):
        prices = [
            float(item[comparable_key])
            for item in pricing["pricing_comparables"]
            if item.get(comparable_key) is not None
        ]
        suggestion = getattr(analysis, output_key)
        if (
            suggestion is not None
            and len(prices) >= MIN_COMPARABLE_PRICES
            and min(prices) <= suggestion <= max(prices)
        ):
            result[output_key] = round(suggestion, 2)

    result["pricing_rationale"] = analysis.rationale
    return result


def record_pricing_suggestion(
    client: Client,
    tags: list[str],
    pricing: dict,
    product_metadata: dict | None,
) -> str | None:
    try:
        response = (
            client.table("AiPricingSuggestions")
            .insert({
                "suggested_price": pricing["suggested_price"],
                "suggested_carousell_price": pricing["suggested_carousell_price"],
                "tag_names": tags,
                "comparable_listing_ids": [
                    item["id"] for item in pricing["pricing_comparables"]
                ],
                "product_id": product_metadata["id"] if product_metadata else None,
            })
            .execute()
        )
        return str(response.data[0]["id"]) if response.data else None
    except Exception:
        logger.warning(
            "Pricing suggestion audit was not recorded; apply the RAG migration",
            exc_info=True,
        )
        return None


def keep_allowed_tag_suggestions(
    suggested_tags: list[SuggestedTag],
    allowed_tags: list[str],
) -> list[SuggestedTag]:
    canonical = {tag.casefold(): tag for tag in allowed_tags}
    kept = {}
    for suggestion in suggested_tags:
        tag = canonical.get(suggestion.tag.casefold())
        if tag:
            current = kept.get(tag)
            if current is None or suggestion.confidence > current.confidence:
                kept[tag] = suggestion.model_copy(update={"tag": tag})

    return sorted(
        kept.values(),
        key=lambda item: item.confidence,
        reverse=True,
    )[:MAX_TAG_SUGGESTIONS]


def read_prediction_image(image: UploadFile) -> bytes:
    if image.content_type not in ALLOWED_PREDICTION_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Use a JPEG, PNG, WebP, or GIF image")

    content = image.file.read(MAX_PREDICTION_IMAGE_BYTES + 1)
    if len(content) > MAX_PREDICTION_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 4 MB or smaller")

    return content


def request_gemini(
    prompt: str,
    schema: type[BaseModel],
    content: bytes | None = None,
    content_type: str | None = None,
) -> BaseModel:
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="AI listing generation is not configured")

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    try:
        response = httpx.post(
            (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent"
            ),
            headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            json={
                "contents": [{
                    "parts": ([{
                        "inline_data": {
                            "mime_type": content_type,
                            "data": base64.b64encode(content).decode("ascii"),
                        }
                    }] if content is not None else []) + [{"text": prompt}],
                }],
                "generationConfig": {
                    "responseFormat": {
                        "text": {
                            "mimeType": "APPLICATION_JSON",
                            "schema": schema.model_json_schema(),
                        }
                    }
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        parsed = parse_gemini_response(response.json(), schema)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gemini returned HTTP %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=(
                exc.response.status_code if exc.response.status_code in {429, 503} else 502
            ),
            detail=f"Gemini returned HTTP {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        logger.exception("Unable to reach Gemini")
        raise HTTPException(status_code=502, detail="Unable to reach Gemini") from exc
    except (KeyError, StopIteration, ValueError) as exc:
        logger.exception("Unable to parse Gemini response")
        raise HTTPException(status_code=502, detail="Invalid response from Gemini") from exc

    return parsed


@router.post("/suggest-listing-details")
def suggest_listing_details(
    image: UploadFile = File(),
    authenticated_supabase: Client = Depends(require_admin),
):
    content = read_prediction_image(image)
    allowed_tags = get_allowed_tags()
    parsed = request_gemini(
        build_prompt(allowed_tags),
        ListingDetailsSuggestion,
        content,
        image.content_type,
    )
    tag_suggestions = keep_allowed_tag_suggestions(
        parsed.tag_suggestions,
        allowed_tags,
    )
    tag_names = [suggestion.tag for suggestion in tag_suggestions]
    product_metadata = get_product_metadata(parsed.name)
    pricing = calculate_pricing(get_price_comparables(tag_names), product_metadata)
    if pricing["pricing_comparables"]:
        try:
            analysis = request_gemini(
                build_pricing_prompt(parsed.name, tag_names, pricing),
                PricingAnalysis,
            )
            pricing = apply_pricing_analysis(pricing, analysis)
        except HTTPException:
            logger.warning("Gemini pricing analysis failed; using baseline pricing")
    pricing_suggestion_id = record_pricing_suggestion(
        authenticated_supabase,
        tag_names,
        pricing,
        product_metadata,
    )
    return {
        "name": parsed.name,
        "description": parsed.description,
        "tag_suggestions": [
            suggestion.model_dump() for suggestion in tag_suggestions
        ],
        "pricing_suggestion_id": pricing_suggestion_id,
        **pricing,
    }
