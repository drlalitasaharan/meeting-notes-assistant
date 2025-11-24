"""merge alembic heads

This revision merges the two previous heads:

- 2033_scheduled_at
- 7cb9db845fc3
"""

import sqlalchemy as sa  # noqa: F401

from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision = "dbd7b21aa1fa"
down_revision = ("2033_scheduled_at", "7cb9db845fc3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge-only revision: no-op upgrade.
    pass


def downgrade() -> None:
    # Merge-only revision: no-op downgrade.
    pass
