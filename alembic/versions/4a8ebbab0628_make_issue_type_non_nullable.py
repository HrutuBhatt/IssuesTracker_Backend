"""make_issue_type_non_nullable

Revision ID: 4a8ebbab0628
Revises: 0c24616ede6f
Create Date: 2026-06-25 11:40:47.118556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8ebbab0628'
down_revision: Union[str, Sequence[str], None] = '0c24616ede6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE issues SET issue_type = 'TRIAGE' WHERE issue_type IS NULL")
    with op.batch_alter_table('issues') as batch_op:
        batch_op.alter_column(
            'issue_type',
            existing_type=sa.Enum('BUG', 'FEATURE', 'CHANGE_REQUEST', 'TRIAGE', name='issuetype'),
            nullable=False,
            server_default='TRIAGE',
        )


def downgrade() -> None:
    with op.batch_alter_table('issues') as batch_op:
        batch_op.alter_column(
            'issue_type',
            existing_type=sa.Enum('BUG', 'FEATURE', 'CHANGE_REQUEST', 'TRIAGE', name='issuetype'),
            nullable=True,
            server_default=None,
        )
