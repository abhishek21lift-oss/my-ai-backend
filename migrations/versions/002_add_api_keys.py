"""add api_keys table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("rate_limit_tpd", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("idx_api_keys_key_prefix", "api_keys", ["key_prefix"])
    op.create_index("idx_api_keys_is_active", "api_keys", ["is_active"])


def downgrade() -> None:
    op.drop_index("idx_api_keys_is_active", table_name="api_keys")
    op.drop_index("idx_api_keys_key_prefix", table_name="api_keys")
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")
    op.drop_table("api_keys")
