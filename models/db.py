import enum
import uuid
from datetime import date, datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Enums ─────────────────────────────────────────────────────────────────────

class PlanEnum(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class PlatformEnum(str, enum.Enum):
    youtube = "youtube"
    tiktok = "tiktok"
    instagram = "instagram"
    twitter = "twitter"
    linkedin = "linkedin"
    reddit = "reddit"
    other = "other"


class ContentTypeEnum(str, enum.Enum):
    video = "video"
    post = "post"
    article = "article"
    thread = "thread"
    reel = "reel"
    short = "short"


class TrendPeriodEnum(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class TrendVelocityEnum(str, enum.Enum):
    rising = "rising"
    falling = "falling"
    stable = "stable"
    viral = "viral"


class ReportStatusEnum(str, enum.Enum):
    draft = "draft"
    processing = "processing"
    completed = "completed"
    archived = "archived"


class HookTypeEnum(str, enum.Enum):
    question = "question"
    statement = "statement"
    statistic = "statistic"
    story = "story"
    controversy = "controversy"
    list_ = "list"
    challenge = "challenge"


class ScriptStatusEnum(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    published = "published"
    archived = "archived"


class AgentStatusEnum(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class EntityTypeEnum(str, enum.Enum):
    topic = "topic"
    viral_content = "viral_content"
    trend_analysis = "trend_analysis"
    research_report = "research_report"
    hook = "hook"
    script = "script"
    daily_report = "daily_report"


class EventTypeEnum(str, enum.Enum):
    view = "view"
    create = "create"
    update = "update"
    delete = "delete"
    export = "export"
    copy = "copy"
    share = "share"
    generate = "generate"
    approve = "approve"
    publish = "publish"


# ── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_is_active", "is_active"),
        Index("idx_users_plan", "plan"),
        Index("idx_users_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    plan: Mapped[PlanEnum] = mapped_column(
        sa.Enum(PlanEnum, name="plan_enum"), nullable=False, default=PlanEnum.free
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    monthly_token_quota: Mapped[Optional[int]] = mapped_column(BigInteger)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="user", cascade="all, delete-orphan"
    )
    viral_content: Mapped[List["ViralContent"]] = relationship(
        "ViralContent", back_populates="user", cascade="all, delete-orphan"
    )
    trend_analyses: Mapped[List["TrendAnalysis"]] = relationship(
        "TrendAnalysis", back_populates="user", cascade="all, delete-orphan"
    )
    research_reports: Mapped[List["ResearchReport"]] = relationship(
        "ResearchReport", back_populates="user", cascade="all, delete-orphan"
    )
    hooks: Mapped[List["Hook"]] = relationship(
        "Hook", back_populates="user", cascade="all, delete-orphan"
    )
    scripts: Mapped[List["Script"]] = relationship(
        "Script", back_populates="user", cascade="all, delete-orphan"
    )
    daily_reports: Mapped[List["DailyReport"]] = relationship(
        "DailyReport", back_populates="user", cascade="all, delete-orphan"
    )
    agent_logs: Mapped[List["AgentLog"]] = relationship(
        "AgentLog", back_populates="user"
    )
    analytics: Mapped[List["Analytics"]] = relationship(
        "Analytics", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
        Index("idx_api_keys_key_prefix", "key_prefix"),
        Index("idx_api_keys_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    rate_limit_tpd: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="api_keys")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_topics_user_name"),
        Index("idx_topics_user_id", "user_id"),
        Index("idx_topics_is_active", "is_active"),
        Index("idx_topics_category", "category"),
        Index("idx_topics_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="topics")
    viral_content: Mapped[List["ViralContent"]] = relationship(
        "ViralContent", back_populates="topic"
    )
    trend_analyses: Mapped[List["TrendAnalysis"]] = relationship(
        "TrendAnalysis", back_populates="topic"
    )
    research_reports: Mapped[List["ResearchReport"]] = relationship(
        "ResearchReport", back_populates="topic"
    )
    hooks: Mapped[List["Hook"]] = relationship("Hook", back_populates="topic")
    scripts: Mapped[List["Script"]] = relationship("Script", back_populates="topic")


class ViralContent(Base):
    __tablename__ = "viral_content"
    __table_args__ = (
        CheckConstraint(
            "viral_score >= 0 AND viral_score <= 100",
            name="ck_viral_content_viral_score",
        ),
        CheckConstraint("views >= 0", name="ck_viral_content_views"),
        CheckConstraint("likes >= 0", name="ck_viral_content_likes"),
        CheckConstraint("shares >= 0", name="ck_viral_content_shares"),
        CheckConstraint("comments >= 0", name="ck_viral_content_comments"),
        Index("idx_viral_content_user_id", "user_id"),
        Index("idx_viral_content_topic_id", "topic_id"),
        Index("idx_viral_content_platform", "platform"),
        Index("idx_viral_content_viral_score", "viral_score"),
        Index("idx_viral_content_collected_at", "collected_at"),
        Index("idx_viral_content_published_at", "published_at"),
        Index("idx_viral_content_user_platform", "user_id", "platform"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL")
    )
    platform: Mapped[PlatformEnum] = mapped_column(
        sa.Enum(PlatformEnum, name="platform_enum"), nullable=False
    )
    content_type: Mapped[Optional[ContentTypeEnum]] = mapped_column(
        sa.Enum(ContentTypeEnum, name="content_type_enum")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(Text)
    views: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float)
    viral_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="viral_content")
    topic: Mapped[Optional["Topic"]] = relationship(
        "Topic", back_populates="viral_content"
    )
    hooks: Mapped[List["Hook"]] = relationship("Hook", back_populates="viral_content")


class TrendAnalysis(Base):
    __tablename__ = "trend_analysis"
    __table_args__ = (
        CheckConstraint(
            "trend_score >= 0 AND trend_score <= 100",
            name="ck_trend_analysis_trend_score",
        ),
        Index("idx_trend_analysis_user_id", "user_id"),
        Index("idx_trend_analysis_topic_id", "topic_id"),
        Index("idx_trend_analysis_period", "period"),
        Index("idx_trend_analysis_velocity", "velocity"),
        Index("idx_trend_analysis_trend_score", "trend_score"),
        Index("idx_trend_analysis_analyzed_at", "analyzed_at"),
        Index("idx_trend_analysis_user_period", "user_id", "period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL")
    )
    period: Mapped[TrendPeriodEnum] = mapped_column(
        sa.Enum(TrendPeriodEnum, name="trend_period_enum"), nullable=False
    )
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    velocity: Mapped[TrendVelocityEnum] = mapped_column(
        sa.Enum(TrendVelocityEnum, name="trend_velocity_enum"),
        nullable=False,
        default=TrendVelocityEnum.stable,
    )
    keywords: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    insights: Mapped[Optional[str]] = mapped_column(Text)
    data_points: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    platforms: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trend_analyses")
    topic: Mapped[Optional["Topic"]] = relationship(
        "Topic", back_populates="trend_analyses"
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"
    __table_args__ = (
        Index("idx_research_reports_user_id", "user_id"),
        Index("idx_research_reports_topic_id", "topic_id"),
        Index("idx_research_reports_status", "status"),
        Index("idx_research_reports_created_at", "created_at"),
        Index(
            "idx_research_reports_active",
            "user_id",
            postgresql_where=text("status != 'archived'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    sources: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    key_findings: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    tags: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    status: Mapped[ReportStatusEnum] = mapped_column(
        sa.Enum(ReportStatusEnum, name="report_status_enum"),
        nullable=False,
        default=ReportStatusEnum.draft,
    )
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="research_reports")
    topic: Mapped[Optional["Topic"]] = relationship(
        "Topic", back_populates="research_reports"
    )


class Hook(Base):
    __tablename__ = "hooks"
    __table_args__ = (
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100",
            name="ck_hooks_quality_score",
        ),
        Index("idx_hooks_user_id", "user_id"),
        Index("idx_hooks_topic_id", "topic_id"),
        Index("idx_hooks_viral_content_id", "viral_content_id"),
        Index("idx_hooks_platform", "platform"),
        Index("idx_hooks_hook_type", "hook_type"),
        Index("idx_hooks_quality_score", "quality_score"),
        Index("idx_hooks_is_used", "is_used"),
        Index("idx_hooks_created_at", "created_at"),
        Index(
            "idx_hooks_unused",
            "user_id",
            "platform",
            postgresql_where=text("is_used = false"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL")
    )
    viral_content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("viral_content.id", ondelete="SET NULL")
    )
    hook_type: Mapped[HookTypeEnum] = mapped_column(
        sa.Enum(HookTypeEnum, name="hook_type_enum"), nullable=False
    )
    platform: Mapped[PlatformEnum] = mapped_column(
        sa.Enum(PlatformEnum, name="platform_enum"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_count: Mapped[Optional[int]] = mapped_column(Integer)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="hooks")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="hooks")
    viral_content: Mapped[Optional["ViralContent"]] = relationship(
        "ViralContent", back_populates="hooks"
    )
    scripts: Mapped[List["Script"]] = relationship("Script", back_populates="hook")


class Script(Base):
    __tablename__ = "scripts"
    __table_args__ = (
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_scripts_duration_positive",
        ),
        CheckConstraint(
            "word_count IS NULL OR word_count >= 0",
            name="ck_scripts_word_count",
        ),
        Index("idx_scripts_user_id", "user_id"),
        Index("idx_scripts_topic_id", "topic_id"),
        Index("idx_scripts_hook_id", "hook_id"),
        Index("idx_scripts_platform", "platform"),
        Index("idx_scripts_status", "status"),
        Index("idx_scripts_created_at", "created_at"),
        Index("idx_scripts_user_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL")
    )
    hook_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hooks.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[PlatformEnum] = mapped_column(
        sa.Enum(PlatformEnum, name="platform_enum"), nullable=False
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    outline: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[ScriptStatusEnum] = mapped_column(
        sa.Enum(ScriptStatusEnum, name="script_status_enum"),
        nullable=False,
        default=ScriptStatusEnum.draft,
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scripts")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="scripts")
    hook: Mapped[Optional["Hook"]] = relationship("Hook", back_populates="scripts")


class DailyReport(Base):
    __tablename__ = "daily_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "report_date", name="uq_daily_reports_user_date"),
        Index("idx_daily_reports_user_id", "user_id"),
        Index("idx_daily_reports_report_date", "report_date"),
        Index("idx_daily_reports_user_date", "user_id", "report_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    topics_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    viral_content_collected: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    hooks_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scripts_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trends_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reports_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_trends: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    top_platforms: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    summary: Mapped[Optional[str]] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_reports")


class AgentLog(Base):
    __tablename__ = "agent_logs"
    __table_args__ = (
        Index("idx_agent_logs_user_id", "user_id"),
        Index("idx_agent_logs_agent_name", "agent_name"),
        Index("idx_agent_logs_task_type", "task_type"),
        Index("idx_agent_logs_status", "status"),
        Index("idx_agent_logs_created_at", "created_at"),
        Index("idx_agent_logs_parent_log_id", "parent_log_id"),
        Index(
            "idx_agent_logs_failed",
            "user_id",
            "agent_name",
            postgresql_where=text("status = 'failed'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    parent_log_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_logs.id", ondelete="SET NULL")
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentStatusEnum] = mapped_column(
        sa.Enum(AgentStatusEnum, name="agent_status_enum"),
        nullable=False,
        default=AgentStatusEnum.pending,
    )
    input: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    output: Mapped[Optional[dict]] = mapped_column(JSONB)
    error: Mapped[Optional[str]] = mapped_column(Text)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="agent_logs")
    parent_log: Mapped[Optional["AgentLog"]] = relationship(
        "AgentLog",
        remote_side="AgentLog.id",
        backref="sub_tasks",
    )


class Analytics(Base):
    __tablename__ = "analytics"
    __table_args__ = (
        Index("idx_analytics_user_id", "user_id"),
        Index("idx_analytics_entity_type", "entity_type"),
        Index("idx_analytics_entity_id", "entity_id"),
        Index("idx_analytics_event_type", "event_type"),
        Index("idx_analytics_created_at", "created_at"),
        Index("idx_analytics_user_entity", "user_id", "entity_type", "entity_id"),
        Index(
            "idx_analytics_entity_event",
            "entity_type",
            "event_type",
            "created_at",
        ),
        Index(
            "idx_analytics_metadata_gin",
            "metadata",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[EntityTypeEnum] = mapped_column(
        sa.Enum(EntityTypeEnum, name="entity_type_enum"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[EventTypeEnum] = mapped_column(
        sa.Enum(EventTypeEnum, name="event_type_enum"), nullable=False
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict,
        server_default=text("'{}'::jsonb"),
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analytics")
