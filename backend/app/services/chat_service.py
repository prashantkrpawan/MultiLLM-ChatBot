"""
ChatService — orchestrates concurrent calls to all enabled providers.
Uses asyncio.gather(return_exceptions=True) so one failure never
kills the other two requests.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.config import settings
from app.providers.mistral import MistralProvider
from app.providers.gemini import GeminiProvider
from app.providers.openrouter import OpenRouterProvider
from app.schemas.chat import ProviderResult, ProviderStatus

logger = logging.getLogger(__name__)


def _build_providers():
    """
    Build provider instances from current settings.
    Called lazily on first use so test env vars set before import are honoured.
    """
    return [
        MistralProvider(
            api_key=settings.MISTRAL_API_KEY,
            base_url=settings.MISTRAL_BASE_URL,
            model=settings.MISTRAL_MODEL,
            timeout=settings.LLM_TIMEOUT,
        ),
        GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
            model=settings.GEMINI_MODEL,
            timeout=settings.LLM_TIMEOUT,
        ),
        OpenRouterProvider(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            model=settings.OPENROUTER_MODEL,
            timeout=settings.LLM_TIMEOUT,
        ),
    ]


_PROVIDERS: list | None = None


def _get_providers():
    global _PROVIDERS
    if _PROVIDERS is None:
        _PROVIDERS = _build_providers()
    return _PROVIDERS


class ChatService:
    """
    Orchestrates concurrent AI provider calls.
    """

    @staticmethod
    async def run_all(
        prompt: str,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> list[ProviderResult]:
        """
        Send the same prompt to all providers concurrently.
        Returns a list of ProviderResult — one per provider, regardless of individual success/failure.
        """
        providers = _get_providers()
        logger.info("Starting concurrent requests to %d providers", len(providers))

        tasks = [
            provider.generate(prompt, image_b64, image_mime)
            for provider in providers
        ]

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[ProviderResult] = []
        for provider, result in zip(providers, raw_results):
            if isinstance(result, Exception):
                logger.error("Unhandled exception from provider %s: %s", provider.provider_id, result)
                results.append(ProviderResult(
                    provider=provider.provider_id,
                    model=provider.model,
                    status=ProviderStatus.ERROR,
                    error=str(result),
                    supports_vision=provider.supports_vision,
                ))
            else:
                results.append(result)

        return results

    @staticmethod
    async def run_single(
        provider_id: str,
        prompt: str,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> ProviderResult:
        """
        Re-run a single provider by ID (used for the Regenerate button).
        """
        for provider in _get_providers():
            if provider.provider_id == provider_id:
                return await provider.generate(prompt, image_b64, image_mime)

        return ProviderResult(
            provider=provider_id,
            model="unknown",
            status=ProviderStatus.ERROR,
            error=f"Unknown provider: {provider_id}",
        )

    @staticmethod
    def get_provider_info() -> list[dict]:
        return [
            {
                "id": p.provider_id,
                "name": p.provider_name,
                "model": p.model,
                "enabled": bool(p.api_key),
                "supports_vision": p.supports_vision,
            }
            for p in _get_providers()
        ]
