"""add checkpoint cleanup trigger

Revision ID: 3a679a51e891
Revises: e67af2186813
Create Date: 2026-04-15 15:39:13.896829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a679a51e891'
down_revision: Union[str, Sequence[str], None] = 'e67af2186813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE OR REPLACE FUNCTION delete_session_checkpoints()
        RETURNS TRIGGER AS $$
        BEGIN
            DELETE FROM checkpoints 
            WHERE thread_id IN ('discovery_' || CAST(OLD.id AS TEXT), 'itinerary_' || CAST(OLD.id AS TEXT));
            
            DELETE FROM checkpoint_blobs 
            WHERE thread_id IN ('discovery_' || CAST(OLD.id AS TEXT), 'itinerary_' || CAST(OLD.id AS TEXT));
            
            DELETE FROM checkpoint_writes 
            WHERE thread_id IN ('discovery_' || CAST(OLD.id AS TEXT), 'itinerary_' || CAST(OLD.id AS TEXT));
            
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_delete_checkpoints
        AFTER DELETE ON vacation_sessions
        FOR EACH ROW EXECUTE FUNCTION delete_session_checkpoints();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS trigger_delete_checkpoints ON vacation_sessions;")
    op.execute("DROP FUNCTION IF EXISTS delete_session_checkpoints();")
