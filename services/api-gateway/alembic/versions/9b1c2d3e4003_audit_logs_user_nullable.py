"""audit_logs.user_id nullable (eventos sin actor autenticado)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "9b1c2d3e4003"
down_revision = "8a2b3c4d5002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE audit_logs SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1) WHERE user_id IS NULL",
    )
    op.alter_column(
        "audit_logs",
        "user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
