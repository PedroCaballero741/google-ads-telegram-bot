"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ad_costs table
    op.create_table(
        'ad_costs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('campaign_id', sa.String(50), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=False),
        sa.Column('cost_micros', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'campaign_id', name='uix_date_campaign'),
    )
    op.create_index('ix_ad_costs_date', 'ad_costs', ['date'])
    op.create_index('ix_ad_costs_date_campaign', 'ad_costs', ['date', 'campaign_id'])

    # Create alert_thresholds table
    op.create_table(
        'alert_thresholds',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('threshold_type', sa.Enum('DAILY_SPEND', 'CAMPAIGN_SPEND', name='thresholdtype'), nullable=False),
        sa.Column('threshold_value', sa.Numeric(12, 2), nullable=False),
        sa.Column('campaign_id', sa.String(50), nullable=True),
        sa.Column('telegram_chat_id', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create alert_history table
    op.create_table(
        'alert_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('threshold_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('triggered_date', sa.Date(), nullable=False),
        sa.Column('actual_value', sa.Numeric(12, 2), nullable=False),
        sa.Column('message_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['threshold_id'], ['alert_thresholds.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('threshold_id', 'triggered_date', name='uix_threshold_date'),
    )
    op.create_index('ix_alert_history_triggered_date', 'alert_history', ['triggered_date'])


def downgrade() -> None:
    op.drop_table('alert_history')
    op.drop_table('alert_thresholds')
    op.drop_table('ad_costs')
    op.execute('DROP TYPE IF EXISTS thresholdtype')
