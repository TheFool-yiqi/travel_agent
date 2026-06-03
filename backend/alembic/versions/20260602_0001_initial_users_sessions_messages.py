"""Initial users, travel_sessions, messages tables.

Revision ID: 20260602_0001
Revises:
Create Date: 2026-06-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260602_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "travel_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), server_default="新对话", nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column("extra_info", sa.JSON(), nullable=True),
        sa.Column("thread_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_travel_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_travel_sessions")),
        sa.UniqueConstraint("thread_id", name=op.f("uq_travel_sessions_thread_id")),
    )
    op.create_index(
        op.f("ix_travel_sessions_user_id"),
        "travel_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_travel_sessions_thread_id"),
        "travel_sessions",
        ["thread_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_travel_sessions_status"),
        "travel_sessions",
        ["status"],
        unique=False,
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("extra_info", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["travel_sessions.id"],
            name=op.f("fk_messages_session_id_travel_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(
        op.f("ix_messages_session_id"),
        "messages",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_role"),
        "messages",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messages_created_at"),
        "messages",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_created_at"), table_name="messages")
    op.drop_index(op.f("ix_messages_role"), table_name="messages")
    op.drop_index(op.f("ix_messages_session_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_travel_sessions_status"), table_name="travel_sessions")
    op.drop_index(op.f("ix_travel_sessions_thread_id"), table_name="travel_sessions")
    op.drop_index(op.f("ix_travel_sessions_user_id"), table_name="travel_sessions")
    op.drop_table("travel_sessions")
    op.drop_table("users")
