"""Esquema inicial: users, projects, scans, vulnerabilities, audit_logs, use_cases, roles, permissions.

FKs con ON DELETE RESTRICT. Índices en columnas FK. Soft delete (deleted_at) salvo audit_logs.
Check line_number >= 0 en vulnerabilities.

Revision ID: 7f1a2b3c0001
Revises:
Create Date: 2025-03-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f1a2b3c0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "use_cases",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"], unique=False)

    op.create_table(
        "scans",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("tool", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scans_project_id", "scans", ["project_id"], unique=False)

    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("cve", sa.String(length=50), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("line_number >= 0", name="ck_vulnerabilities_line_number"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vulnerabilities_scan_id", "vulnerabilities", ["scan_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("entity", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)

    op.create_table(
        "permissions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("use_case_id", sa.BigInteger(), nullable=False),
        sa.Column("c", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("r", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("u", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("d", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["use_case_id"], ["use_cases.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_permissions_role_id", "permissions", ["role_id"], unique=False)
    op.create_index("ix_permissions_use_case_id", "permissions", ["use_case_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_permissions_use_case_id", table_name="permissions")
    op.drop_index("ix_permissions_role_id", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_vulnerabilities_scan_id", table_name="vulnerabilities")
    op.drop_table("vulnerabilities")

    op.drop_index("ix_scans_project_id", table_name="scans")
    op.drop_table("scans")

    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")

    op.drop_table("roles")
    op.drop_table("use_cases")
    op.drop_table("users")
