import logging
import traceback
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from agents.context import AgentContext
from agents.fitness_scientist.agent import FitnessScientistAgent
from agents.hook_generator.agent import HookGeneratorAgent
from agents.orchestrator.schemas import PipelineRequest, PipelineResult, PipelineStageResult
from agents.script_writer.agent import ScriptWriterAgent
from agents.trend_detector.agent import TrendDetectorAgent
from agents.viral_scout.agent import ViralScoutAgent
from models.db import AgentStatusEnum
from repositories.agent_logs import AgentLogsRepository
from services.llm.anthropic import AnthropicService

logger = logging.getLogger(__name__)


async def run_content_pipeline(
    request: PipelineRequest,
    session: AsyncSession,
    redis: aioredis.Redis,
    orchestrator_log_id: Optional[UUID] = None,
) -> PipelineResult:
    """
    Runs the full 5-agent content pipeline:
      ViralScout → TrendDetector → FitnessScientist → HookGenerator → ScriptWriter

    Each stage logs independently. The orchestrator log ties them together via
    parent_log_id. Returns a PipelineResult with all created entity IDs.
    """
    logs_repo = AgentLogsRepository(session)
    llm = AnthropicService()

    # Create or reuse orchestrator-level log entry
    if orchestrator_log_id is None:
        orch_log = await logs_repo.create(
            user_id=request.user_id,
            agent_name="orchestrator",
            task_type="content_pipeline",
            status=AgentStatusEnum.pending,
        )
        await session.commit()
        await logs_repo.mark_running(orch_log.id)
        await session.commit()
        orchestrator_log_id = orch_log.id
    else:
        orch_log = await logs_repo.get_by_id(orchestrator_log_id)

    logger.info(
        "Pipeline started",
        extra={
            "ctx_orchestrator_log_id": str(orchestrator_log_id),
            "ctx_user_id": str(request.user_id),
            "ctx_topic_id": str(request.topic_id),
            "ctx_platform": request.platform.value,
        },
    )

    result = PipelineResult(success=False, orchestrator_log_id=orchestrator_log_id)

    def make_ctx(**extra) -> AgentContext:
        return AgentContext(
            user_id=request.user_id,
            topic_id=request.topic_id,
            platform=request.platform.value,
            session=session,
            redis=redis,
            parent_log_id=orchestrator_log_id,
            extra=extra,
        )

    try:
        # ── Stage 1: Viral Scout ──────────────────────────────────────────────
        logger.info("Stage 1: Viral Scout")
        scout_result = await ViralScoutAgent(llm).run(make_ctx())
        viral_ids = scout_result.output.get("viral_content_ids", [])
        result.viral_content_ids = viral_ids
        result.stages.append(PipelineStageResult(
            stage="viral_scout",
            success=True,
            log_id=scout_result.log_id,
            output=scout_result.output,
            input_tokens=scout_result.input_tokens,
            output_tokens=scout_result.output_tokens,
            duration_ms=scout_result.duration_ms,
        ))
        result.total_input_tokens += scout_result.input_tokens
        result.total_output_tokens += scout_result.output_tokens
        result.total_duration_ms += scout_result.duration_ms

        # ── Stage 2: Trend Detector ───────────────────────────────────────────
        logger.info("Stage 2: Trend Detector")
        trend_result = await TrendDetectorAgent(llm).run(
            make_ctx(viral_content_ids=viral_ids)
        )
        trend_id = trend_result.output.get("trend_id")
        result.trend_id = trend_id
        result.stages.append(PipelineStageResult(
            stage="trend_detector",
            success=True,
            log_id=trend_result.log_id,
            output=trend_result.output,
            input_tokens=trend_result.input_tokens,
            output_tokens=trend_result.output_tokens,
            duration_ms=trend_result.duration_ms,
        ))
        result.total_input_tokens += trend_result.input_tokens
        result.total_output_tokens += trend_result.output_tokens
        result.total_duration_ms += trend_result.duration_ms

        # ── Stage 3: Fitness Scientist ────────────────────────────────────────
        logger.info("Stage 3: Fitness Scientist")
        fitness_result = await FitnessScientistAgent(llm).run(
            make_ctx(trend_id=trend_id, viral_content_ids=viral_ids)
        )
        report_id = fitness_result.output.get("report_id")
        fitness_score = fitness_result.output.get("fitness_score")
        result.report_id = report_id
        result.stages.append(PipelineStageResult(
            stage="fitness_scientist",
            success=True,
            log_id=fitness_result.log_id,
            output=fitness_result.output,
            input_tokens=fitness_result.input_tokens,
            output_tokens=fitness_result.output_tokens,
            duration_ms=fitness_result.duration_ms,
        ))
        result.total_input_tokens += fitness_result.input_tokens
        result.total_output_tokens += fitness_result.output_tokens
        result.total_duration_ms += fitness_result.duration_ms

        # ── Stage 4: Hook Generator ───────────────────────────────────────────
        logger.info("Stage 4: Hook Generator")
        hook_result = await HookGeneratorAgent(llm).run(
            make_ctx(
                report_id=report_id,
                trend_id=trend_id,
                fitness_score=fitness_score,
            )
        )
        hook_ids = hook_result.output.get("hook_ids", [])
        result.hook_ids = hook_ids
        result.stages.append(PipelineStageResult(
            stage="hook_generator",
            success=True,
            log_id=hook_result.log_id,
            output=hook_result.output,
            input_tokens=hook_result.input_tokens,
            output_tokens=hook_result.output_tokens,
            duration_ms=hook_result.duration_ms,
        ))
        result.total_input_tokens += hook_result.input_tokens
        result.total_output_tokens += hook_result.output_tokens
        result.total_duration_ms += hook_result.duration_ms

        # ── Stage 5: Script Writer ────────────────────────────────────────────
        logger.info("Stage 5: Script Writer")
        script_result = await ScriptWriterAgent(llm).run(
            make_ctx(
                hook_ids=hook_ids,
                trend_id=trend_id,
                report_id=report_id,
                fitness_score=fitness_score,
            )
        )
        script_ids = script_result.output.get("script_ids", [])
        result.script_ids = script_ids
        result.stages.append(PipelineStageResult(
            stage="script_writer",
            success=True,
            log_id=script_result.log_id,
            output=script_result.output,
            input_tokens=script_result.input_tokens,
            output_tokens=script_result.output_tokens,
            duration_ms=script_result.duration_ms,
        ))
        result.total_input_tokens += script_result.input_tokens
        result.total_output_tokens += script_result.output_tokens
        result.total_duration_ms += script_result.duration_ms

        result.success = True
        await logs_repo.mark_completed(
            orchestrator_log_id,
            result.to_dict(),
            result.total_input_tokens,
            result.total_output_tokens,
            result.total_duration_ms,
        )
        await session.commit()

        # Invalidate stale daily recommendations cache for this user
        try:
            from datetime import date
            from core.cache import CacheService
            cache_key = CacheService.key("recs", str(request.user_id), str(date.today()))
            await redis.delete(cache_key)
        except Exception:
            logger.warning("Cache invalidation failed after pipeline completion")

        logger.info(
            "Pipeline completed",
            extra={
                "ctx_orchestrator_log_id": str(orchestrator_log_id),
                "ctx_hooks_created": len(hook_ids),
                "ctx_scripts_created": len(script_ids),
                "ctx_total_tokens": result.total_input_tokens + result.total_output_tokens,
            },
        )
        return result

    except Exception as exc:
        tb = traceback.format_exc()
        result.error = str(exc)
        # Record the failure stage
        failed_stage = _current_stage(result)
        result.stages.append(PipelineStageResult(
            stage=failed_stage,
            success=False,
            log_id=orchestrator_log_id,
            output={},
            input_tokens=0,
            output_tokens=0,
            duration_ms=0,
            error=str(exc),
        ))
        try:
            await logs_repo.mark_failed(orchestrator_log_id, str(exc), tb)
            await session.commit()
        except Exception:
            logger.exception("Could not persist orchestrator failure log")

        logger.error(
            "Pipeline failed",
            extra={
                "ctx_orchestrator_log_id": str(orchestrator_log_id),
                "ctx_failed_stage": failed_stage,
                "ctx_error": str(exc),
            },
        )
        raise


def _current_stage(result: PipelineResult) -> str:
    """Infer which stage just failed based on what succeeded."""
    completed = {s.stage for s in result.stages if s.success}
    pipeline = ["viral_scout", "trend_detector", "fitness_scientist", "hook_generator", "script_writer"]
    for stage in pipeline:
        if stage not in completed:
            return stage
    return "unknown"
