"""Abstract base class for all LLM provider adapters."""
from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from app.schemas.chat import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Every provider must subclass this and implement `_call_api`.
    The `generate` method wraps the call with timing, timeout handling,
    and error normalisation so orchestration code stays clean.
    """

    # Subclasses must set these
    provider_id: str = ""
    provider_name: str = ""
    model: str = ""
    supports_vision: bool = False

    def __init__(self, api_key: Optional[str], base_url: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("Provider %s has no API key set — requests will fail.", self.provider_id)

    async def generate(
        self,
        prompt: str,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> ProviderResult:
        """
        Public entry point called by the orchestration layer.
        Returns a fully populated ProviderResult regardless of success/failure.
        """
        if not self.api_key:
            return ProviderResult(
                provider=self.provider_id,
                model=self.model,
                status=ProviderStatus.ERROR,
                error="API key not configured. Set the environment variable and restart.",
                supports_vision=self.supports_vision,
            )

        start = time.monotonic()
        try:
            response_text = await self._call_api(prompt, image_b64, image_mime)
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "provider=%s model=%s status=success latency_ms=%d",
                self.provider_id, self.model, latency_ms,
            )
            return ProviderResult(
                provider=self.provider_id,
                model=self.model,
                status=ProviderStatus.SUCCESS,
                response=response_text,
                latency_ms=latency_ms,
                supports_vision=self.supports_vision,
            )

        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.warning("provider=%s status=timeout latency_ms=%d", self.provider_id, latency_ms)
            return ProviderResult(
                provider=self.provider_id,
                model=self.model,
                status=ProviderStatus.TIMEOUT,
                latency_ms=latency_ms,
                error="Request timed out. The provider did not respond in time.",
                supports_vision=self.supports_vision,
            )

        except httpx.HTTPStatusError as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            status = ProviderStatus.RATE_LIMITED if exc.response.status_code == 429 else ProviderStatus.ERROR
            error_msg = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            logger.error("provider=%s status=%s error=%s", self.provider_id, status, error_msg)
            return ProviderResult(
                provider=self.provider_id,
                model=self.model,
                status=status,
                latency_ms=latency_ms,
                error=error_msg,
                supports_vision=self.supports_vision,
            )

        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.error("provider=%s status=error error=%s", self.provider_id, str(exc))
            return ProviderResult(
                provider=self.provider_id,
                model=self.model,
                status=ProviderStatus.ERROR,
                latency_ms=latency_ms,
                error=str(exc),
                supports_vision=self.supports_vision,
            )

    @abstractmethod
    async def _call_api(
        self,
        prompt: str,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> str:
        """
        Subclasses implement this.
        Should raise httpx exceptions normally — base class handles them.
        Must return the model's text response as a plain string.
        """
        ...

    def _build_client(self) -> httpx.AsyncClient:
        """Create a shared async HTTP client with auth and timeout pre-set."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
