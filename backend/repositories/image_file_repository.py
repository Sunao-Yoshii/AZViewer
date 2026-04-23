from __future__ import annotations

from math import ceil
from sqlite3 import Connection

from backend.models import ImageFileListItem, ImageFileRecord, SearchImageFilesResult


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

    def find_all_items(self) -> list[ImageFileListItem]:
        """登録済み画像ファイル情報を全件取得する。"""

        rows = self._connection.execute(
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
            ORDER BY id DESC
            """
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def delete_by_paths(self, paths: list[str]) -> list[int]:
        """指定されたパスに一致する画像ファイル情報を削除し、削除IDを返す。"""

        if not paths:
            return []

        record_ids = self.find_ids_by_paths(paths)

        self._connection.executemany(
            "DELETE FROM image_file_data WHERE path = ?",
            [(path,) for path in paths],
        )
        return record_ids

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

    def find_by_paths(self, paths: list[str]) -> list[ImageFileListItem]:
        """指定パス群に一致する画像ファイル情報を取得する。"""

        if not paths:
            return []

        placeholders = ", ".join("?" for _ in paths)
        rows = self._connection.execute(
            f"""
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
            WHERE path IN ({placeholders})
            """,
            paths,
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def find_ids_by_paths(self, paths: list[str]) -> list[int]:
        """指定パス群に一致するレコードID一覧を取得する。"""

        if not paths:
            return []

        placeholders = ", ".join("?" for _ in paths)
        rows = self._connection.execute(
            f"SELECT id FROM image_file_data WHERE path IN ({placeholders})",
            paths,
        ).fetchall()
        return [int(row["id"]) for row in rows]

    def search(
        self,
        *,
        path: str = "",
        rating: str | None = None,
        is_checked: bool | int | None = None,
        is_favorite: bool | int | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "id_desc",
    ) -> SearchImageFilesResult:
        """条件に一致する画像一覧をページング付きで取得する。"""

        safe_page = max(1, int(page))
        safe_page_size = max(1, int(page_size))
        where_clauses: list[str] = []
        params: list[object] = []

        normalized_path = path.strip()
        if normalized_path:
            where_clauses.append("path LIKE ?")
            params.append(f"%{normalized_path}%")

        if rating:
            where_clauses.append("rating = ?")
            params.append(rating)

        if self._normalize_true_condition(is_checked):
            where_clauses.append("is_checked = 1")

        if self._normalize_true_condition(is_favorite):
            where_clauses.append("is_favorite = 1")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        total_count = int(
            self._connection.execute(
                f"SELECT COUNT(*) AS count FROM image_file_data {where_sql}",
                params,
            ).fetchone()["count"]
        )
        total_pages = ceil(total_count / safe_page_size) if total_count > 0 else 0
        offset = (safe_page - 1) * safe_page_size
        order_sql = self._build_order_by(sort)
        rows = self._connection.execute(
            f"""
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
            {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_page_size, offset],
        ).fetchall()

        items = [self._row_to_item(row) for row in rows]
        return SearchImageFilesResult(
            items=items,
            total_count=total_count,
            total_pages=total_pages,
            page=safe_page,
            page_size=safe_page_size,
        )

    def update_flag(self, record_id: int, field: str, value: int) -> bool:
        """指定レコードのフラグ項目を更新する。"""

        if field not in {"is_checked", "is_favorite"}:
            raise ValueError("field must be 'is_checked' or 'is_favorite'.")
        if value not in {0, 1}:
            raise ValueError("value must be 0 or 1.")

        cursor = self._connection.execute(
            f"UPDATE image_file_data SET {field} = ? WHERE id = ?",
            (value, record_id),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def find_by_id(self, record_id: int) -> ImageFileListItem | None:
        """IDに一致する画像ファイル情報を取得する。"""

        row = self._connection.execute(
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
            WHERE id = ?
            LIMIT 1
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_item(row)

    def _row_to_item(self, row) -> ImageFileListItem:
        """SQLite行データを一覧表示用DTOへ変換する。"""

        return ImageFileListItem(
            id=int(row["id"]),
            filename=str(row["filename"]),
            path=str(row["path"]),
            folder=str(row["folder"]),
            rating=str(row["rating"]),
            is_checked=int(row["is_checked"]),
            is_favorite=int(row["is_favorite"]),
            comment=None if row["comment"] is None else str(row["comment"]),
        )

    def _build_order_by(self, sort: str) -> str:
        """許可済みソート値からORDER BY句を生成する。"""

        mapping = {
            "id_desc": "id DESC",
            "id_asc": "id ASC",
            "filename_asc": "filename COLLATE NOCASE ASC, id DESC",
            "filename_desc": "filename COLLATE NOCASE DESC, id DESC",
            "rating_asc": "rating ASC, id DESC",
            "rating_desc": "rating DESC, id DESC",
        }
        return mapping.get(sort, mapping["id_desc"])

    def _normalize_true_condition(self, value: bool | int | None) -> bool:
        """検索条件値をtrue条件として評価する。"""

        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return int(value) == 1
