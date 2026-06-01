"""add_agent_spans

Revision ID: 45f63597f15b
Revises: 1cddb91a63bf
Create Date: 2026-06-01 22:27:01.323080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '45f63597f15b'
down_revision: Union[str, Sequence[str], None] = '1cddb91a63bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'agent_spans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trace_id', sa.String(length=64), nullable=False),
        sa.Column('parent_span_id', sa.Integer(), nullable=True),
        sa.Column('span_type', sa.String(length=20), nullable=False),
        sa.Column('span_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('token_usage', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['trace_id'], ['agent_traces.trace_id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['parent_span_id'], ['agent_spans.id'], ondelete='CASCADE'
        ),
    )
    op.create_index(
        'idx_agent_spans_trace',
        'agent_spans',
        ['trace_id'],
        unique=False,
    )
    op.create_index(
        'idx_agent_spans_type',
        'agent_spans',
        ['span_type'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_agent_spans_type', table_name='agent_spans')
    op.drop_index('idx_agent_spans_trace', table_name='agent_spans')
    op.drop_table('agent_spans')
