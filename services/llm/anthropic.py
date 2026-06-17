import asyncio
import json
import logging
from typing import Any

from anthropic import AsyncAnthropic, APIStatusError, InternalServerError, RateLimitError

from core.config import get_settings
from exceptions.app_exceptions import ExternalAPIError
from services.llm.base import BaseLLMService

logger = logging.getLogger(__name__)
_settings = get_settings()

_MAX_RETRIES = 4
_RETRY_BASE_SECONDS = 2.0


class AnthropicService(BaseLLMService):
    MODEL = "claude-opus-4-8"

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=_settings.ANTHROPIC_API_KEY)

    async def complete_one_turn(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 4096,
    ) -> Any:
        """Single ReAct step with tool_use support and exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return await self._client.messages.create(
                    model=self.MODEL,
                    system=system,
                    messages=messages,
                    tools=tools,
                    max_tokens=max_tokens,
                )
            except (RateLimitError, InternalServerError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    wait = _RETRY_BASE_SECONDS * (2 ** attempt)
                    logger.warning(
                        "Anthropic transient error — retrying",
                        extra={"ctx_attempt": attempt + 1, "ctx_wait_s": wait, "ctx_error": str(exc)},
                    )
                    await asyncio.sleep(wait)
            except APIStatusError as exc:
                logger.error("Anthropic API error in agent turn", extra={"ctx_status": exc.status_code})
                raise ExternalAPIError(f"Anthropic API error: {exc.message}") from exc
        raise ExternalAPIError(
            f"Anthropic API unavailable after {_MAX_RETRIES} retries: {last_exc}"
        ) from last_exc

    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await self._client.messages.create(
                    model=self.MODEL,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return response.content[0].text
            except (RateLimitError, InternalServerError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    wait = _RETRY_BASE_SECONDS * (2 ** attempt)
                    logger.warning(
                        "Anthropic transient error — retrying",
                        extra={"ctx_attempt": attempt + 1, "ctx_wait_s": wait},
                    )
                    await asyncio.sleep(wait)
            except APIStatusError as exc:
                logger.error("Anthropic API error", extra={"ctx_status": exc.status_code})
                raise ExternalAPIError(f"Anthropic API error: {exc.message}") from exc
        raise ExternalAPIError(
            f"Anthropic API unavailable after {_MAX_RETRIES} retries: {last_exc}"
        ) from last_exc

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
