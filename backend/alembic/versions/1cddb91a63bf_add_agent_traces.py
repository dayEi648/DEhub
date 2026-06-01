"""add_agent_traces

Revision ID: 1cddb91a63bf
Revises: dce1e1a610a1
Create Date: 2026-06-01 22:27:01.323080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1cddb91a63bf'
down_revision: Union[str, Sequence[str], None] = 'dce1e1a610a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'agent_traces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trace_id', sa.String(length=64), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('graph_name', sa.String(length=50), nullable=False, server_default='chat_agent'),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('input_message', sa.Text(), nullable=True),
        sa.Column('output_message', sa.Text(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('tool_calls_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('node_steps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_type', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trace_id'),
        sa.ForeignKeyConstraint(
            ['conversation_id'], ['ai_conversations.id'], ondelete='SET NULL'
        ),
    )
    op.create_index(
        'idx_agent_traces_conv_started',
        'agent_traces',
        ['conversation_id', sa.literal_column('started_at DESC')],
        unique=False,
    )
    op.create_index(
        'idx_agent_traces_user_started',
        'agent_traces',
        ['user_id', sa.literal_column('started_at DESC')],
        unique=False,
    )
    op.create_index(
        'idx_agent_traces_status',
        'agent_traces',
        ['status'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_agent_traces_status', table_name='agent_traces')
    op.drop_index('idx_agent_traces_user_started', table_name='agent_traces')
    op.drop_index('idx_agent_traces_conv_started', table_name='agent_traces')
    op.drop_table('agent_traces')
