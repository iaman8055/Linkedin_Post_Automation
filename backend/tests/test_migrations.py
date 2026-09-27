from pathlib import Path

from alembic.config import Config
from pytest import MonkeyPatch
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings


def test_initial_migration_upgrades_and_downgrades(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    backend_root = Path(__file__).resolve().parents[1]
    config = Config(backend_root / "alembic.ini")
    config.set_main_option("script_location", str(backend_root / "alembic"))

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    assert len(tables) == 21
    assert {"alembic_version", "auth_tokens", "users", "posts"} <= tables

    command.downgrade(config, "base")
    remaining_tables = set(inspect(engine).get_table_names())
    assert remaining_tables <= {"alembic_version"}
    engine.dispose()
    get_settings.cache_clear()
