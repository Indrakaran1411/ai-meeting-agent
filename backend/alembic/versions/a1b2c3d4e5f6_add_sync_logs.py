"""Add sync_logs table for webhook audit trail and idempotency

Revision ID: a1b2c3d4e5f6
Revises: 366f35fdc6b0
Create Date: 2026-06-28 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '366f35fdc6b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the sync_status enum type
    sync_status_enum = postgresql.ENUM(
        'PENDING', 'SUCCESS', 'FAILED',
        name='sync_status',
        create_type=True
    )
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'sync_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column(
            'meeting_id', sa.UUID(), nullable=False,
            comment='FK to the meeting being synced'
        ),
        sa.Column(
            'request_id', sa.String(length=128), nullable=True,
            comment='Correlation request ID from the originating HTTP request'
        ),
        sa.Column(
            'webhook_url', sa.String(length=2048), nullable=True,
            comment='Target webhook URL used for this dispatch attempt'
        ),
        sa.Column(
            'status',
            postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', name='sync_status', create_type=False),
            nullable=False,
            comment='PENDING on insert, updated to SUCCESS or FAILED after dispatch'
        ),
        sa.Column(
            'http_status', sa.Integer(), nullable=True,
            comment='HTTP response status code returned by the downstream receiver'
        ),
        sa.Column(
            'response_message', sa.Text(), nullable=True,
            comment='Contextual message from the dispatch outcome'
        ),
        sa.Column(
            'payload_hash', sa.String(length=64), nullable=True,
            comment='SHA-256 hex digest of the serialized JSON payload (for idempotency)'
        ),
        sa.Column(
            'dispatched_at', sa.DateTime(timezone=True), nullable=True,
            comment='Timestamp when the dispatch completed (null while PENDING)'
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
            comment='Timestamp when this audit record was created'
        ),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sync_logs_meeting_id', 'sync_logs', ['meeting_id'], unique=False)
    op.create_index('ix_sync_logs_status', 'sync_logs', ['status'], unique=False)
    op.create_index('ix_sync_logs_payload_hash', 'sync_logs', ['payload_hash'], unique=False)
    op.create_index(
        'ix_sync_logs_idempotency', 'sync_logs',
        ['meeting_id', 'payload_hash', 'status'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_sync_logs_idempotency', table_name='sync_logs')
    op.drop_index('ix_sync_logs_payload_hash', table_name='sync_logs')
    op.drop_index('ix_sync_logs_status', table_name='sync_logs')
    op.drop_index('ix_sync_logs_meeting_id', table_name='sync_logs')
    op.drop_table('sync_logs')

    # Drop the enum type after the table is removed
    sync_status_enum = postgresql.ENUM(name='sync_status')
    sync_status_enum.drop(op.get_bind(), checkfirst=True)
