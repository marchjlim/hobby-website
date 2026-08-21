from collections import defaultdict
from difflib import SequenceMatcher
import json
import logging
import re
from statistics import median

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from supabase import Client

from database import supabase
from services.gemini import request_gemini, request_gemini_embedding


logger = logging.getLogger(__name__)
MAX_PREDICTION_IMAGE_BYTES = 4 * 1024 * 1024
ALLOWED_PREDICTION_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_TAG_SUGGESTIONS = 7
MAX_COMPARABLE_LISTINGS = 15
MIN_COMPARABLE_PRICES = 2
PRODUCT_MATCH_THRESHOLD = 0.65

# DB fields
PRODUCT_FIELDS = (
    "id,canonical_name,grade,scale,msrp,msrp_currency,"
    "original_release_date,last_reproduction_date"
)
TAGGED_FIELDS = (
    "ListingId,TagName"
)
COMPARABLE_LISTING_FIELDS = (
    "id,product_id,name,price,carousell_price,created_at,is_active"
)

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
        "- Grade tags such as HG, RG, MG, MGEX, or PG refer to the product grade printed on the box. Select at most one grade.",
        "- 'Clear Color' applies only when the product or packaging explicitly indicates a transparent/clear-color edition.",
        "- 'Gundam Base Limited' applies only when the packaging indicates it.",
        "- 'Event limited' applies when the box contains 'Limited Item'",
        "- 'P-bandai' usually applies when the box is monochrome/greyscale and has no 'Limited item'",
        "- 'Standard Release' usually applies when the item is not event limited, P-Bandai, or Gundam Base Limited.",
    ]
    instructions = (
        "Suggest a listing name formatted as grade, scale, then product name. "
        "Include visible edition text. Write a concise 1-2 sentence description only "
        "about the model itself and its source series when identifiable from the packaging. "
        "Do not explain grades, scales, or model-kit terminology, and do not include generic "
        "marketing filler or claims about condition, completeness, or authenticity. "
        f"Suggest up to {MAX_TAG_SUGGESTIONS} tags for this Gundam box image. "
        "Use only exact tags from this allowed list: "
        + json.dumps(allowed_tags)
    )
    return instructions + "\n\nRules:\n" + "\n".join(rules)


def get_allowed_tags() -> list[str]:
    response = supabase.table("ListingTag").select("name").execute()
    return [row["name"] for row in response.data]


def tag_weight(tag: str) -> int:
    return TAG_WEIGHTS.get(tag.casefold(), 1)


def rank_price_comparables(
    listings: list[dict],
    relationships: list[dict],
    requested_tags: list[str],
    target_product: dict | None = None,
) -> list[dict]:
    requested_tag_set = set(requested_tags)
    matches_by_listing = defaultdict(set)
    for relationship in relationships:
        tag = relationship["TagName"]
        if tag in requested_tag_set and tag_weight(tag) > 0:
            matches_by_listing[relationship["ListingId"]].add(tag)

    ranked = []
    for listing in listings:
        matched_tags = matches_by_listing.get(listing["id"], set())
        if not matched_tags:
            continue
        product_metadata = listing.get("product_metadata")
        product_match_score = sum(
            product_metadata.get(field) is not None
            and product_metadata.get(field) == target_product.get(field)
            for field in ("grade", "scale")
        ) if product_metadata and target_product else 0
        ranked.append({
            "id": listing["id"],
            "product_id": listing.get("product_id"),
            "name": listing["name"],
            "price": listing.get("price"),
            "carousell_price": listing.get("carousell_price"),
            "created_at": listing.get("created_at"),
            "is_active": listing.get("is_active"),
            "matched_tags": sorted(matched_tags),
            "match_score": sum(tag_weight(tag) for tag in matched_tags),
            "product_match_score": product_match_score,
            "product_metadata": product_metadata,
            "retrieval_tier": "tag_match",
        })

    return sorted(
        ranked,
        key=lambda listing: (
            listing["match_score"],
            listing["product_match_score"],
            len(listing["matched_tags"]),
            listing.get("created_at") or "",
        ),
        reverse=True,
    )[:MAX_COMPARABLE_LISTINGS]


