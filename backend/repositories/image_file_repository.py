from __future__ import annotations

from sqlite3 import Connection

from backend.models import ImageFileRecord


class ImageFileRepository:
    """画像ファイル情報を保存するSQLiteテーブルへのアクセスを担当する。"""

    def __init__(self, connection: Connection) -> None:
        """リポジトリで利用するSQLite接続を保持する。"""

        self._connection = connection

    def create_table(self) -> None:
        """画像ファイル情報を保存するテーブルを作成する。"""

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS image_file_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                folder TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('General', 'R-15', 'R-18', 'R-18G')),
                is_checked INTEGER NOT NULL CHECK (is_checked IN (0, 1)),
                is_favorite INTEGER NOT NULL CHECK (is_favorite IN (0, 1)),
                comment TEXT NULL
            )
            """
        )
        self._connection.commit()

    def find_all_paths(self) -> list[str]:
        """登録済み画像ファイルのパス一覧を取得する。"""

        rows = self._connection.execute("SELECT path FROM image_file_data").fetchall()
        return [str(row["path"]) for row in rows]

    def delete_by_paths(self, paths: list[str]) -> None:
        """指定されたパスに一致する画像ファイル情報を削除する。"""

        if not paths:
            return

        self._connection.executemany(
            "DELETE FROM image_file_data WHERE path = ?",
            [(path,) for path in paths],
        )

    def insert_many(self, records: list[ImageFileRecord]) -> None:
        """複数の画像ファイル情報を一括登録する。"""

        if not records:
            return

        self._connection.executemany(
            """
            INSERT INTO image_file_data (
                filename,
                path,
                folder,
                rating,
                is_checked,
                is_favorite,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    record.filename,
                    record.path,
                    record.folder,
                    record.rating,
                    record.is_checked,
                    record.is_favorite,
                    record.comment,
                )
                for record in records
            ],
        )

    def exists_by_path(self, path: str) -> bool:
        """指定されたパスの画像ファイル情報が登録済みか判定する。"""

        row = self._connection.execute(
            "SELECT 1 FROM image_file_data WHERE path = ? LIMIT 1",
            (path,),
        ).fetchone()
        return row is not None
