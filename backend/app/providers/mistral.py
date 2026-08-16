"""
Mistral AI provider adapter.
API: OpenAI-compatible chat/completions endpoint.
Model: mistral-small-latest (text only; Mistral's vision models are paid-tier).
Free tier: rate-limited on the free plan at console.mistral.ai — no credit card needed.
"""
from __future__ import annotations
from typing import Optional
from app.providers.base import LLMProvider


class MistralProvider(LLMProvider):
    provider_id = "mistral"
    provider_name = "Mistral AI"
    supports_vision = False  # Free-tier models are text-only

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
