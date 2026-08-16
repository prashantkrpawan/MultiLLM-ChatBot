"""
API routes for the chat feature.

POST /api/chat                           — run all providers concurrently
POST /api/chat/regenerate/{provider_id}  — re-run a single provider
GET  /api/health                         — health check
GET  /api/providers                      — list provider metadata
"""
from __future__ import annotations

import base64
import binascii
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ProviderInfo,
    ProvidersResponse,
    RegenerateRequest,
    ProviderResult,
)
from app.services.chat_service import ChatService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _validate_attachment(attachment: Optional[str], mime: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not attachment:
        return None, None

    if not mime or mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported attachment type '{mime}'. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    if attachment.startswith("data:"):
        try:
            _, b64_part = attachment.split(",", 1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid data URI format.")
        attachment = b64_part

    try:
        raw = base64.b64decode(attachment, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid base64 encoding in attachment.")

    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Attachment exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    return attachment, mime


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/providers", response_model=ProvidersResponse, tags=["System"])
async def list_providers() -> ProvidersResponse:
    infos = ChatService.get_provider_info()
    return ProvidersResponse(providers=[ProviderInfo(**p) for p in infos])


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a prompt (and optional image) to all three providers concurrently.
    Always returns HTTP 200; individual provider failures are represented
    inside the results list with an appropriate status field.
    """
    request_id = str(uuid.uuid4())
    logger.info("request_id=%s message_len=%d has_attachment=%s",
                request_id, len(request.message), bool(request.attachment))

    image_b64, image_mime = _validate_attachment(request.attachment, request.attachment_mime)

    results = await ChatService.run_all(
        prompt=request.message,
        image_b64=image_b64,
        image_mime=image_mime,
    )

    return ChatResponse(request_id=request_id, results=results)


@router.post("/chat/regenerate/{provider_id}", response_model=ProviderResult, tags=["Chat"])
async def regenerate(provider_id: str, request: RegenerateRequest) -> ProviderResult:
    """Re-run a single provider (used by the Regenerate button on a model card)."""
    image_b64, image_mime = _validate_attachment(request.attachment, request.attachment_mime)

    result = await ChatService.run_single(
        provider_id=provider_id,
        prompt=request.message,
        image_b64=image_b64,
        image_mime=image_mime,
    )
    return result
