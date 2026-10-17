"""Initial persistent curiosity archive and audit records."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "stars",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("interest_reason", sa.Text()),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_reference", sa.Text()),
        sa.Column("estimated_minutes", sa.Integer()),
        sa.Column("estimated_budget", sa.Float()),
        sa.Column("energy_level", sa.String(12)),
        sa.Column("status", sa.String(20), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "quests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_key", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_budget", sa.Float()),
        sa.Column("energy_level", sa.String(12), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("uncertainties", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "quest_stars",
        sa.Column(
            "quest_id", sa.String(36), sa.ForeignKey("quests.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("star_id", sa.String(36), sa.ForeignKey("stars.id", ondelete="RESTRICT"), primary_key=True),
    )
    op.create_table(
        "reflections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "quest_id",
            sa.String(36),
            sa.ForeignKey("quests.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("user_feedback", sa.Text(), nullable=False),
        sa.Column("liked_aspects", sa.JSON(), nullable=False),
        sa.Column("disliked_aspects", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("explicit", sa.JSON(), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "agent_runs",
        sa.Column("run_id", sa.String(36), primary_key=True),
        sa.Column("request_key", sa.String(100), nullable=False, unique=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("request_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("mode", sa.String(12), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("elapsed_ms", sa.Integer()),
        sa.Column("error_type", sa.String(80)),
        sa.Column("summary", sa.Text()),
        sa.Column("decisions", sa.JSON(), nullable=False),
    )


def downgrade():
    for name in ["agent_runs", "user_preferences", "reflections", "quest_stars", "quests", "stars"]:
        op.drop_table(name)