def get_price_comparables(
    client: Client,
    tags: list[str],
    product: dict,
) -> list[dict]:
    try:
        exact_listings = (
            client.table("Listings")
            .select(COMPARABLE_LISTING_FIELDS)
            .eq("product_id", product["id"])
            .eq("is_active", False)
            .order("created_at", desc=True)
            .execute()
            .data
        )

        relationships = []
        tagged_listings = []
        if tags:
            relationships = (
                client.table("Tagged")
                .select(TAGGED_FIELDS)
                .in_("TagName", tags)
                .execute()
                .data
            )
            listing_ids = sorted({row["ListingId"] for row in relationships})
            if listing_ids:
                tagged_listings = (
                    client.table("Listings")
                    .select(COMPARABLE_LISTING_FIELDS)
                    .in_("id", listing_ids)
                    .execute()
                    .data
                )

        product_by_id = {product["id"]: product}
        other_product_ids = sorted({
            listing["product_id"]
            for listing in tagged_listings
            if listing.get("product_id") is not None
            and listing["product_id"] != product["id"]
        })
        if other_product_ids:
            products = (
                client.table("products")
                .select(PRODUCT_FIELDS)
                .in_("id", other_product_ids)
                .execute()
                .data
            )
            product_by_id.update({item["id"]: item for item in products})

        enriched_tagged_listings = [
            {
                **listing,
                "product_metadata": product_by_id.get(listing.get("product_id")),
            }
            for listing in tagged_listings
        ]
        ranked_tag_matches = rank_price_comparables(
            enriched_tagged_listings,
            relationships,
            tags,
            product,
        )
        ranked_by_id = {item["id"]: item for item in ranked_tag_matches}
        exact_comparables = []
        for listing in exact_listings:
            comparable = ranked_by_id.get(listing["id"], {
                **listing,
                "matched_tags": [],
                "match_score": 0,
                "product_match_score": 2,
                "product_metadata": product,
            })
            exact_comparables.append({
                **comparable,
                "retrieval_tier": "same_product",
            })

        exact_ids = {item["id"] for item in exact_comparables}
        return (
            exact_comparables
            + [item for item in ranked_tag_matches if item["id"] not in exact_ids]
        )[:MAX_COMPARABLE_LISTINGS]
    except Exception:
        logger.exception("Unable to fetch comparable listings")
        return []

