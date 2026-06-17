from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from models.db import PlatformEnum


@dataclass
class PipelineRequest:
    user_id: UUID
    topic_id: UUID
    platform: PlatformEnum


@dataclass
class PipelineStageResult:
    stage: str
    success: bool
    log_id: UUID
    output: dict
    input_tokens: int
    output_tokens: int
    duration_ms: int
    error: Optional[str] = None


@dataclass
class PipelineResult:
    success: bool
    orchestrator_log_id: UUID
    stages: list[PipelineStageResult] = field(default_factory=list)

    # Collected entity IDs from each stage
    viral_content_ids: list[str] = field(default_factory=list)
    trend_id: Optional[str] = None
    report_id: Optional[str] = None
    hook_ids: list[str] = field(default_factory=list)
    script_ids: list[str] = field(default_factory=list)

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "orchestrator_log_id": str(self.orchestrator_log_id),
            "viral_content_ids": self.viral_content_ids,
            "trend_id": self.trend_id,
            "report_id": self.report_id,
            "hook_ids": self.hook_ids,
            "script_ids": self.script_ids,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
        }
