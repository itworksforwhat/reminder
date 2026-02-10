"""Initial schema - users, companies, reminders, templates

Revision ID: 001_initial
Revises:
Create Date: 2026-02-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Companies
    op.create_table(
        'companies',
        sa.Column('id', sa.Uuid(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('business_number', sa.String(20), nullable=True),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.UniqueConstraint('business_number'),
    )

    # Company Members
    op.create_table(
        'company_members',
        sa.Column('id', sa.Uuid(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

    # Templates
    op.create_table(
        'templates',
        sa.Column('id', sa.Uuid(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_templates_category', 'templates', ['category'])

    # Template Items
    op.create_table(
        'template_items',
        sa.Column('id', sa.Uuid(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('template_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('day', sa.Integer(), nullable=True),
        sa.Column('recurrence', sa.String(20), nullable=False, server_default='once'),
        sa.Column('adjust_for_holiday', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('extra_config', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id']),
    )

    # Reminders
    op.create_table(
        'reminders',
        sa.Column('id', sa.Uuid(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('deadline', sa.Date(), nullable=False),
        sa.Column('original_deadline', sa.Date(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('template_id', sa.Uuid(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    op.create_index('ix_reminders_category', 'reminders', ['category'])
    op.create_index('ix_reminders_deadline', 'reminders', ['deadline'])


def downgrade() -> None:
    op.drop_table('reminders')
    op.drop_table('template_items')
    op.drop_table('templates')
    op.drop_table('company_members')
    op.drop_table('companies')
    op.drop_table('users')