def normalize_product_name(name: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", name.casefold()))


def best_product_match(name: str, candidates: list[dict]) -> dict | None:
    normalized = normalize_product_name(name)
    return max(
        candidates,
        key=lambda product: SequenceMatcher(
            None, normalized, normalize_product_name(product["canonical_name"])
        ).ratio(),
        default=None,
    )


def _get_lexical_product_match(client: Client, name: str) -> dict | None:

    try:
        exact = (
            client.table("products")
            .select(PRODUCT_FIELDS)
            .ilike("canonical_name", name)
            .limit(1)
            .execute()
        )
        if exact.data:
            return exact.data[0]

        grade_match = re.search(r"\b(HG|RG|MGEX|MG|PG|RE/100)\b", name, re.IGNORECASE)
        scale_match = re.search(r"\b1/(?:60|100|144)\b", name)
        ignored = {
            "hg", "rg", "mg", "pg", "re", "100", "1", "60", "144",
            "gundam", "model", "kit", "the", "ver", "version", "limited",
        }
        distinctive = sorted(
            (word for word in normalize_product_name(name).split()
             if word not in ignored and len(word) > 2),
            key=len,
            reverse=True,
        )
        if not distinctive:
            return None

        candidates = {}
        for word in distinctive[:3]:
            query = client.table("products").select(PRODUCT_FIELDS)
            if grade_match:
                query = query.eq("grade", grade_match.group().upper())
            if scale_match:
                query = query.eq("scale", scale_match.group())
            for product in (
                query.ilike("canonical_name", f"%{word}%")
                .limit(100)
                .execute()
                .data
            ):
                candidates[product["id"]] = product
        return best_product_match(name, list(candidates.values()))
    except Exception:
        logger.info("Product catalogue is unavailable or has no migration", exc_info=True)
        return None


def get_product_metadata(client: Client, name: str) -> dict | None:
    try:
        query_embedding = request_gemini_embedding(
            f'task: search result | query: {name}'
        )
        response = client.rpc(
            'match_products',
            {
                'query_embedding': query_embedding,
                'match_threshold': PRODUCT_MATCH_THRESHOLD,
                'match_count': 1,
            },
        ).execute()
        if response.data:
            return response.data[0]
    except Exception:
        logger.info('Semantic product search failed; using lexical fallback', exc_info=True)

    return _get_lexical_product_match(client, name)


def median_price(comparables: list[dict], field: str) -> float | None:
    prices = [
        float(listing[field])
        for listing in comparables
        if listing.get(field) is not None
    ]
    if len(prices) < MIN_COMPARABLE_PRICES:
        return None
    return round(float(median(prices)), 2)


def calculate_pricing(comparables: list[dict], 
                      product_metadata: dict | None = None) -> dict:
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
            "prices. Exact-product listings are prioritised, followed by shared tags "
            f"and product metadata. Matched tags: {', '.join(matched_tags)}."
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
    product_id: int | None,
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
                "product_id": product_id,
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


def generate_pricing(client: Client, product: dict, 
                     listing_name: str, tags: list[str]) -> dict:
    # do not use product metadata if msrp is not available in the db
    product_metadata = product if product.get("msrp") is not None else None
    pricing = calculate_pricing(get_price_comparables(client, tags, product), product_metadata)
    if pricing["pricing_comparables"]:
        try:
            analysis = request_gemini(
                build_pricing_prompt(listing_name, tags, pricing),
                PricingAnalysis,
                attempts=5,
            )
            pricing = apply_pricing_analysis(pricing, analysis)
        except HTTPException:
            logger.warning("Gemini pricing analysis failed; using baseline pricing")

    return {
        "pricing_suggestion_id": record_pricing_suggestion(
            client, tags, pricing, product["id"]
        ),
        **pricing,
    }


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


def generate_listing_details(image: UploadFile, client: Client) -> dict:
    content = read_prediction_image(image)
    allowed_tags = get_allowed_tags()
    parsed = request_gemini(
        build_prompt(allowed_tags),
        ListingDetailsSuggestion,
        content,
        image.content_type,
        attempts=5,
    )
    tag_suggestions = keep_allowed_tag_suggestions(
        parsed.tag_suggestions,
        allowed_tags,
    )
    suggested_product = get_product_metadata(client, parsed.name)
    tags = [suggestion.tag for suggestion in tag_suggestions]
    result = {
        "name": parsed.name,
        "description": parsed.description,
        "suggested_product_name": (
            suggested_product["canonical_name"] if suggested_product else None
        ),
        "suggested_product_id": suggested_product["id"] if suggested_product else None,
        "tag_suggestions": [
            suggestion.model_dump() for suggestion in tag_suggestions
        ],
    }
    if suggested_product:
        result.update(generate_pricing(client, suggested_product, parsed.name, tags))
    return result


def generate_product_pricing(client: Client, product_id: int, 
                             listing_name: str, tags: list[str]) -> dict:
    product_response = (
        client.table("products")
        .select(PRODUCT_FIELDS)
        .eq("id", product_id)
        .maybe_single() # tells supabase that the query should return 0 or 1 row, rather than a list of rows
        .execute()
    )
    if not product_response.data:
        raise HTTPException(status_code=422, detail="Selected product does not exist")

    return generate_pricing(client, product_response.data, listing_name, tags)
