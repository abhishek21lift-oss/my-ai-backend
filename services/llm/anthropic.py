import json
import logging
from typing import Any

from anthropic import AsyncAnthropic, APIStatusError

from core.config import get_settings
from exceptions.app_exceptions import ExternalAPIError
from services.llm.base import BaseLLMService

logger = logging.getLogger(__name__)
_settings = get_settings()


class AnthropicService(BaseLLMService):
    MODEL = "claude-opus-4-8"

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=_settings.ANTHROPIC_API_KEY)

    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        try:
            response = await self._client.messages.create(
                model=self.MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
        except APIStatusError as exc:
            logger.error("Anthropic API error", extra={"ctx_status": exc.status_code})
            raise ExternalAPIError(f"Anthropic API error: {exc.message}") from exc

    async def complete_json(self, system: str, user: str, max_tokens: int = 2048) -> Any:
        """Request JSON output from the model and parse it."""
        json_system = (
            f"{system}\n\n"
            "IMPORTANT: Respond ONLY with valid JSON. No markdown fences, no explanation."
        )
        raw = await self.complete(json_system, user, max_tokens)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ExternalAPIError(f"LLM returned invalid JSON: {exc}") from exc
