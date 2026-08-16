"""
Unit tests for provider adapters using mocked httpx responses.
Run: cd backend && python -m pytest tests/ -v
"""
from __future__ import annotations

import pytest
import httpx
import respx

from app.providers.mistral import MistralProvider
from app.providers.gemini import GeminiProvider
from app.providers.openrouter import OpenRouterProvider
from app.schemas.chat import ProviderStatus


FAKE_COMPLETION = {
    "choices": [{"message": {"content": "Mocked response text."}}]
}


@pytest.mark.asyncio
class TestMistralProvider:
    def _make(self):
        return MistralProvider(
            api_key="fake-key",
            base_url="https://api.mistral.ai/v1",
            model="mistral-small-latest",
            timeout=5,
        )

    @respx.mock
    async def test_success(self):
        respx.post("https://api.mistral.ai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=FAKE_COMPLETION)
        )
        result = await self._make().generate("Hello")
        assert result.status == ProviderStatus.SUCCESS
        assert result.response == "Mocked response text."

    @respx.mock
    async def test_rate_limit(self):
        respx.post("https://api.mistral.ai/v1/chat/completions").mock(
            return_value=httpx.Response(429, json={"error": "rate limit"})
        )
        result = await self._make().generate("Hello")
        assert result.status == ProviderStatus.RATE_LIMITED

    @respx.mock
    async def test_timeout(self):
        respx.post("https://api.mistral.ai/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await self._make().generate("Hello")
        assert result.status == ProviderStatus.TIMEOUT

    async def test_missing_api_key(self):
        provider = MistralProvider(api_key=None, base_url="https://api.mistral.ai/v1", model="mistral-small-latest")
        result = await provider.generate("Hello")
        assert result.status == ProviderStatus.ERROR
        assert "API key" in result.error


@pytest.mark.asyncio
class TestGeminiProvider:
    def _make(self):
        return GeminiProvider(
            api_key="fake-key",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model="gemini-2.0-flash",
            timeout=5,
        )

    @respx.mock
    async def test_success(self):
        respx.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions").mock(
            return_value=httpx.Response(200, json=FAKE_COMPLETION)
        )
        result = await self._make().generate("What is AI?")
        assert result.status == ProviderStatus.SUCCESS
        assert result.provider == "gemini"

    @respx.mock
    async def test_rate_limit(self):
        respx.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions").mock(
            return_value=httpx.Response(429, json={"error": "rate limit"})
        )
        result = await self._make().generate("Hello")
        assert result.status == ProviderStatus.RATE_LIMITED

    @respx.mock
    async def test_server_error(self):
        respx.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions").mock(
            return_value=httpx.Response(500, json={"error": "Internal error"})
        )
        result = await self._make().generate("Hello")
        assert result.status == ProviderStatus.ERROR


@pytest.mark.asyncio
class TestOpenRouterProvider:
    def _make(self):
        return OpenRouterProvider(
            api_key="fake-key",
            base_url="https://openrouter.ai/api/v1",
            model="google/gemini-2.5-flash:free",
            timeout=5,
        )

    @respx.mock
    async def test_success(self):
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=FAKE_COMPLETION)
        )
        result = await self._make().generate("Tell me a joke")
        assert result.status == ProviderStatus.SUCCESS
        assert result.provider == "openrouter"

    @respx.mock
    async def test_timeout(self):
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await self._make().generate("Hello")
        assert result.status == ProviderStatus.TIMEOUT
