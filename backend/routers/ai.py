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

MAX_PREDICTION_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_PREDICTION_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_TAG_SUGGESTIONS = 5

class SuggestedTag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: str
    confidence: float = Field(ge=0, le=1)


class TagSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestions: list[SuggestedTag] = Field(max_length=MAX_TAG_SUGGESTIONS)


def build_prompt(allowed_tags: list[str]) -> str:
    RULES = [
        "- Grade tags such as HG, RG, MG, or PG refer to the product grade printed on the box. Select at most one grade.",
        "- 'Clear Color' applies only when the product or packaging explicitly indicates a transparent/clear-color edition.",
        "- 'Gundam Base Limited' applies only when the packaging indicates it.",
        "- 'Event limited' applies when the box contains 'Limited Item'",
        "- 'P-bandai' usually applies when the box is greyscale and has no 'Limited item'",
        "- 'Standard Release' uaully applies when the item is not event limited, nor p-bandai, nor gundam base limited."
    ]
    instructions = (
        f"Suggest up to {MAX_TAG_SUGGESTIONS} tags for this Gundam box image. "
        "Use only exact tags from this allowed list: "
        + json.dumps(allowed_tags)
    )
    constraints = "\n".join(RULES)

    prompt = instructions + "\n\nRules:\n" + constraints
    
    return prompt

def parse_gemini_tag_suggestions(response_data: dict) -> TagSuggestions:
    output_text = next(
        part["text"]
        for part in response_data["candidates"][0]["content"]["parts"]
        if "text" in part and not part.get("thought")
    )
    return TagSuggestions.model_validate_json(output_text)


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
            curr_confidence = kept.get(tag, -1)
            if tag not in kept or confidence > curr_confidence:
                # add if tag is not yet added or confidences exceeds curr confidence
                kept[tag] = suggestion.model_copy(update={"tag": tag})
    
    return sorted(kept.values(), key=lambda item: item.confidence, reverse=True)[:MAX_TAG_SUGGESTIONS]


@router.post("/suggest-listing-tags")
def suggest_listing_tags(
    image: UploadFile = File(),
    _: Client = Depends(require_admin),
):
    if image.content_type not in ALLOWED_PREDICTION_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Use a JPEG, PNG, WebP, or GIF image")

    content = image.file.read(MAX_PREDICTION_IMAGE_BYTES + 1)
    if len(content) > MAX_PREDICTION_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller")

    tags_response = supabase.table("ListingTag").select("name").execute()
    allowed_tags = [row["name"] for row in tags_response.data]
    if not allowed_tags:
        return {"suggestions": []}

    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="Tag prediction is not configured")

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
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
                                "mime_type": image.content_type,
                                "data": base64.b64encode(content).decode("ascii"),
                            }
                        },
                        {
                            "text": build_prompt(allowed_tags),
                        },
                    ],
                }],
                "generationConfig": {
                    "responseFormat": {
                        "text": {
                            "mimeType": "APPLICATION_JSON",
                            "schema": TagSuggestions.model_json_schema(),
                        }
                    }
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        parsed = parse_gemini_tag_suggestions(response.json())
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gemini returned HTTP %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Gemini returned HTTP {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        logger.exception("Unable to reach Gemini")
        raise HTTPException(status_code=502, detail="Unable to reach Gemini") from exc
    except (KeyError, StopIteration, ValueError) as exc:
        logger.exception("Unable to parse Gemini response")
        raise HTTPException(status_code=502, detail="Invalid response from Gemini") from exc

    suggestions = keep_allowed_suggestions(parsed.suggestions, allowed_tags)
    return {"suggestions": [suggestion.model_dump() for suggestion in suggestions]}
