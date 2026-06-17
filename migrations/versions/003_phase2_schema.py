"""Phase 2 schema additions

Revision ID: 003
Revises: 002
Create Date: 2025-01-01 00:00:00.000000

Changes:
- viral_content: content_hash column + unique constraint per user
- trend_analysis: previous_trend_id self-reference FK
- hooks: user_rating, user_notes, rated_at
- scripts: script_format enum, user_rating, user_notes, rated_at,
           published_at, publish_platform
- New tables: keywords, trend_keywords, sources, research_report_sources
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── script_format_enum ────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE script_format_enum AS ENUM "
        "('short_form', 'long_form', 'carousel', 'thread', 'experimental')"
    )

    # ── viral_content: content_hash ───────────────────────────────────────────
    op.add_column("viral_content", sa.Column("content_hash", sa.String(64), nullable=True))
    op.create_unique_constraint(
        "uq_viral_content_user_hash", "viral_content", ["user_id", "content_hash"]
    )
    op.create_index("idx_viral_content_content_hash", "viral_content", ["content_hash"])

    # ── trend_analysis: previous_trend_id ─────────────────────────────────────
    op.add_column(
        "trend_analysis",
        sa.Column("previous_trend_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_trend_analysis_previous",
        "trend_analysis",
        "trend_analysis",
        ["previous_trend_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── hooks: rating fields ──────────────────────────────────────────────────
    op.add_column("hooks", sa.Column("user_rating", sa.Integer(), nullable=True))
    op.add_column("hooks", sa.Column("user_notes", sa.Text(), nullable=True))
    op.add_column("hooks", sa.Column("rated_at", sa.DateTime(timezone=True), nullable=True))

    # ── scripts: format + rating + publish fields ─────────────────────────────
    op.add_column(
        "scripts",
        sa.Column(
            "script_format",
            sa.Enum(
                "short_form", "long_form", "carousel", "thread", "experimental",
                name="script_format_enum",
            ),
            nullable=False,
            server_default="short_form",
        ),
    )
    op.add_column("scripts", sa.Column("user_rating", sa.Integer(), nullable=True))
    op.add_column("scripts", sa.Column("user_notes", sa.Text(), nullable=True))
    op.add_column("scripts", sa.Column("rated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scripts", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scripts", sa.Column("publish_platform", sa.String(50), nullable=True))

    # ── keywords table ────────────────────────────────────────────────────────
    op.create_table(
        "keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keyword", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("keyword"),
    )
    op.create_index("idx_keywords_keyword", "keywords", ["keyword"])

    # ── trend_keywords junction ───────────────────────────────────────────────
    op.create_table(
        "trend_keywords",
        sa.Column("trend_analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keyword_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.ForeignKeyConstraint(
            ["trend_analysis_id"], ["trend_analysis.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("trend_analysis_id", "keyword_id"),
    )

    # ── sources table ─────────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reliability_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("content_checksum", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("idx_sources_domain", "sources", ["domain"])
    op.create_index("idx_sources_url", "sources", ["url"])

    # ── research_report_sources junction ──────────────────────────────────────
    op.create_table(
        "research_report_sources",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("relevance", sa.Float(), nullable=False, server_default="1.0"),
        sa.ForeignKeyConstraint(
            ["report_id"], ["research_reports.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("report_id", "source_id"),
    )


def downgrade() -> None:
    op.drop_table("research_report_sources")
    op.drop_index("idx_sources_url", table_name="sources")
    op.drop_index("idx_sources_domain", table_name="sources")
    op.drop_table("sources")
    op.drop_table("trend_keywords")
    op.drop_index("idx_keywords_keyword", table_name="keywords")
    op.drop_table("keywords")

    op.drop_column("scripts", "publish_platform")
    op.drop_column("scripts", "published_at")
    op.drop_column("scripts", "rated_at")
    op.drop_column("scripts", "user_notes")
    op.drop_column("scripts", "user_rating")
    op.drop_column("scripts", "script_format")

    op.drop_column("hooks", "rated_at")
    op.drop_column("hooks", "user_notes")
    op.drop_column("hooks", "user_rating")

    op.drop_constraint("fk_trend_analysis_previous", "trend_analysis", type_="foreignkey")
    op.drop_column("trend_analysis", "previous_trend_id")

    op.drop_index("idx_viral_content_content_hash", table_name="viral_content")
    op.drop_constraint("uq_viral_content_user_hash", "viral_content", type_="unique")
    op.drop_column("viral_content", "content_hash")

    op.execute("DROP TYPE script_format_enum")
