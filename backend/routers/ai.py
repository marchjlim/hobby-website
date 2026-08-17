import base64
import json
import logging
import os

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

class SuggestedTag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: str
    confidence: float = Field(ge=0, le=1)


class TagSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestions: list[SuggestedTag] = Field(max_length=MAX_TAG_SUGGESTIONS)


class ListingDetailsSuggestion(TagSuggestions):
    name: str = Field(description="Grade, scale, and product name from the packaging")


def build_prompt(allowed_tags: list[str], *, include_name: bool = False) -> str:
    rules = [
        "- Grade tags such as HG, RG, MG, or PG refer to the product grade printed on the box. Select at most one grade.",
        "- 'Clear Color' applies only when the product or packaging explicitly indicates a transparent/clear-color edition.",
        "- 'Gundam Base Limited' applies only when the packaging indicates it.",
        "- 'Event limited' applies when the box contains 'Limited Item'",
        "- 'P-bandai' usually applies when the box is monochrome/greyscale and has no 'Limited item'",
        "- 'Standard Release' usually applies when the item is not event limited, P-Bandai, or Gundam Base Limited.",
    ]
    instructions = []
    if include_name:
        instructions.append(
            "Suggest a listing name formatted as grade, scale, then product name. "
            "Include visible edition text."
        )
    instructions.append(
        f"Suggest up to {MAX_TAG_SUGGESTIONS} tags for this Gundam box image. "
        "Use only exact tags from this allowed list: "
        + json.dumps(allowed_tags)
    )
    return "\n\n".join(instructions) + "\n\nRules:\n" + "\n".join(rules)


def parse_gemini_tag_suggestions(response_data: dict) -> TagSuggestions:
    return parse_gemini_response(response_data, TagSuggestions)


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


def keep_allowed_suggestions(
    suggestions: list[SuggestedTag],
    allowed_tags: list[str],
) -> list[SuggestedTag]:
    canonical = {tag.casefold(): tag for tag in allowed_tags}
    kept = {} # maps tag str to SuggestedTag
    for suggestion in suggestions:
        tag = canonical.get(suggestion.tag.casefold())
        if tag:
            confidence = suggestion.confidence
            current = kept.get(tag)
            if current is None or confidence > current.confidence:
                # add if tag is not yet added or confidences exceeds curr confidence
                kept[tag] = suggestion.model_copy(update={"tag": tag})
    
    return sorted(kept.values(), key=lambda item: item.confidence, reverse=True)[:MAX_TAG_SUGGESTIONS]


def read_prediction_image(image: UploadFile) -> bytes:
    if image.content_type not in ALLOWED_PREDICTION_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Use a JPEG, PNG, WebP, or GIF image")

    content = image.file.read(MAX_PREDICTION_IMAGE_BYTES + 1)
    if len(content) > MAX_PREDICTION_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 4 MB or smaller")

    return content


def request_gemini(
    content: bytes,
    content_type: str,
    prompt: str,
    schema: type[BaseModel],
) -> BaseModel:
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Tag prediction is not configured")

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
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": content_type,
                                "data": base64.b64encode(content).decode("ascii"),
                            }
                        },
                        {
                            "text": prompt,
                        },
                    ],
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
            status_code=503 if exc.response.status_code == 503 else 502,
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
    _: Client = Depends(require_admin),
):
    content = read_prediction_image(image)
    allowed_tags = get_allowed_tags()
    parsed = request_gemini(
        content,
        image.content_type,
        build_prompt(allowed_tags, include_name=True),
        ListingDetailsSuggestion,
    )
    suggestions = keep_allowed_suggestions(parsed.suggestions, allowed_tags)
    return {
        "name": parsed.name,
        "suggestions": [suggestion.model_dump() for suggestion in suggestions],
    }
