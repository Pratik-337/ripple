from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Load all models so Alembic can build the metadata
import app.models  # noqa: F401

from app.core.database import Base
from app.core.config import settings

config = context.config

# Override sqlalchemy.url from settings (swap asyncpg → psycopg2 for sync Alembic)
sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

IGNORE_INDEXES = {
    "idx_comp_deps_source",
    "idx_comp_deps_target",
    "idx_changes_project",
    "idx_impacts_change",
    "idx_impacts_contrib",
    "idx_notifs_recipient",
    "idx_files_component",
    "idx_drafts_file",
}

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "index" and name in IGNORE_INDEXES:
        return False
    return True

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine
    connectable = create_engine(sync_url, poolclass=pool.NullPool)
    with connectable.begin() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
