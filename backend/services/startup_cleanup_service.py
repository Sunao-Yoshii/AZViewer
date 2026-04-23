from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection

from backend.repositories import ImageFileRepository


class StartupCleanupService:
    """アプリケーション起動時に登録済みデータの整合性を保つ処理を提供する。"""

    def __init__(self, connection: Connection, repository: ImageFileRepository) -> None:
        """クリーンアップ処理で利用するDB接続とリポジトリを保持する。"""

        self._connection = connection
        self._repository = repository

    def cleanup_missing_files(self) -> int:
        """実ファイルが存在しなくなった画像ファイル情報を削除し、削除件数を返す。"""

        paths = self._repository.find_all_paths()
        missing_paths = [path for path in paths if not Path(path).is_file()]

        if not missing_paths:
            return 0

        self._repository.delete_by_paths(missing_paths)
        self._connection.commit()
        return len(missing_paths)
