"""Add application persistence, organisation ownership and demo indicators."""

import sqlalchemy as sa
from alembic import op

revision = "7a05cf21b8d4"
down_revision = "2deb215f12b2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("synthetic", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("users", sa.Column("organisation_name", sa.String(120), nullable=True))
    op.add_column("posts", sa.Column("synthetic", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("opportunities", sa.Column("hard_age_limit", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("athlete_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(24), server_default="submitted", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("athlete_id", "opportunity_id", name="uq_application_athlete_opportunity"),
    )
    op.create_index("ix_applications_opportunity_id", "applications", ["opportunity_id"])


def downgrade():
    op.drop_table("applications")
    op.drop_column("opportunities", "hard_age_limit")
    op.drop_column("posts", "synthetic")
    op.drop_column("users", "organisation_name")
    op.drop_column("users", "synthetic")
