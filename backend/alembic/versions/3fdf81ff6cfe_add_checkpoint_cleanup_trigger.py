"""add_checkpoint_cleanup_trigger

Revision ID: 3fdf81ff6cfe
Revises: ea5a8a1c516e
Create Date: 2026-03-06 12:12:56.652787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fdf81ff6cfe'
down_revision: Union[str, Sequence[str], None] = 'ea5a8a1c516e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE OR REPLACE FUNCTION delete_session_checkpoints()
        RETURNS TRIGGER AS $$
        BEGIN
            -- LangGraph thread_id is the string version of VacationSession.id
            DELETE FROM checkpoints WHERE thread_id = CAST(OLD.id AS TEXT);
            DELETE FROM checkpoint_blobs WHERE thread_id = CAST(OLD.id AS TEXT);
            DELETE FROM checkpoint_writes WHERE thread_id = CAST(OLD.id AS TEXT);
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
