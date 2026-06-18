"""Initial schema — all tables, indexes, and constraints

Revision ID: 001
Revises:
Create Date: 2026-06-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Enum helpers ──────────────────────────────────────────────────────────────

def _safe_create_enum(name: str, values: str) -> None:
    op.execute(sa.text(
        f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))


def _create_enums() -> None:
    _safe_create_enum("plan_enum", "'free', 'pro', 'enterprise'")
    _safe_create_enum("platform_enum", "'youtube', 'tiktok', 'instagram', 'twitter', 'linkedin', 'reddit', 'other'")
    _safe_create_enum("content_type_enum", "'video', 'post', 'article', 'thread', 'reel', 'short'")
    _safe_create_enum("trend_period_enum", "'daily', 'weekly', 'monthly'")
    _safe_create_enum("trend_velocity_enum", "'rising', 'falling', 'stable', 'viral'")
    _safe_create_enum("report_status_enum", "'draft', 'processing', 'completed', 'archived'")
    _safe_create_enum("hook_type_enum", "'question', 'statement', 'statistic', 'story', 'controversy', 'list', 'challenge'")
    _safe_create_enum("script_status_enum", "'draft', 'review', 'approved', 'published', 'archived'")
    _safe_create_enum("agent_status_enum", "'pending', 'running', 'completed', 'failed', 'cancelled'")
    _safe_create_enum("entity_type_enum", "'topic', 'viral_content', 'trend_analysis', 'research_report', 'hook', 'script', 'daily_report'")
    _safe_create_enum("event_type_enum", "'view', 'create', 'update', 'delete', 'export', 'copy', 'share', 'generate', 'approve', 'publish'")


def _drop_enums() -> None:
    for name in [
        "event_type_enum", "entity_type_enum", "agent_status_enum",
        "script_status_enum", "hook_type_enum", "report_status_enum",
        "trend_velocity_enum", "trend_period_enum", "content_type_enum",
        "platform_enum", "plan_enum",
    ]:
        op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))


# ── Upgrade ───────────────────────────────────────────────────────────────────

def upgrade() -> None:
    _create_enums()

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column(
            "plan",
            sa.Enum(name="plan_enum", create_type=False),
            nullable=False,
            server_default="free",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("monthly_token_quota", sa.BigInteger(), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_is_active", "users", ["is_active"])
    op.create_index("idx_users_plan", "users", ["plan"])
    op.create_index("idx_users_created_at", "users", ["created_at"])

    # ── topics ────────────────────────────────────────────────────────────────
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "name", name="uq_topics_user_name"),
    )
    op.create_index("idx_topics_user_id", "topics", ["user_id"])
    op.create_index("idx_topics_is_active", "topics", ["is_active"])
    op.create_index("idx_topics_category", "topics", ["category"])
    op.create_index("idx_topics_created_at", "topics", ["created_at"])

    # ── viral_content ─────────────────────────────────────────────────────────
    op.create_table(
        "viral_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "topic_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "platform",
            sa.Enum(name="platform_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.Enum(name="content_type_enum", create_type=False),
            nullable=True,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content_url", sa.Text(), nullable=True),
        sa.Column("views", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("likes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("shares", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("comments", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("engagement_rate", sa.Float(), nullable=True),
        sa.Column("viral_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "collected_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "viral_score >= 0 AND viral_score <= 100",
            name="ck_viral_content_viral_score",
        ),
        sa.CheckConstraint("views >= 0", name="ck_viral_content_views"),
        sa.CheckConstraint("likes >= 0", name="ck_viral_content_likes"),
        sa.CheckConstraint("shares >= 0", name="ck_viral_content_shares"),
        sa.CheckConstraint("comments >= 0", name="ck_viral_content_comments"),
    )
    op.create_index("idx_viral_content_user_id", "viral_content", ["user_id"])
    op.create_index("idx_viral_content_topic_id", "viral_content", ["topic_id"])
    op.create_index("idx_viral_content_platform", "viral_content", ["platform"])
    op.create_index("idx_viral_content_viral_score", "viral_content", ["viral_score"])
    op.create_index("idx_viral_content_collected_at", "viral_content", ["collected_at"])
    op.create_index("idx_viral_content_published_at", "viral_content", ["published_at"])
    op.create_index(
        "idx_viral_content_user_platform", "viral_content", ["user_id", "platform"]
    )

    # ── trend_analysis ────────────────────────────────────────────────────────
    op.create_table(
        "trend_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "topic_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "period",
            sa.Enum(name="trend_period_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("trend_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "velocity",
            sa.Enum(name="trend_velocity_enum", create_type=False),
            nullable=False,
            server_default="stable",
        ),
        sa.Column(
            "keywords", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("insights", sa.Text(), nullable=True),
        sa.Column(
            "data_points", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "platforms", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "analyzed_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "trend_score >= 0 AND trend_score <= 100",
            name="ck_trend_analysis_trend_score",
        ),
    )
    op.create_index("idx_trend_analysis_user_id", "trend_analysis", ["user_id"])
    op.create_index("idx_trend_analysis_topic_id", "trend_analysis", ["topic_id"])
    op.create_index("idx_trend_analysis_period", "trend_analysis", ["period"])
    op.create_index("idx_trend_analysis_velocity", "trend_analysis", ["velocity"])
    op.create_index("idx_trend_analysis_trend_score", "trend_analysis", ["trend_score"])
    op.create_index("idx_trend_analysis_analyzed_at", "trend_analysis", ["analyzed_at"])
    op.create_index(
        "idx_trend_analysis_user_period", "trend_analysis", ["user_id", "period"]
    )

    # ── research_reports ──────────────────────────────────────────────────────
    op.create_table(
        "research_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "topic_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "sources", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "key_findings", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "tags", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.Enum(name="report_status_enum", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_research_reports_user_id", "research_reports", ["user_id"])
    op.create_index("idx_research_reports_topic_id", "research_reports", ["topic_id"])
    op.create_index("idx_research_reports_status", "research_reports", ["status"])
    op.create_index(
        "idx_research_reports_created_at", "research_reports", ["created_at"]
    )
    op.create_index(
        "idx_research_reports_active",
        "research_reports",
        ["user_id"],
        postgresql_where=sa.text("status != 'archived'"),
    )

    # ── hooks ─────────────────────────────────────────────────────────────────
    op.create_table(
        "hooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "topic_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "viral_content_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("viral_content.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "hook_type",
            sa.Enum(name="hook_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "platform",
            sa.Enum(name="platform_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("character_count", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)",
            name="ck_hooks_quality_score",
        ),
    )
    op.create_index("idx_hooks_user_id", "hooks", ["user_id"])
    op.create_index("idx_hooks_topic_id", "hooks", ["topic_id"])
    op.create_index("idx_hooks_viral_content_id", "hooks", ["viral_content_id"])
    op.create_index("idx_hooks_platform", "hooks", ["platform"])
    op.create_index("idx_hooks_hook_type", "hooks", ["hook_type"])
    op.create_index("idx_hooks_quality_score", "hooks", ["quality_score"])
    op.create_index("idx_hooks_is_used", "hooks", ["is_used"])
    op.create_index("idx_hooks_created_at", "hooks", ["created_at"])
    op.create_index(
        "idx_hooks_unused",
        "hooks",
        ["user_id", "platform"],
        postgresql_where=sa.text("is_used = false"),
    )

    # ── scripts ───────────────────────────────────────────────────────────────
    op.create_table(
        "scripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "topic_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "hook_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("hooks.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column(
            "platform",
            sa.Enum(name="platform_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "outline", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(name="script_status_enum", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_scripts_duration_positive",
        ),
        sa.CheckConstraint(
            "word_count IS NULL OR word_count >= 0",
            name="ck_scripts_word_count",
        ),
    )
    op.create_index("idx_scripts_user_id", "scripts", ["user_id"])
    op.create_index("idx_scripts_topic_id", "scripts", ["topic_id"])
    op.create_index("idx_scripts_hook_id", "scripts", ["hook_id"])
    op.create_index("idx_scripts_platform", "scripts", ["platform"])
    op.create_index("idx_scripts_status", "scripts", ["status"])
    op.create_index("idx_scripts_created_at", "scripts", ["created_at"])
    op.create_index("idx_scripts_user_status", "scripts", ["user_id", "status"])

    # ── daily_reports ─────────────────────────────────────────────────────────
    op.create_table(
        "daily_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column(
            "topics_analyzed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "viral_content_collected", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "hooks_generated", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "scripts_generated", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "trends_detected", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "reports_generated", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "top_trends", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "top_platforms", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("user_id", "report_date", name="uq_daily_reports_user_date"),
    )
    op.create_index("idx_daily_reports_user_id", "daily_reports", ["user_id"])
    op.create_index("idx_daily_reports_report_date", "daily_reports", ["report_date"])
    op.create_index(
        "idx_daily_reports_user_date", "daily_reports", ["user_id", "report_date"]
    )

    # ── agent_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "agent_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "parent_log_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_logs.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(name="agent_status_enum", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "input", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("error_traceback", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_agent_logs_user_id", "agent_logs", ["user_id"])
    op.create_index("idx_agent_logs_agent_name", "agent_logs", ["agent_name"])
    op.create_index("idx_agent_logs_task_type", "agent_logs", ["task_type"])
    op.create_index("idx_agent_logs_status", "agent_logs", ["status"])
    op.create_index("idx_agent_logs_created_at", "agent_logs", ["created_at"])
    op.create_index("idx_agent_logs_parent_log_id", "agent_logs", ["parent_log_id"])
    op.create_index(
        "idx_agent_logs_failed",
        "agent_logs",
        ["user_id", "agent_name"],
        postgresql_where=sa.text("status = 'failed'"),
    )

    # ── analytics ─────────────────────────────────────────────────────────────
    op.create_table(
        "analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "entity_type",
            sa.Enum(name="entity_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(name="event_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False, server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_analytics_user_id", "analytics", ["user_id"])
    op.create_index("idx_analytics_entity_type", "analytics", ["entity_type"])
    op.create_index("idx_analytics_entity_id", "analytics", ["entity_id"])
    op.create_index("idx_analytics_event_type", "analytics", ["event_type"])
    op.create_index("idx_analytics_created_at", "analytics", ["created_at"])
    op.create_index(
        "idx_analytics_user_entity",
        "analytics",
        ["user_id", "entity_type", "entity_id"],
    )
    op.create_index(
        "idx_analytics_entity_event",
        "analytics",
        ["entity_type", "event_type", "created_at"],
    )
    op.create_index(
        "idx_analytics_metadata_gin",
        "analytics",
        ["metadata"],
        postgresql_using="gin",
    )


# ── Downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    op.drop_table("analytics")
    op.drop_table("agent_logs")
    op.drop_table("daily_reports")
    op.drop_table("scripts")
    op.drop_table("hooks")
    op.drop_table("research_reports")
    op.drop_table("trend_analysis")
    op.drop_table("viral_content")
    op.drop_table("topics")
    op.drop_table("users")
    _drop_enums()
