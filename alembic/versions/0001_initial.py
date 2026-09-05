"""Initial schema generated from SQLAlchemy metadata.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-24
"""

from alembic import op

from bookstore.database import Base
from bookstore.models import entities as _entities  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
