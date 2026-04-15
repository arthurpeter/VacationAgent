"""add cleanup jobs

Revision ID: 8dadc1ef6431
Revises: 10d27dbdc81b
Create Date: 2026-04-15 15:36:21.579848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dadc1ef6431'
down_revision: Union[str, Sequence[str], None] = '10d27dbdc81b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_cron;")
    
    op.execute("""
        SELECT cron.schedule('cleanup_vacation_sessions', '0 * * * *', $$
            DELETE FROM vacation_session 
            WHERE expires_at IS NOT NULL AND expires_at < NOW();
        $$);
    """)
    
    op.execute("""
        SELECT cron.schedule('cleanup_blacklist_tokens', '0 * * * *', $$
            DELETE FROM blacklist_token 
            WHERE expires_at IS NOT NULL AND expires_at < NOW();
        $$);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("SELECT cron.unschedule('cleanup_vacation_sessions');")
    op.execute("SELECT cron.unschedule('cleanup_blacklist_tokens');")
    op.execute("DROP EXTENSION IF EXISTS pg_cron;")
