from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.config.settings import settings
from app.database.base import Base

# Import all models so Alembic can detect their tables.
from app.models.user import User
from app.models.line import Line
from app.models.stand_position import Position
from app.models.stand_asset import StandAsset
from app.models.entry_guide_asset import EntryGuideAsset
from app.models.stand_installation import StandInstallation
from app.models.entry_guide_installation import EntryGuideInstallation
from app.models.activity_log import ActivityLog
from app.models.stand_change_event import StandChangeEvent
from app.models.inventory_item import InventoryItem
from app.models.inventory_transaction import InventoryTransaction
from app.models.stand_preparation_event import StandPreparationEvent


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy metadata containing all registered models.
target_metadata = Base.metadata

# Use the application's database URL.
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL
)


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
