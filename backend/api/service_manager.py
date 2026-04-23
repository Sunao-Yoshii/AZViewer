from __future__ import annotations

from backend.db import ConnectionManager


class ServiceManager:
    """ConnectionManager の生成・接続ライフサイクル管理を担当する。"""

    def __init__(self) -> None:
        """接続管理を未初期化状態で準備する。"""

        self._connection_manager = ConnectionManager()
        self._initialized = False

    def initialize(self) -> None:
        """データベース接続を初期化する。"""

        if self._initialized:
            return

        self._connection_manager.initialize()
        self._initialized = True

    def close(self) -> None:
        """保持している接続を閉じる。"""

        self._connection_manager.close()

    def get_connection(self):
        """初期化済みの単一コネクションを返す。"""

        self.initialize()
        return self._connection_manager.get_connection()
