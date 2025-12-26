"""Add image_url to Message model

Revision ID: 001
Revises:
Create Date: 2025-12-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add image_url column to messages table"""
    op.add_column('messages', sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Remove image_url column from messages table"""
    op.drop_column('messages', 'image_url')
