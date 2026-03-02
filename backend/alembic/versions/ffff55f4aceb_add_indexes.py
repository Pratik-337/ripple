"""add_indexes

Revision ID: ffff55f4aceb
Revises: 586a722f4624
Create Date: 2026-02-27 07:51:32.249872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffff55f4aceb'
down_revision: Union[str, None] = '586a722f4624'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_comp_deps_source', 'component_dependencies', ['source_component_id'])
    op.create_index('idx_comp_deps_target', 'component_dependencies', ['target_component_id'])
    op.create_index('idx_changes_project', 'change_requests', ['project_id', 'status'])
    op.create_index('idx_impacts_change', 'change_impacts', ['change_request_id'])
    op.create_index('idx_impacts_contrib', 'change_impacts', ['contributor_id', 'acknowledged'])
    op.create_index('idx_notifs_recipient', 'notifications', ['user_id', 'is_read', sa.text('created_at DESC')])
    op.create_index('idx_files_component', 'project_files', ['component_id'])
    op.create_index('idx_drafts_file', 'file_drafts', ['file_id', 'is_active'])

def downgrade() -> None:
    op.drop_index('idx_drafts_file', table_name='file_drafts')
    op.drop_index('idx_files_component', table_name='project_files')
    op.drop_index('idx_notifs_recipient', table_name='notifications')
    op.drop_index('idx_impacts_contrib', table_name='change_impacts')
    op.drop_index('idx_impacts_change', table_name='change_impacts')
    op.drop_index('idx_changes_project', table_name='change_requests')
    op.drop_index('idx_comp_deps_target', table_name='component_dependencies')
    op.drop_index('idx_comp_deps_source', table_name='component_dependencies')
