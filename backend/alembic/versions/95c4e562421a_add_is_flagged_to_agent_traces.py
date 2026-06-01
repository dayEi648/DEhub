"""add_is_flagged_to_agent_traces

Revision ID: 95c4e562421a
Revises: f4011120a712
Create Date: 2026-06-02 00:16:42.454675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95c4e562421a'
down_revision: Union[str, Sequence[str], None] = 'f4011120a712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "agent_traces",
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("idx_agent_traces_flagged", "agent_traces", ["is_flagged"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_agent_traces_flagged", table_name="agent_traces")
    op.drop_column("agent_traces", "is_flagged")
