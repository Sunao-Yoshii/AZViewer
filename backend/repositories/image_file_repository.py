from __future__ import annotations

from sqlite3 import Connection

from backend.models import ImageFileRecord


class ImageFileRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def create_table(self) -> None:
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
        rows = self._connection.execute("SELECT path FROM image_file_data").fetchall()
        return [str(row["path"]) for row in rows]

    def delete_by_paths(self, paths: list[str]) -> None:
        if not paths:
            return

        self._connection.executemany(
            "DELETE FROM image_file_data WHERE path = ?",
            [(path,) for path in paths],
        )

    def insert_many(self, records: list[ImageFileRecord]) -> None:
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
        row = self._connection.execute(
            "SELECT 1 FROM image_file_data WHERE path = ? LIMIT 1",
            (path,),
        ).fetchone()
        return row is not None
