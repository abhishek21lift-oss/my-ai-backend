from datetime import date, datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.db import (
    AgentStatusEnum,
    ContentTypeEnum,
    EntityTypeEnum,
    EventTypeEnum,
    HookTypeEnum,
    PlanEnum,
    PlatformEnum,
    ReportStatusEnum,
    ScriptStatusEnum,
    TrendPeriodEnum,
    TrendVelocityEnum,
)

T = TypeVar("T")

# ── Shared ────────────────────────────────────────────────────────────────────


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int
    has_more: bool


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None


# ── Users ─────────────────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: Optional[str]
    plan: PlanEnum
    is_active: bool
    monthly_token_quota: Optional[int]
    created_at: datetime


# ── API Keys ──────────────────────────────────────────────────────────────────


class APIKeyCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    rate_limit_rpm: int = Field(60, ge=1, le=1000)
    rate_limit_tpd: Optional[int] = Field(None, ge=1)
    expires_at: Optional[datetime] = None


class APIKeyCreatedResponse(BaseModel):
    """Shown exactly once at creation — raw key is never returned again."""
    id: UUID
    key: str
    key_prefix: str
    name: Optional[str]
    rate_limit_rpm: int
    created_at: datetime


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key_prefix: str
    name: Optional[str]
    is_active: bool
    rate_limit_rpm: int
    rate_limit_tpd: Optional[int]
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime


# ── Topics ────────────────────────────────────────────────────────────────────


class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


# ── Viral Content ─────────────────────────────────────────────────────────────


class ViralContentCreate(BaseModel):
    topic_id: Optional[UUID] = None
    platform: PlatformEnum
    content_type: Optional[ContentTypeEnum] = None
    title: str = Field(..., min_length=1)
    content_url: Optional[str] = None
    views: int = Field(0, ge=0)
    likes: int = Field(0, ge=0)
    shares: int = Field(0, ge=0)
    comments: int = Field(0, ge=0)
    engagement_rate: Optional[float] = Field(None, ge=0, le=100)
    viral_score: float = Field(0.0, ge=0, le=100)
    published_at: Optional[datetime] = None


class ViralContentUpdate(BaseModel):
    topic_id: Optional[UUID] = None
    viral_score: Optional[float] = Field(None, ge=0, le=100)
    engagement_rate: Optional[float] = Field(None, ge=0, le=100)
    content_type: Optional[ContentTypeEnum] = None


class ViralContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    topic_id: Optional[UUID]
    platform: PlatformEnum
    content_type: Optional[ContentTypeEnum]
    title: str
    content_url: Optional[str]
    views: int
    likes: int
    shares: int
    comments: int
    engagement_rate: Optional[float]
    viral_score: float
    published_at: Optional[datetime]
    collected_at: datetime
    created_at: datetime


# ── Trends ────────────────────────────────────────────────────────────────────


class TrendAnalysisCreate(BaseModel):
    topic_id: Optional[UUID] = None
    period: TrendPeriodEnum
    keywords: List[str] = []
    data_points: List[dict] = []
    platforms: List[str] = []


class TrendAnalyzeRequest(BaseModel):
    """Ask the AI to analyze a topic and produce trend insights."""
    topic_id: UUID
    period: TrendPeriodEnum = TrendPeriodEnum.weekly
    context: Optional[str] = Field(
        None,
        description="Extra context or data to include in the analysis",
    )


class TrendAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    topic_id: Optional[UUID]
    period: TrendPeriodEnum
    trend_score: float
    velocity: TrendVelocityEnum
    keywords: List[Any]
    insights: Optional[str]
    data_points: List[Any]
    platforms: List[Any]
    analyzed_at: datetime
    created_at: datetime


# ── Research Reports ──────────────────────────────────────────────────────────


class ResearchReportCreate(BaseModel):
    topic_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=500)
    tags: List[str] = []


