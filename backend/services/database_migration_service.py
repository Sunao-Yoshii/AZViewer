from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine


class DatabaseMigrationService:
    """DBスキーマの起動時マイグレーションを担当する。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def migrate(self) -> None:
        """必要なスキーマ変更を適用する。"""

        with self._engine.connect() as conn:
            columns = self._fetch_image_file_columns(conn)
            if not columns:
                return

            has_folder = "folder" in columns
            has_folder_id = "folder_id" in columns
            if has_folder and not has_folder_id:
                self._migrate_image_folder_schema_atomic(conn)
                return
            if not has_folder and has_folder_id:
                self._ensure_folder_indexes(conn)
                self._ensure_tag_link_indexes(conn)
                conn.commit()
                return
            if has_folder and has_folder_id:
                raise RuntimeError("image_file_data has both folder and folder_id columns.")
            raise RuntimeError("image_file_data has neither folder nor folder_id columns.")

    def _fetch_image_file_columns(self, conn) -> set[str]:
        rows = conn.execute(text("PRAGMA table_info(image_file_data)")).mappings().all()
        return {str(row["name"]) for row in rows}

    def _migrate_image_folder_schema_atomic(self, conn) -> None:
        conn.commit()
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        conn.commit()
        transaction = conn.begin()
        try:
            self._migrate_image_folder_schema(conn)
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()

    def _migrate_image_folder_schema(self, conn) -> None:
        rows = self._fetch_old_image_file_rows(conn)
        self._create_image_folder_table(conn)
        folder_ids = self._create_folders(conn, rows)
        self._rebuild_image_file_data(conn, rows, folder_ids)
        self._ensure_folder_indexes(conn)
        self._ensure_tag_link_indexes(conn)

    def _fetch_old_image_file_rows(self, conn) -> list[dict[str, object]]:
        rows = conn.execute(
            text(
                """
                SELECT
                    id,
                    filename,
                    path,
                    folder,
                    rating,
                    is_checked,
                    is_favorite,
                    comment
                FROM image_file_data
                ORDER BY id ASC
                """
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    def _create_image_folder_table(self, conn) -> None:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS image_folder (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_path TEXT NOT NULL UNIQUE,
                    folder_name TEXT NOT NULL
                )
                """
            )
        )

    def _create_folders(self, conn, rows: list[dict[str, object]]) -> dict[str, int]:
        folder_ids: dict[str, int] = {}
        for row in rows:
            folder_path, folder_name = self._build_folder_identity(row["path"])
            if folder_path in folder_ids:
                continue

            conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO image_folder (
                        folder_path,
                        folder_name
                    )
                    VALUES (
                        :folder_path,
                        :folder_name
                    )
                    """
                ),
                {"folder_path": folder_path, "folder_name": folder_name},
            )
            folder_ids[folder_path] = self._fetch_folder_id(conn, folder_path)
        return folder_ids

    def _build_folder_identity(self, path: object) -> tuple[str, str]:
        folder = Path(str(path)).parent
        folder_path = str(folder)
        folder_name = folder.name
        if not folder_path or not folder_name:
            raise RuntimeError(f"Folder identity could not be built from path: {path}")
        return folder_path, folder_name

    def _fetch_folder_id(self, conn, folder_path: str) -> int:
        row = conn.execute(
            text(
                """
                SELECT id
                FROM image_folder
                WHERE folder_path = :folder_path
                LIMIT 1
                """
            ),
            {"folder_path": folder_path},
        ).mappings().first()
        if row is None:
            raise RuntimeError(f"Folder could not be created: {folder_path}")
        return int(row["id"])

    def _rebuild_image_file_data(
        self,
        conn,
        rows: list[dict[str, object]],
        folder_ids: dict[str, int],
    ) -> None:
        self._create_new_image_file_data(conn, "image_file_data_new")
        for row in rows:
            folder_path, _folder_name = self._build_folder_identity(row["path"])
            self._insert_migrated_image_file(conn, "image_file_data_new", row, folder_ids[folder_path])
        conn.execute(text("DROP TABLE image_file_data"))
        conn.execute(text("ALTER TABLE image_file_data_new RENAME TO image_file_data"))

    def _create_new_image_file_data(self, conn, table_name: str) -> None:
        conn.execute(
            text(
                f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    folder_id INTEGER NOT NULL,
                    rating TEXT NOT NULL CHECK (rating IN ('General', 'R-15', 'R-18', 'R-18G')),
                    is_checked INTEGER NOT NULL CHECK (is_checked IN (0, 1)),
                    is_favorite INTEGER NOT NULL CHECK (is_favorite IN (0, 1)),
                    comment TEXT NULL,
                    FOREIGN KEY (folder_id)
                        REFERENCES image_folder(id)
                        ON DELETE RESTRICT
                )
                """
            )
        )

    def _insert_migrated_image_file(
        self,
        conn,
        table_name: str,
        row: dict[str, object],
        folder_id: int,
    ) -> None:
        conn.execute(
            text(
                f"""
                INSERT INTO {table_name} (
                    id,
                    filename,
                    path,
                    folder_id,
                    rating,
                    is_checked,
                    is_favorite,
                    comment
                )
                VALUES (
                    :id,
                    :filename,
                    :path,
                    :folder_id,
                    :rating,
                    :is_checked,
                    :is_favorite,
                    :comment
                )
                """
            ),
            {
                "id": row["id"],
                "filename": row["filename"],
                "path": row["path"],
                "folder_id": folder_id,
                "rating": row["rating"],
                "is_checked": row["is_checked"],
                "is_favorite": row["is_favorite"],
                "comment": row["comment"],
            },
        )

    def _ensure_folder_indexes(self, conn) -> None:
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_image_folder_folder_name
                ON image_folder(folder_name)
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_image_file_data_folder_id
                ON image_file_data(folder_id)
                """
            )
        )

    def _ensure_tag_link_indexes(self, conn) -> None:
        if not self._table_exists(conn, "tag_image_link"):
            return

        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_tag_image_link_tag_id
                ON tag_image_link(tag_id)
                """
            )
        )

    def _table_exists(self, conn, table_name: str) -> bool:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = :table_name
                LIMIT 1
                """
            ),
            {"table_name": table_name},
        ).first()
        return row is not None
