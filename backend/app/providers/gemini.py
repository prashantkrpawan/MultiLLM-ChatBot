"""
Google Gemini provider adapter via the OpenAI-compatible endpoint.
API: https://generativelanguage.googleapis.com/v1beta/openai/
Free tier: Very generous — gemini-2.0-flash gets 1500 req/day, 1M tokens/min for free.
Sign up at: https://aistudio.google.com — Google account, no credit card.
Get API key: https://aistudio.google.com/apikey
"""
from __future__ import annotations
from typing import Optional
from app.providers.base import LLMProvider


class GeminiProvider(LLMProvider):
    provider_id = "gemini"
    provider_name = "Google Gemini"
    supports_vision = False  # Vision possible but kept simple for MVP

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
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
