"""Add itineraries table.

Revision ID: 20260602_0002
Revises: 20260602_0001
Create Date: 2026-06-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260602_0002"
down_revision: Union[str, Sequence[str], None] = "20260602_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "itineraries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("days", sa.JSON(), nullable=False),
        sa.Column("budget", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
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
            name=op.f("fk_itineraries_session_id_travel_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_itineraries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_itineraries")),
    )
    op.create_index(
        op.f("ix_itineraries_session_id"),
        "itineraries",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itineraries_user_id"),
        "itineraries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itineraries_status"),
        "itineraries",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_itineraries_status"), table_name="itineraries")
    op.drop_index(op.f("ix_itineraries_user_id"), table_name="itineraries")
    op.drop_index(op.f("ix_itineraries_session_id"), table_name="itineraries")
    op.drop_table("itineraries")
