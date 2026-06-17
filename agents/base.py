import json
import logging
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from agents.context import AgentContext, AgentResult
from exceptions.app_exceptions import ExternalAPIError
from models.db import AgentStatusEnum
from repositories.agent_logs import AgentLogsRepository
from services.llm.anthropic import AnthropicService


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict        # JSON Schema {"type":"object","properties":{...},"required":[...]}
    fn: Callable[..., Awaitable[Any]]   # async(**tool_input) -> JSON-serialisable


class AgentError(Exception):
    pass


def _parse_final_answer(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"raw_output": text}


class BaseAgent(ABC):
    AGENT_NAME: str
    TASK_TYPE: str
    MAX_TURNS: int = 10
    MAX_TOKENS: int = 4096

    def __init__(self, llm: AnthropicService) -> None:
        self.llm = llm
        self._logger = logging.getLogger(f"agents.{self.__class__.AGENT_NAME}")

    @abstractmethod
    def get_system_prompt(self, ctx: AgentContext) -> str: ...

    @abstractmethod
    def get_initial_message(self, ctx: AgentContext) -> str: ...

    @abstractmethod
    def get_tools(self, ctx: AgentContext) -> list[ToolDef]: ...

    async def run(self, ctx: AgentContext) -> AgentResult:
        logs_repo = AgentLogsRepository(ctx.session)
        log = await logs_repo.create(
            user_id=ctx.user_id,
            parent_log_id=ctx.parent_log_id,
            agent_name=self.AGENT_NAME,
            task_type=self.TASK_TYPE,
            status=AgentStatusEnum.pending,
        )
        await ctx.session.commit()

        await logs_repo.mark_running(log.id)
        await ctx.session.commit()

        start_ms = int(time.time() * 1000)
        self._logger.info(
            f"{self.AGENT_NAME} started",
            extra={"ctx_log_id": str(log.id), "ctx_topic_id": str(ctx.topic_id)},
        )

        try:
            output, in_tok, out_tok = await self._react_loop(ctx)
            duration_ms = int(time.time() * 1000) - start_ms

            await logs_repo.mark_completed(log.id, output, in_tok, out_tok, duration_ms)
            await ctx.session.commit()

            self._logger.info(
                f"{self.AGENT_NAME} completed",
                extra={
                    "ctx_log_id": str(log.id),
                    "ctx_tokens_in": in_tok,
                    "ctx_tokens_out": out_tok,
                    "ctx_duration_ms": duration_ms,
                },
            )
            return AgentResult(
                output=output,
                input_tokens=in_tok,
                output_tokens=out_tok,
                duration_ms=duration_ms,
                log_id=log.id,
            )
        except Exception as exc:
            duration_ms = int(time.time() * 1000) - start_ms
            tb = traceback.format_exc()
            try:
                await ctx.session.rollback()
                await logs_repo.mark_failed(log.id, str(exc), tb)
                await ctx.session.commit()
            except Exception:
                self._logger.exception("Failed to persist agent failure log")

            self._logger.error(
                f"{self.AGENT_NAME} failed",
                extra={"ctx_log_id": str(log.id), "ctx_error": str(exc)},
            )
            raise

    async def _react_loop(
        self, ctx: AgentContext
    ) -> tuple[dict[str, Any], int, int]:
        system = self.get_system_prompt(ctx)
        tools = self.get_tools(ctx)
        api_tools = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in tools
        ]
        tool_map = {t.name: t for t in tools}

        messages: list[dict] = [{"role": "user", "content": self.get_initial_message(ctx)}]
        total_in, total_out = 0, 0

        for turn in range(self.MAX_TURNS):
            self._logger.debug(f"ReAct turn {turn + 1}/{self.MAX_TURNS}")

            response = await self.llm.complete_one_turn(
                system=system,
                messages=messages,
                tools=api_tools,
                max_tokens=self.MAX_TOKENS,
            )
            total_in += response.usage.input_tokens
            total_out += response.usage.output_tokens

            # Append the typed content blocks directly — the SDK serialises them
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "max_tokens":
                raise AgentError(
                    f"{self.AGENT_NAME}: model hit max_tokens on turn {turn + 1}"
                )

            if response.stop_reason == "end_turn":
                text_block = next(
                    (b for b in response.content if b.type == "text"), None
                )
                if text_block is None:
                    raise AgentError(
                        f"{self.AGENT_NAME}: end_turn with no text block"
                    )
                return _parse_final_answer(text_block.text), total_in, total_out

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    tool_def = tool_map.get(block.name)
                    if tool_def is None:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "is_error": True,
                            "content": f"Unknown tool '{block.name}'. Available: {list(tool_map)}",
                        })
                        continue
                    try:
                        result = await tool_def.fn(**block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, default=str),
                        })
                        # Commit any DB writes from this tool before the next turn
                        await ctx.session.commit()
                        self._logger.debug(
                            "Tool executed",
                            extra={"ctx_tool": block.name},
                        )
                    except Exception as exc:
                        self._logger.warning(
                            "Tool execution error",
                            extra={"ctx_tool": block.name, "ctx_error": str(exc)},
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "is_error": True,
                            "content": f"Tool error: {exc}",
                        })
                messages.append({"role": "user", "content": tool_results})
                continue

            raise AgentError(
                f"{self.AGENT_NAME}: unexpected stop_reason='{response.stop_reason}'"
            )

        raise AgentError(
            f"{self.AGENT_NAME}: ReAct loop exceeded MAX_TURNS={self.MAX_TURNS}"
        )
