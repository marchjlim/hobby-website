import base64
import logging
import os
import time

import httpx
from fastapi import HTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)


def parse_gemini_response(response_data: dict, schema: type[BaseModel]) -> BaseModel:
    output_text = next(
        part["text"]
        for part in response_data["candidates"][0]["content"]["parts"]
        if "text" in part and not part.get("thought")
    )
    return schema.model_validate_json(output_text)


def request_gemini(
    prompt: str,
    schema: type[BaseModel],
    content: bytes | None = None,
    content_type: str | None = None,
    attempts: int = 1,
) -> BaseModel:
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="AI listing generation is not configured")

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    for attempt in range(attempts):
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
            return parse_gemini_response(response.json(), schema)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.error("Gemini returned HTTP %s: %s", status, exc.response.text)
            if status == 503 and attempt < attempts - 1:
                delay = 0.5 * 2 ** attempt
                logger.warning("Gemini overloaded; retrying in %.1f seconds", delay)
                time.sleep(delay)
                continue
            raise HTTPException(
                status_code=status if status in {429, 503} else 502,
                detail=f"Gemini returned HTTP {status}",
            ) from exc
        except httpx.RequestError as exc:
            if attempt < attempts - 1:
                delay = 0.5 * 2 ** attempt
                logger.warning("Unable to reach Gemini; retrying in %.1f seconds", delay)
                time.sleep(delay)
                continue
            logger.exception("Unable to reach Gemini")
            raise HTTPException(status_code=502, detail="Unable to reach Gemini") from exc
        except (KeyError, StopIteration, ValueError) as exc:
            logger.exception("Unable to parse Gemini response")
            raise HTTPException(status_code=502, detail="Invalid response from Gemini") from exc

    raise HTTPException(status_code=503, detail="Gemini is temporarily overloaded")
