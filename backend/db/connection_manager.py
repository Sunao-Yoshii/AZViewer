from __future__ import annotations

import sqlite3
from pathlib import Path


class ConnectionManager:
    """Owns the application-wide SQLite connection."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or Path.cwd() / "data" / "az_data.sqlite3"
        self._connection: sqlite3.Connection | None = None

    @property
    def db_path(self) -> Path:
        return self._db_path

    def initialize(self) -> None:
        if self._connection is not None:
            return

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self.initialize()
        if self._connection is None:
            raise RuntimeError("SQLite connection could not be initialized.")
        return self._connection

    def close(self) -> None:
        if self._connection is None:
            return

        self._connection.close()
        self._connection = None
