"""Document intake for the cleaning vertical.

The endpoint deliberately creates a *draft* spec. The user still reviews and
confirms it before any company calls are queued.
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, UploadFile, status

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
SUPPORTED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
EXTENSION_MEDIA_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "webp": "image/webp", "pdf": "application/pdf",
}

_SPEC_TEMPLATE: Dict[str, Any] = {
    "property": {"type": "house", "sqft": 0, "bedrooms": 0, "bathrooms": 0, "levels": 1},
    "clean_type": "standard",
    "frequency": "one_time",
    "condition": {"clutter_level": "medium", "has_pets": False, "weeks_since_last_clean": 0},
    "add_ons": {"fridge": False, "oven": False, "windows": False, "baseboards": False, "laundry": False},
    "access": {"parking": "street", "entry_method": "to be confirmed", "walk_up_floor": 0},
    "schedule": {"preferred_date": "", "preferred_time_window": "to be confirmed", "flexibility": None},
    "open_questions": [],
    "confirmed_by_user": False,
    "intake_source": "document",
}

_REQUIRED_PATHS = {
    "property.sqft": "square footage",
    "property.bedrooms": "bedrooms",
    "property.bathrooms": "bathrooms",
    "schedule.preferred_date": "preferred date",
}

_EXTRACTION_PROMPT = """Extract a home-cleaning job specification from the supplied document or image.
Return JSON only. Use this exact shape:
{
  "property":{"type":"apartment|house|condo|townhouse","sqft":number,"bedrooms":number,"bathrooms":number,"levels":number},
  "clean_type":"standard|deep|move_out",
  "frequency":"one_time|weekly|biweekly|monthly",
  "condition":{"clutter_level":"low|medium|high","has_pets":boolean,"weeks_since_last_clean":number},
  "add_ons":{"fridge":boolean,"oven":boolean,"windows":boolean,"baseboards":boolean,"laundry":boolean},
  "access":{"parking":"street|driveway|garage|metered","entry_method":string,"walk_up_floor":number},
  "schedule":{"preferred_date":"YYYY-MM-DD","preferred_time_window":string,"flexibility":string|null},
  "open_questions":[string]
}
Never make up a value. Omit or use null for information the file does not support. Put every missing
or ambiguous field in open_questions. This is a draft which the user will review before any calls."""


def _media_type(upload: UploadFile) -> str:
    declared = (upload.content_type or "").split(";", 1)[0].lower().strip()
    if declared in SUPPORTED_MEDIA_TYPES:
        return declared
    extension = (upload.filename or "").rsplit(".", 1)[-1].lower()
    if extension in EXTENSION_MEDIA_TYPES:
        return EXTENSION_MEDIA_TYPES[extension]
    raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a PDF, JPG, PNG, or WEBP file.")


def _merge_spec(extracted: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    # JSON round-trip provides a small, dependency-free deep copy.
    spec = json.loads(json.dumps(_SPEC_TEMPLATE))
    for group in ("property", "condition", "add_ons", "access", "schedule"):
        if isinstance(extracted.get(group), dict):
            for key, value in extracted[group].items():
                if key in spec[group] and value is not None:
                    spec[group][key] = value
    for key in ("clean_type", "frequency"):
        if extracted.get(key) is not None:
            spec[key] = extracted[key]
    questions = extracted.get("open_questions") if isinstance(extracted.get("open_questions"), list) else []
    missing: List[str] = []
    for path, label in _REQUIRED_PATHS.items():
        parent, key = path.split(".")
        value = spec[parent][key]
        if value in (None, "", 0):
            missing.append(label)
    spec["open_questions"] = list(dict.fromkeys([str(q) for q in questions] + missing))
    return spec, missing


async def extract_document_spec(file: UploadFile) -> Tuple[Dict[str, Any], List[str]]:
    media_type = _media_type(file)
    raw = await file.read()
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The upload was empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "The upload exceeds 20 MB.")
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "OPENAI_API_KEY is not configured for document intake.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Install backend requirements before using document intake.") from exc

    encoded = base64.b64encode(raw).decode("utf-8")
    if media_type == "application/pdf":
        content = [{"type": "text", "text": _EXTRACTION_PROMPT}, {"type": "file", "file": {"filename": file.filename or "upload.pdf", "file_data": f"data:{media_type};base64,{encoded}"}}]
    else:
        content = [{"type": "text", "text": _EXTRACTION_PROMPT}, {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{encoded}"}}]
    try:
        response = OpenAI().chat.completions.create(
            model=os.environ.get("INTAKE_MODEL", "gpt-4o"),
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": content}],
        )
        extracted = json.loads(response.choices[0].message.content or "{}")
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Vision extraction failed: {exc}") from exc
    if not isinstance(extracted, dict):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Vision extraction did not return an object.")
    return _merge_spec(extracted)
