"""add_agent_evaluations

Revision ID: f4011120a712
Revises: 45f63597f15b
Create Date: 2026-06-01 23:42:15.633575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4011120a712'
down_revision: Union[str, Sequence[str], None] = '45f63597f15b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "agent_evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=True),
        sa.Column("eval_type", sa.String(length=30), nullable=False, server_default="auto_llm_judge"),
        sa.Column("dimension", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("evaluator_model", sa.String(length=50), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["trace_id"], ["agent_traces.trace_id"], ondelete="CASCADE"
        ),
    )
    op.create_index("idx_agent_evaluations_trace", "agent_evaluations", ["trace_id"])
    op.create_index(
        "idx_agent_evaluations_dimension",
        "agent_evaluations",
        ["dimension", "score"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_agent_evaluations_dimension", table_name="agent_evaluations")
    op.drop_index("idx_agent_evaluations_trace", table_name="agent_evaluations")
    op.drop_table("agent_evaluations")
