"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('membership', sa.String(20), default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('default_ticker', sa.String(20), default='THYAO.IS'),
        sa.Column('default_interval', sa.String(10), default='5m'),
        sa.Column('risk_tolerance', sa.String(20), default='moderate'),
        sa.Column('email_notifications', sa.Boolean(), default=True),
        sa.Column('push_notifications', sa.Boolean(), default=True),
        sa.Column('sms_notifications', sa.Boolean(), default=False),
        sa.Column('price_alert_enabled', sa.Boolean(), default=True),
        sa.Column('signal_alert_enabled', sa.Boolean(), default=True),
        sa.Column('news_alert_enabled', sa.Boolean(), default=False),
        sa.Column('theme', sa.String(20), default='dark'),
        sa.Column('language', sa.String(10), default='tr'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_profiles_id', 'user_profiles', ['id'])
    
    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, default='Ana Portföy'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('total_value', sa.Float(), default=0.0),
        sa.Column('total_cost', sa.Float(), default=0.0),
        sa.Column('total_profit_loss', sa.Float(), default=0.0),
        sa.Column('total_profit_loss_percent', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_portfolios_id', 'portfolios', ['id'])
    op.create_index('ix_portfolios_user_id', 'portfolios', ['user_id'])
    
    # Create portfolio_transactions table
    op.create_table(
        'portfolio_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('commission', sa.Float(), default=0.0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE')
    )
    op.create_index('ix_portfolio_transactions_id', 'portfolio_transactions', ['id'])
    op.create_index('ix_portfolio_transactions_portfolio_id', 'portfolio_transactions', ['portfolio_id'])
    op.create_index('ix_portfolio_transactions_ticker', 'portfolio_transactions', ['ticker'])
    
    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, default='Takip Listem'),
        sa.Column('tickers', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_watchlists_id', 'watchlists', ['id'])
    op.create_index('ix_watchlists_user_id', 'watchlists', ['user_id'])


def downgrade() -> None:
    op.drop_table('watchlists')
    op.drop_table('portfolio_transactions')
    op.drop_table('portfolios')
    op.drop_table('user_profiles')
    op.drop_table('users')
