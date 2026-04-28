from __future__ import annotations

from sqlite3 import Connection

from backend.db import ConnectionManager


class DatabaseLifecycleManager:
    """アプリケーション全体で共有するSQLite接続のライフサイクルのみを管理する。

    Repository / Service / API インスタンスは保持しない。
    """

    def __init__(self) -> None:
        """共有SQLite接続の管理に使うConnectionManagerを準備する。"""

        self._connection_manager = ConnectionManager()
        self._initialized = False

    def initialize(self) -> None:
        """共有SQLite接続を初期化する。"""

        if self._initialized:
            return

        self._connection_manager.initialize()
        self._initialized = True

    def close(self) -> None:
        """共有SQLite接続を閉じる。"""

        self._connection_manager.close()
        self._initialized = False

    def get_connection(self) -> Connection:
        """初期化済みの共有SQLite接続を返す。"""

        self.initialize()
        return self._connection_manager.get_connection()
