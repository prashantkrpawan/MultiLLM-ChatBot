"""Pydantic schemas for all API request/response models."""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNSUPPORTED = "unsupported"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32_000, description="User prompt text")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for future context threading")
    attachment: Optional[str] = Field(None, description="Base64-encoded image attachment (optional)")
    attachment_mime: Optional[str] = Field(None, description="MIME type of the attachment e.g. image/jpeg")


class RegenerateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32_000)
    attachment: Optional[str] = None
    attachment_mime: Optional[str] = None


class ProviderResult(BaseModel):
    provider: str
    model: str
    status: ProviderStatus
    response: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    supports_vision: bool = False


class ChatResponse(BaseModel):
    request_id: str
    results: list[ProviderResult]


class HealthResponse(BaseModel):
    status: str = "ok"


class ProviderInfo(BaseModel):
    id: str
    name: str
    model: str
    enabled: bool
    supports_vision: bool


class ProvidersResponse(BaseModel):
    providers: list[ProviderInfo]
