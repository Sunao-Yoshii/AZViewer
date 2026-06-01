from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine

from backend.db import create_database_engine


class DatabaseLifecycleManager:
    """アプリケーション全体で共有する SQLAlchemy Engine のライフサイクルを管理する。

    Repository / Service / API インスタンスは保持しない。
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Engine 作成に使う DB パスと初期化状態を保持する。"""

        self._db_path = Path(db_path) if db_path else Path.cwd() / "data" / "az_data.sqlite3"
        self._engine: Engine | None = None

    def initialize(self) -> None:
        """共有 Engine を初期化する。"""

        if self._engine is not None:
            return

        self._engine = create_database_engine(self._db_path)

    def get_engine(self) -> Engine:
        """初期化済みの共有 Engine を返す。"""

        if self._engine is None:
            self.initialize()
        if self._engine is None:
            raise RuntimeError("Database engine が初期化されていません。")
        return self._engine

    def dispose(self) -> None:
        """共有 Engine を破棄する。"""

        if self._engine is None:
            return

        self._engine.dispose()
        self._engine = None

    def close(self) -> None:
        """互換用の終了処理。新規実装では dispose() を使う。"""

        self.dispose()
