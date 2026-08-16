"""
OpenRouter provider adapter.
API: OpenAI-compatible chat/completions endpoint.
Free models: append ":free" suffix (e.g., google/gemini-2.5-flash:free).
Sign up at: https://openrouter.ai — email only, no credit card.
Docs: https://openrouter.ai/docs
"""
from __future__ import annotations
from typing import Optional
from app.providers.base import LLMProvider


class OpenRouterProvider(LLMProvider):
    provider_id = "openrouter"
    provider_name = "OpenRouter"
    supports_vision = False

    def __init__(self, api_key: Optional[str], base_url: str, model: str, timeout: int = 30):
        super().__init__(api_key, base_url, timeout)
        self.model = model

    async def _call_api(
        self,
        prompt: str,
        image_b64: Optional[str] = None,
        image_mime: Optional[str] = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": False,
        }

        async with self._build_client() as client:
            resp = await client.post(
                "/chat/completions",
                json=payload,
                # OpenRouter requires these headers to identify your app
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Multi-Model AI Chat",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
