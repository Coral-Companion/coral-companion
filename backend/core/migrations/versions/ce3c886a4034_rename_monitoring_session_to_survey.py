
"""Rename monitoring session to survey

Revision ID: ce3c886a4034
Revises: 195b031a8c66
Create Date: 2026-11-10 19:47:12.012165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ce3c886a4034'
down_revision: Union[str, Sequence[str], None] = '195b031a8c66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.rename_table(
        'monitoring_sessions',
        'surveys',
    )

    op.alter_column(
        table_name='observations',
        column_name='monitoring_session_id',
        new_column_name='survey_id',
        existing_type=sa.Uuid(),
        existing_nullable=False,
    )

    op.execute(
        """
        ALTER TABLE observations
        RENAME CONSTRAINT observations_monitoring_session_id_fkey
        TO observations_survey_id_fkey
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        """
        ALTER TABLE observations
        RENAME CONSTRAINT observations_survey_id_fkey
        TO observations_monitoring_session_id_fkey
        """
    )

    op.alter_column(
        table_name='observations',
        column_name='survey_id',
        new_column_name='monitoring_session_id',
        existing_type=sa.Uuid(),
        existing_nullable=False,
    )

    op.rename_table(
        'surveys',
        'monitoring_sessions',
    )
