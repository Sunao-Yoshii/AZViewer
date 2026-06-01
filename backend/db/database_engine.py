from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool


def create_database_engine(db_path: str | Path) -> Engine:
    """AZViewer 用 SQLite Engine を作成し、接続ごとの PRAGMA を設定する。"""

    db_file = Path(db_path).resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"timeout": 30},
        poolclass=NullPool,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA busy_timeout = 30000")
        finally:
            cursor.close()

    with engine.connect() as conn:
        journal_mode = conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            text("PRAGMA journal_mode = WAL")
        ).scalar()
        if str(journal_mode).lower() != "wal":
            raise RuntimeError(f"SQLite WAL mode を有効化できませんでした: {journal_mode}")

    return engine