class ResearchGenerateRequest(BaseModel):
    """Trigger AI generation of a full research report."""
    topic_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    focus_areas: List[str] = Field(
        default=[],
        description="Specific angles to cover in the report",
    )
    tags: List[str] = []


class ResearchReportUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    content: Optional[str] = None
    sources: Optional[List[dict]] = None
    key_findings: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ResearchReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    topic_id: Optional[UUID]
    title: str
    summary: Optional[str]
    content: Optional[str]
    sources: List[Any]
    key_findings: List[Any]
    tags: List[Any]
    status: ReportStatusEnum
    word_count: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


class ResearchJobResponse(BaseModel):
    """Returned when a report is queued for background generation."""
    report_id: UUID
    status: ReportStatusEnum
    message: str


# ── Hooks ─────────────────────────────────────────────────────────────────────


class HookGenerateRequest(BaseModel):
    topic_id: UUID
    platform: PlatformEnum
    hook_types: List[HookTypeEnum] = []
    count: int = Field(5, ge=1, le=20)
    viral_content_id: Optional[UUID] = None
    style_notes: Optional[str] = None


class HookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    topic_id: Optional[UUID]
    viral_content_id: Optional[UUID]
    hook_type: HookTypeEnum
    platform: PlatformEnum
    content: str
    character_count: Optional[int]
    quality_score: Optional[float]
    is_used: bool
    created_at: datetime


class HookListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[HookResponse]
    total: int


# ── Scripts ───────────────────────────────────────────────────────────────────


class ScriptGenerateRequest(BaseModel):
    topic_id: UUID
    hook_id: Optional[UUID] = None
    platform: PlatformEnum
    title: str = Field(..., min_length=1, max_length=500)
    duration_seconds: Optional[int] = Field(None, gt=0)
    tone: Optional[str] = Field(None, description="e.g. 'educational', 'entertaining', 'inspirational'")
    outline_notes: Optional[str] = None


class ScriptUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    outline: Optional[List[dict]] = None


class ScriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    topic_id: Optional[UUID]
    hook_id: Optional[UUID]
    title: str
    platform: PlatformEnum
    duration_seconds: Optional[int]
    content: str
    outline: List[Any]
    word_count: Optional[int]
    status: ScriptStatusEnum
    created_at: datetime
    updated_at: Optional[datetime]


# ── Daily Recommendations ─────────────────────────────────────────────────────


class RecommendationItem(BaseModel):
    type: str  # hook | script | trend | report | viral_content
    id: UUID
    title: str
    description: str
    priority: int = Field(..., ge=1, le=10)
    action: str
    metadata: dict = {}


class DailyRecommendationsResponse(BaseModel):
    report_date: date
    user_id: UUID
    items: List[RecommendationItem]
    summary: str
    top_platforms: List[str]
    top_trending_topics: List[str]
    tokens_quota_remaining: Optional[int]
    generated_at: datetime


# ── Agent Logs ────────────────────────────────────────────────────────────────


class AgentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID]
    agent_name: str
    task_type: str
    status: AgentStatusEnum
    input_tokens: int
    output_tokens: int
    duration_ms: Optional[int]
    retry_count: int
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


# ── Agent Pipeline ────────────────────────────────────────────────────────────


class AgentRunRequest(BaseModel):
    topic_id: UUID
    platform: PlatformEnum


class AgentRunResponse(BaseModel):
    orchestrator_log_id: UUID
    status: AgentStatusEnum
    message: str
    job_id: Optional[str] = None
    result: Optional[dict] = None
    stages: Optional[List[dict]] = None


# ── Chat (kept for backward-compat) ──────────────────────────────────────────


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "claude-opus-4-8"
    max_tokens: int = Field(default=1024, gt=0, le=8096)
    system: Optional[str] = None


class UsageStats(BaseModel):
    input_tokens: int
    output_tokens: int


class ChatResponse(BaseModel):
    content: str
    model: str
    usage: Optional[UsageStats] = None
