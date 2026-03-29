"""add_pg_cron_cleanup_jobs

Revision ID: c2c2b3dfce45
Revises: 1e6e388c9646
Create Date: 2026-03-29 18:00:03.591690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2c2b3dfce45'
down_revision: Union[str, Sequence[str], None] = '1e6e388c9646'
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
