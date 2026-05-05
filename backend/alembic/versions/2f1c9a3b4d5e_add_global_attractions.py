"""add global attractions

Revision ID: 2f1c9a3b4d5e
Revises: 052f7eb1443f
Create Date: 2026-05-05 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f1c9a3b4d5e'
down_revision: Union[str, Sequence[str], None] = '052f7eb1443f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'global_attractions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('external_place_id', sa.String(), nullable=False),
        sa.Column('city_name', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('duration_mins', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_place_id')
    )
    op.create_index(op.f('ix_global_attractions_city_name'), 'global_attractions', ['city_name'], unique=False)
    op.create_index(op.f('ix_global_attractions_external_place_id'), 'global_attractions', ['external_place_id'], unique=False)
    op.create_index(op.f('ix_global_attractions_id'), 'global_attractions', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_global_attractions_id'), table_name='global_attractions')
    op.drop_index(op.f('ix_global_attractions_external_place_id'), table_name='global_attractions')
    op.drop_index(op.f('ix_global_attractions_city_name'), table_name='global_attractions')
    op.drop_table('global_attractions')
