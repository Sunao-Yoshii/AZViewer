from __future__ import annotations

import hashlib
from dataclasses import replace
from math import ceil
from typing import Iterable, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.models import (
    DuplicateTagSetItem,
    FolderListItem,
    ImageModelListItem,
    ImageFileListItem,
    ImageFileRecord,
    ImageFolderMaintenanceItem,
    ImageFolderReference,
    MasterBulkDeleteResult,
    MasterDeleteResult,
    MasterMaintenanceItem,
    MasterReplaceResult,
    SearchImageFilesResult,
    TagListItem,
)


class _QueryResult:
    """Repository 内の既存 fetch API と rowcount 利用を吸収する結果ラッパー。"""

    def __init__(
        self,
        *,
        rows: list[dict[str, object]] | None = None,
        rowcount: int = -1,
        lastrowid: int | None = None,
    ) -> None:
        self._rows = rows or []
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def fetchall(self) -> list[dict[str, object]]:
        return self._rows

    def fetchone(self) -> dict[str, object] | None:
        if not self._rows:
            return None
        return self._rows[0]


class _SqlAlchemyRepositoryConnection:
    """SQLAlchemy Engine の短命 Connection を既存 Repository API に寄せるアダプタ。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._active_connection = None
        self._active_transaction = None

    def execute(self, sql: str, params: object | None = None) -> _QueryResult:
        statement = sql.strip()
        upper_statement = statement.upper()
        if upper_statement == "BEGIN":
            self._begin()
            return _QueryResult(rowcount=0)

        translated_sql, translated_params = self._translate_parameters(sql, params)
        if self._active_connection is not None:
            return self._execute_on_connection(self._active_connection, translated_sql, translated_params)

        if self._is_read_statement(statement):
            with self._engine.connect() as conn:
                return self._execute_on_connection(conn, translated_sql, translated_params)

        with self._engine.begin() as conn:
            return self._execute_on_connection(conn, translated_sql, translated_params)

    def executemany(self, sql: str, params: Iterable[object]) -> _QueryResult:
        params_list = list(params)
        translated_sql, translated_params = self._translate_many_parameters(sql, params_list)
        if self._active_connection is not None:
            return self._execute_on_connection(self._active_connection, translated_sql, translated_params)

        with self._engine.begin() as conn:
            return self._execute_on_connection(conn, translated_sql, translated_params)

    def commit(self) -> None:
        if self._active_transaction is None:
            return

        transaction = self._active_transaction
        connection = self._active_connection
        self._active_transaction = None
        self._active_connection = None
        try:
            transaction.commit()
        finally:
            connection.close()

    def rollback(self) -> None:
        if self._active_transaction is None:
            return

        transaction = self._active_transaction
        connection = self._active_connection
        self._active_transaction = None
        self._active_connection = None
        try:
            transaction.rollback()
        finally:
            connection.close()

    def _begin(self) -> None:
        if self._active_transaction is not None:
            raise RuntimeError("Transaction is already active.")

        self._active_connection = self._engine.connect()
        self._active_transaction = self._active_connection.begin()

    def _execute_on_connection(self, connection, sql: str, params: object | None) -> _QueryResult:
        result = connection.execute(text(sql), params or {})
        rows = [dict(row) for row in result.mappings().all()] if result.returns_rows else []
        return _QueryResult(
            rows=rows,
            rowcount=result.rowcount,
            lastrowid=getattr(result, "lastrowid", None),
        )

    def _translate_parameters(self, sql: str, params: object | None) -> tuple[str, object | None]:
        if params is None or isinstance(params, dict):
            return sql, params

        values = self._to_sequence(params)
        return self._replace_qmark_parameters(sql, values)

    def _translate_many_parameters(self, sql: str, params: list[object]) -> tuple[str, list[dict[str, object]]]:
        if not params:
            return sql, []

        first = params[0]
        if isinstance(first, dict):
            return sql, [dict(item) for item in params if isinstance(item, dict)]

        translated_sql, translated_params = self._replace_qmark_parameters(sql, self._to_sequence(first))
        param_names = list(translated_params.keys())
        return translated_sql, [
            {name: value for name, value in zip(param_names, self._to_sequence(item), strict=True)}
            for item in params
        ]

    def _replace_qmark_parameters(self, sql: str, values: Sequence[object]) -> tuple[str, dict[str, object]]:
        translated_sql_parts: list[str] = []
        params: dict[str, object] = {}
        value_index = 0

        for character in sql:
            if character != "?":
                translated_sql_parts.append(character)
                continue
            param_name = f"p_{value_index}"
            translated_sql_parts.append(f":{param_name}")
            params[param_name] = values[value_index]
            value_index += 1

        if value_index != len(values):
            raise ValueError("SQL placeholder count does not match parameter count.")
        return "".join(translated_sql_parts), params

    def _to_sequence(self, params: object) -> Sequence[object]:
        if isinstance(params, Sequence) and not isinstance(params, (str, bytes, bytearray)):
            return params
        return (params,)

    def _is_read_statement(self, statement: str) -> bool:
        upper_statement = statement.upper()
        return upper_statement.startswith(("SELECT", "WITH", "PRAGMA"))


class ImageFileRepository:
    """画像ファイル情報を保存するSQLiteテーブルへのアクセスを担当する。"""

    _ALLOWED_PAGE_SIZES = {25, 50, 75, 100, 200, 500, 1000, 2500}
    _DEFAULT_PAGE_SIZE = 25

    def __init__(self, engine: Engine) -> None:
        """リポジトリで利用する SQLAlchemy Engine を保持する。"""

        self._engine = engine
        self._connection = _SqlAlchemyRepositoryConnection(engine)

    def create_table(self) -> None:
        """画像ファイル情報を保存するテーブルを作成する。"""

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS image_folder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_path TEXT NOT NULL UNIQUE,
                folder_name TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS image_file_data (
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
        self._create_folder_indexes()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                CHECK (length(name) <= 512)
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tag_image_link (
                image_file_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (image_file_id, tag_id),
                FOREIGN KEY (image_file_id)
                    REFERENCES image_file_data(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (tag_id)
                    REFERENCES tag(id)
                    ON DELETE CASCADE
            )
            """
        )
        self._create_tag_link_indexes()
        self._create_tag_hash_table()
        self._create_image_model_tables()
        self._connection.commit()

    def _create_folder_indexes(self) -> None:
        """フォルダ管理用テーブルのインデックスを作成する。"""

        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_image_folder_folder_name
            ON image_folder(folder_name)
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_image_file_data_folder_id
            ON image_file_data(folder_id)
            """
        )

    def _create_tag_link_indexes(self) -> None:
        """タグリンク検索用インデックスを作成する。"""

        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tag_image_link_tag_id
            ON tag_image_link(tag_id)
            """
        )

    def _create_tag_hash_table(self) -> None:
        """タグ構成検索用の派生インデックステーブルを作成する。"""

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tag_hash (
                image_file_data_id INTEGER PRIMARY KEY,
                tag_names TEXT NOT NULL,
                tag_set TEXT NOT NULL,
                hash TEXT NOT NULL,
                FOREIGN KEY (image_file_data_id)
                    REFERENCES image_file_data(id)
                    ON DELETE CASCADE
            )
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tag_hash_hash
            ON tag_hash(hash)
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tag_hash_hash_tag_set
            ON tag_hash(hash, tag_set)
            """
        )

    def _create_image_model_tables(self) -> None:
        """生成元モデル管理用テーブルとインデックスを作成する。"""

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS image_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                CHECK (length(name) <= 512)
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS image_model_to_file_data (
                image_file_data_id INTEGER NOT NULL,
                image_model_id INTEGER NOT NULL,
                PRIMARY KEY (image_file_data_id, image_model_id),
                UNIQUE (image_file_data_id),
                FOREIGN KEY (image_file_data_id)
                    REFERENCES image_file_data(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (image_model_id)
                    REFERENCES image_model(id)
                    ON DELETE CASCADE
            )
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_image_model_name
            ON image_model(name)
            """
        )
        self._connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_image_model_to_file_data_model_id
            ON image_model_to_file_data(image_model_id)
            """
        )

    def _image_file_select_sql(self, from_clause: str = "image_file") -> str:
        """画像一覧DTO用のSELECT句とJOIN句を返す。"""

        return f"""
            SELECT
                {from_clause}.id,
                {from_clause}.filename,
                {from_clause}.path,
                image_folder.folder_name AS folder,
                image_folder.id AS folder_id,
                image_folder.folder_path AS folder_path,
                {from_clause}.rating,
                {from_clause}.is_checked,
                {from_clause}.is_favorite,
                {from_clause}.comment
            FROM image_file_data {from_clause}
            INNER JOIN image_folder
                ON image_folder.id = {from_clause}.folder_id
        """

    def find_all_paths(self) -> list[str]:
        """登録済み画像ファイルのパス一覧を取得する。"""

        rows = self._connection.execute("SELECT path FROM image_file_data").fetchall()
        return [str(row["path"]) for row in rows]

    def find_all_items(self) -> list[ImageFileListItem]:
        """登録済み画像ファイル情報を全件取得する。"""

        rows = self._connection.execute(
            f"""
            {self._image_file_select_sql()}
            ORDER BY image_file.id DESC
            """
        ).fetchall()
        return self._attach_related_data([self._row_to_item(row) for row in rows])

    def find_items_without_tags(self) -> list[ImageFileListItem]:
        """タグが1件も紐づいていない画像ファイル情報を取得する。"""

        rows = self._connection.execute(
            f"""
            {self._image_file_select_sql()}
            WHERE NOT EXISTS (
                SELECT 1
                FROM tag_image_link tag_link
                WHERE tag_link.image_file_id = image_file.id
            )
            ORDER BY image_file.id ASC
            """
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def find_items_without_model(self) -> list[ImageFileListItem]:
        """生成元モデルが紐づいていない画像ファイル情報を取得する。"""

        rows = self._connection.execute(
            f"""
            {self._image_file_select_sql()}
            WHERE NOT EXISTS (
                SELECT 1
                FROM image_model_to_file_data model_link
                WHERE model_link.image_file_data_id = image_file.id
            )
            ORDER BY image_file.id ASC
            """
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def delete_by_paths(self, paths: list[str]) -> list[int]:
        """指定されたパスに一致する画像ファイル情報を削除し、削除IDを返す。"""

        if not paths:
            return []

        record_ids = self.find_ids_by_paths(paths)
        try:
            self._connection.execute("BEGIN")
            self.delete_tag_hashes(record_ids)
            self._connection.executemany(
                "DELETE FROM image_file_data WHERE path = ?",
                [(path,) for path in paths],
            )
            self._connection.commit()
            return record_ids
        except Exception:
            self._connection.rollback()
            raise

    def insert_many(self, records: list[ImageFileRecord]) -> None:
        """複数の画像ファイル情報を一括登録する。"""

        if not records:
            return

        try:
            self._connection.execute("BEGIN")
            for record in records:
                folder_id = self.find_or_create_image_folder(
                    record.folder_path,
                    record.folder_name,
                )
                self._connection.execute(
                    """
                    INSERT INTO image_file_data (
                        filename,
                        path,
                        folder_id,
                        rating,
                        is_checked,
                        is_favorite,
                        comment
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.filename,
                        record.path,
                        folder_id,
                        record.rating,
                        record.is_checked,
                        record.is_favorite,
                        record.comment,
                    ),
                )
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def find_or_create_image_folder(self, folder_path: str, folder_name: str) -> int:
        """フォルダパスに対応するIDを取得し、未登録の場合は作成する。"""

        normalized_path = str(folder_path or "").strip()
        normalized_name = str(folder_name or "").strip()
        if not normalized_path:
            raise ValueError("folder_path is required.")
        if not normalized_name:
            raise ValueError("folder_name is required.")

        self._connection.execute(
            """
            INSERT OR IGNORE INTO image_folder (
                folder_path,
                folder_name
            )
            VALUES (?, ?)
            """,
            (normalized_path, normalized_name),
        )
        row = self._connection.execute(
            """
            SELECT id
            FROM image_folder
            WHERE folder_path = ?
            LIMIT 1
            """,
            (normalized_path,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Image folder could not be created: {normalized_path}")
        return int(row["id"])

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
            {self._image_file_select_sql()}
            WHERE image_file.path IN ({placeholders})
            """,
            paths,
        ).fetchall()
        return self._attach_related_data([self._row_to_item(row) for row in rows])

    def find_by_ids(self, record_ids: list[int]) -> list[ImageFileListItem]:
        """指定ID群に一致する画像ファイル情報を取得する。"""

        if not record_ids:
            return []

        placeholders = ", ".join("?" for _ in record_ids)
        rows = self._connection.execute(
            f"""
            {self._image_file_select_sql()}
            WHERE image_file.id IN ({placeholders})
            ORDER BY image_file.id ASC
            """,
            record_ids,
        ).fetchall()
        return self._attach_related_data([self._row_to_item(row) for row in rows])

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
        tags: list[str] | None = None,
        folder_id: int | None = None,
        model: str | None = None,
        tag_hash: str | None = None,
        tag_set: str | None = None,
        tag_keyword: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "id_desc",
    ) -> SearchImageFilesResult:
        """条件に一致する画像一覧をページング付きで取得する。"""

        safe_page = self._normalize_page(page)
        safe_page_size = self._normalize_page_size(page_size)
        where_clauses, params = self._build_search_conditions(
            path=path,
            rating=rating,
            is_checked=is_checked,
            is_favorite=is_favorite,
            tags=tags,
            folder_id=folder_id,
            model=model,
            tag_hash=tag_hash,
            tag_set=tag_set,
            tag_keyword=tag_keyword,
        )
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        total_count = int(
            self._connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM image_file_data image_file
                {where_sql}
                """,
                params,
            ).fetchone()["count"]
        )
        total_pages = ceil(total_count / safe_page_size) if total_count > 0 else 0
        offset = (safe_page - 1) * safe_page_size
        order_sql = self._build_order_by(sort)
        rows = self._connection.execute(
            f"""
            {self._image_file_select_sql()}
            {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_page_size, offset],
        ).fetchall()

        items = [self._row_to_item(row) for row in rows]
        items = self._attach_related_data(items)
        return SearchImageFilesResult(
            items=items,
            total_count=total_count,
            total_pages=total_pages,
            page=safe_page,
            page_size=safe_page_size,
        )

    def find_tags_for_search(self, keyword: str | None = None, limit: int = 256) -> list[TagListItem]:
        """タグ検索候補をID昇順で取得する。"""

        params = self._build_tag_search_params(keyword, limit)
        rows = self._connection.execute(
            """
            SELECT
                id,
                name
            FROM tag
            WHERE (:keyword = '' OR name LIKE :keyword_like)
            ORDER BY id ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [
            TagListItem(id=int(row["id"]), name=str(row["name"]))
            for row in rows
        ]

    def count_tags_for_search(self, keyword: str | None = None) -> int:
        """タグ検索候補の条件一致総数を取得する。"""

        params = self._build_tag_search_params(keyword, 1)
        return int(
            self._connection.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM tag
                WHERE (:keyword = '' OR name LIKE :keyword_like)
                """,
                params,
            ).fetchone()["count"]
        )

    def find_folders_for_search(self, keyword: str | None = None, limit: int = 256) -> list[FolderListItem]:
        """フォルダ検索候補を登録順相当で取得する。"""

        params = self._build_folder_search_params(keyword, limit)
        rows = self._connection.execute(
            """
            SELECT
                image_folder.id,
                image_folder.folder_name AS name,
                image_folder.folder_path AS path,
                COUNT(image_file.id) AS image_count,
                MIN(image_file.id) AS first_id
            FROM image_folder
            INNER JOIN image_file_data image_file
                ON image_file.folder_id = image_folder.id
            WHERE (
                :keyword = ''
                OR image_folder.folder_name LIKE :keyword_like
                OR image_folder.folder_path LIKE :keyword_like
            )
            GROUP BY
                image_folder.id,
                image_folder.folder_name,
                image_folder.folder_path
            ORDER BY first_id ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [
            FolderListItem(
                id=int(row["id"]),
                name=str(row["name"]),
                path=str(row["path"]),
                image_count=int(row["image_count"]),
            )
            for row in rows
        ]

    def count_folders_for_search(self, keyword: str | None = None) -> int:
        """フォルダ検索候補の条件一致総数を取得する。"""

        params = self._build_folder_search_params(keyword, 1)
        return int(
            self._connection.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM image_folder
                WHERE EXISTS (
                    SELECT 1
                    FROM image_file_data image_file
                    WHERE image_file.folder_id = image_folder.id
                )
                  AND (
                    :keyword = ''
                    OR image_folder.folder_name LIKE :keyword_like
                    OR image_folder.folder_path LIKE :keyword_like
                  )
                """,
                params,
            ).fetchone()["count"]
        )

    def find_models_for_search(self, keyword: str | None = None, limit: int = 256) -> list[ImageModelListItem]:
        """モデル検索候補を登録順相当で取得する。"""

        params = self._build_model_search_params(keyword, limit)
        rows = self._connection.execute(
            """
            SELECT
                image_model.name AS name,
                COUNT(model_link.image_file_data_id) AS image_count,
                MIN(model_link.image_file_data_id) AS first_id
            FROM image_model
            INNER JOIN image_model_to_file_data model_link
                ON model_link.image_model_id = image_model.id
            WHERE (:keyword = '' OR image_model.name LIKE :keyword_like)
            GROUP BY image_model.id, image_model.name
            ORDER BY first_id ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [
            ImageModelListItem(name=str(row["name"]), image_count=int(row["image_count"]))
            for row in rows
        ]

    def count_models_for_search(self, keyword: str | None = None) -> int:
        """モデル検索候補の条件一致総数を取得する。"""

        params = self._build_model_search_params(keyword, 1)
        return int(
            self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM image_model
                WHERE (:keyword = '' OR name LIKE :keyword_like)
                  AND EXISTS (
                    SELECT 1
                    FROM image_model_to_file_data model_link
                    WHERE model_link.image_model_id = image_model.id
                  )
                """,
                params,
            ).fetchone()["count"]
        )

    def find_tags_for_maintenance(
        self,
        keyword: str | None = None,
        limit: int = 50,
    ) -> list[MasterMaintenanceItem]:
        """タグメンテナンス候補を使用件数付きで取得する。"""

        params = self._build_tag_search_params(keyword, limit)
        rows = self._connection.execute(
            """
            SELECT
                tag.id,
                tag.name,
                COUNT(tag_link.image_file_id) AS image_count
            FROM tag
            LEFT JOIN tag_image_link tag_link
                ON tag_link.tag_id = tag.id
            WHERE (:keyword = '' OR tag.name LIKE :keyword_like)
            GROUP BY tag.id, tag.name
            ORDER BY tag.id ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [self._row_to_master_maintenance_item(row) for row in rows]

    def count_tags_for_maintenance(self, keyword: str | None = None) -> int:
        """タグメンテナンス候補の条件一致総数を取得する。"""

        params = self._build_tag_search_params(keyword, 1)
        return int(
            self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM tag
                WHERE (:keyword = '' OR name LIKE :keyword_like)
                """,
                params,
            ).fetchone()["count"]
        )

    def find_models_for_maintenance(
        self,
        keyword: str | None = None,
        limit: int = 50,
    ) -> list[MasterMaintenanceItem]:
        """モデルメンテナンス候補を使用件数付きで取得する。"""

        params = self._build_model_search_params(keyword, limit)
        rows = self._connection.execute(
            """
            SELECT
                image_model.id,
                image_model.name,
                COUNT(model_link.image_file_data_id) AS image_count
            FROM image_model
            LEFT JOIN image_model_to_file_data model_link
                ON model_link.image_model_id = image_model.id
            WHERE (:keyword = '' OR image_model.name LIKE :keyword_like)
            GROUP BY image_model.id, image_model.name
            ORDER BY image_model.id ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [self._row_to_master_maintenance_item(row) for row in rows]

    def count_models_for_maintenance(self, keyword: str | None = None) -> int:
        """モデルメンテナンス候補の条件一致総数を取得する。"""

        params = self._build_model_search_params(keyword, 1)
        return int(
            self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM image_model
                WHERE (:keyword = '' OR name LIKE :keyword_like)
                """,
                params,
            ).fetchone()["count"]
        )

    def find_folders_for_maintenance(
        self,
        keyword: str | None = None,
        limit: int = 50,
    ) -> list[ImageFolderMaintenanceItem]:
        """フォルダメンテナンス候補を使用件数付きで取得する。"""

        params = self._build_folder_search_params(keyword, limit)
        rows = self._connection.execute(
            """
            SELECT
                image_folder.id,
                image_folder.folder_name AS name,
                image_folder.folder_path AS path,
                COUNT(image_file.id) AS image_count
            FROM image_folder
            LEFT JOIN image_file_data image_file
                ON image_file.folder_id = image_folder.id
            WHERE (
                :keyword = ''
                OR image_folder.folder_name LIKE :keyword_like
                OR image_folder.folder_path LIKE :keyword_like
            )
            GROUP BY
                image_folder.id,
                image_folder.folder_name,
                image_folder.folder_path
            ORDER BY image_folder.folder_path ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [
            ImageFolderMaintenanceItem(
                id=int(row["id"]),
                name=str(row["name"]),
                path=str(row["path"]),
                image_count=int(row["image_count"]),
            )
            for row in rows
        ]

    def count_folders_for_maintenance(self, keyword: str | None = None) -> int:
        """フォルダメンテナンス候補の条件一致総数を取得する。"""

        params = self._build_folder_search_params(keyword, 1)
        return int(
            self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM image_folder
                WHERE (
                    :keyword = ''
                    OR folder_name LIKE :keyword_like
                    OR folder_path LIKE :keyword_like
                )
                """,
                params,
            ).fetchone()["count"]
        )

    def delete_unused_folders(self) -> MasterBulkDeleteResult:
        """画像から参照されていないフォルダマスタを一括削除する。"""

        try:
            self._connection.execute("BEGIN")
            cursor = self._connection.execute(
                """
                DELETE FROM image_folder
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM image_file_data image_file
                    WHERE image_file.folder_id = image_folder.id
                )
                """
            )
            self._connection.commit()
            return MasterBulkDeleteResult(deleted_count=cursor.rowcount)
        except Exception:
            self._connection.rollback()
            raise

    def find_image_ids_by_folder_id(self, folder_id: int) -> list[int]:
        """フォルダIDに紐づく画像ID一覧を取得する。"""

        rows = self._connection.execute(
            """
            SELECT id
            FROM image_file_data
            WHERE folder_id = ?
            ORDER BY id ASC
            """,
            (folder_id,),
        ).fetchall()
        return [int(row["id"]) for row in rows]

    def find_folder_by_id(self, folder_id: int) -> ImageFolderReference | None:
        """IDに一致するフォルダ定義を取得する。"""

        row = self._connection.execute(
            """
            SELECT
                id,
                folder_name,
                folder_path
            FROM image_folder
            WHERE id = ?
            LIMIT 1
            """,
            (folder_id,),
        ).fetchone()
        if row is None:
            return None
        return ImageFolderReference(
            id=int(row["id"]),
            name=str(row["folder_name"]),
            path=str(row["folder_path"]),
        )

    def delete_tag_master(self, tag_id: int) -> MasterDeleteResult:
        """タグマスタを削除し、影響画像のtag_hashを再同期する。"""

        try:
            self._connection.execute("BEGIN")
            tag = self._find_tag_by_id(tag_id)
            if tag is None:
                raise ValueError("削除対象のタグが存在しません。")

            image_ids = self._find_image_ids_by_tag_id(tag_id)
            self._connection.execute(
                "DELETE FROM tag_image_link WHERE tag_id = ?",
                (tag_id,),
            )
            cursor = self._connection.execute(
                "DELETE FROM tag WHERE id = ?",
                (tag_id,),
            )
            self._replace_tag_hashes(image_ids)
            self._connection.commit()
            return MasterDeleteResult(
                id=tag_id,
                name=str(tag["name"]),
                affected_image_count=len(image_ids),
                deleted_count=cursor.rowcount,
            )
        except Exception:
            self._connection.rollback()
            raise

    def replace_tag_master(self, tag_id: int, new_name: str) -> MasterReplaceResult:
        """タグマスタ名を変更または既存タグへ統合する。"""

        try:
            self._connection.execute("BEGIN")
            source = self._find_tag_by_id(tag_id)
            if source is None:
                raise ValueError("置き換え対象のタグが存在しません。")
            if str(source["name"]) == new_name:
                raise ValueError("同じタグ名には置き換えできません。")

            image_ids = self._find_image_ids_by_tag_id(tag_id)
            target = self._find_tag_by_name(new_name)
            result = self._replace_or_merge_tag(tag_id, source, target, new_name, image_ids)
            self._replace_tag_hashes(image_ids)
            self._connection.commit()
            return result
        except Exception:
            self._connection.rollback()
            raise

    def delete_unused_tags(self) -> MasterBulkDeleteResult:
        """使用されていないタグマスタを一括削除する。"""

        try:
            self._connection.execute("BEGIN")
            cursor = self._connection.execute(
                """
                DELETE FROM tag
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM tag_image_link tag_link
                    WHERE tag_link.tag_id = tag.id
                )
                """
            )
            self._connection.commit()
            return MasterBulkDeleteResult(deleted_count=cursor.rowcount)
        except Exception:
            self._connection.rollback()
            raise

    def delete_model_master(self, model_id: int) -> MasterDeleteResult:
        """モデルマスタを削除し、画像とのリンクを解除する。"""

        try:
            self._connection.execute("BEGIN")
            model = self._find_model_by_id(model_id)
            if model is None:
                raise ValueError("削除対象のモデルが存在しません。")

            image_ids = self._find_image_ids_by_model_id(model_id)
            self._connection.execute(
                "DELETE FROM image_model_to_file_data WHERE image_model_id = ?",
                (model_id,),
            )
            cursor = self._connection.execute(
                "DELETE FROM image_model WHERE id = ?",
                (model_id,),
            )
            self._connection.commit()
            return MasterDeleteResult(
                id=model_id,
                name=str(model["name"]),
                affected_image_count=len(image_ids),
                deleted_count=cursor.rowcount,
            )
        except Exception:
            self._connection.rollback()
            raise

    def replace_model_master(self, model_id: int, new_name: str) -> MasterReplaceResult:
        """モデルマスタ名を変更または既存モデルへ統合する。"""

        try:
            self._connection.execute("BEGIN")
            source = self._find_model_by_id(model_id)
            if source is None:
                raise ValueError("置き換え対象のモデルが存在しません。")
            if str(source["name"]) == new_name:
                raise ValueError("同じモデル名には置き換えできません。")

            image_ids = self._find_image_ids_by_model_id(model_id)
            target = self._find_model_by_name(new_name)
            result = self._replace_or_merge_model(model_id, source, target, new_name, image_ids)
            self._connection.commit()
            return result
        except Exception:
            self._connection.rollback()
            raise

    def delete_unused_models(self) -> MasterBulkDeleteResult:
        """使用されていないモデルマスタを一括削除する。"""

        try:
            self._connection.execute("BEGIN")
            cursor = self._connection.execute(
                """
                DELETE FROM image_model
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM image_model_to_file_data model_link
                    WHERE model_link.image_model_id = image_model.id
                )
                """
            )
            self._connection.commit()
            return MasterBulkDeleteResult(deleted_count=cursor.rowcount)
        except Exception:
            self._connection.rollback()
            raise

    def remove_from_catalog_by_ids(self, record_ids: list[int]) -> int:
        """指定ID群を画像カタログの管理対象から除外する。"""

        if not record_ids:
            return 0

        placeholders = ", ".join("?" for _ in record_ids)
        try:
            self._connection.execute("BEGIN")
            self._connection.execute(
                f"DELETE FROM tag_image_link WHERE image_file_id IN ({placeholders})",
                record_ids,
            )
            self._connection.execute(
                f"DELETE FROM image_model_to_file_data WHERE image_file_data_id IN ({placeholders})",
                record_ids,
            )
            self._connection.execute(
                f"DELETE FROM tag_hash WHERE image_file_data_id IN ({placeholders})",
                record_ids,
            )
            cursor = self._connection.execute(
                f"DELETE FROM image_file_data WHERE id IN ({placeholders})",
                record_ids,
            )
            self._connection.commit()
            return cursor.rowcount
        except Exception:
            self._connection.rollback()
            raise

    def update_paths(self, updates: list[dict[str, object]]) -> int:
        """指定ID群のファイル識別情報を更新し、更新件数を返す。"""

        if not updates:
            return 0

        try:
            self._connection.execute("BEGIN")
            updated_count = 0
            for update in updates:
                folder_id = self.find_or_create_image_folder(
                    str(update.get("folder_path") or ""),
                    str(update.get("folder_name") or ""),
                )
                cursor = self._connection.execute(
                    """
                    UPDATE image_file_data
                    SET
                        filename = :filename,
                        path = :path,
                        folder_id = :folder_id
                    WHERE id = :id
                    """,
                    {
                        "id": update["id"],
                        "filename": update["filename"],
                        "path": update["path"],
                        "folder_id": folder_id,
                    },
                )
                updated_count += cursor.rowcount
            if updated_count != len(updates):
                raise RuntimeError("Some image file paths could not be updated.")
            self._connection.commit()
            return updated_count
        except Exception:
            self._connection.rollback()
            raise

    def update_file_identity(self, record_id: int, filename: str, path: str) -> int:
        """指定IDのファイル名とパスを更新する。"""

        try:
            self._connection.execute("BEGIN")
            cursor = self._connection.execute(
                """
                UPDATE image_file_data
                SET
                    filename = ?,
                    path = ?
                WHERE id = ?
                """,
                (filename, path, record_id),
            )
            self._connection.commit()
            return cursor.rowcount
        except Exception:
            self._connection.rollback()
            raise

    def bulk_update_attributes(self, record_ids: list[int], updates: dict | None) -> int:
        """指定ID群の許可された属性だけを一括更新し、更新件数を返す。"""

        if not record_ids:
            return 0

        update_values = self._filter_bulk_attribute_updates(updates)
        if not update_values:
            return 0

        set_clauses, params = self._build_bulk_attribute_update_params(
            record_ids,
            update_values,
        )
        id_placeholders = ", ".join(f":id_{index}" for index in range(len(record_ids)))
        sql = f"""
            UPDATE image_file_data
            SET {", ".join(set_clauses)}
            WHERE id IN ({id_placeholders})
        """

        try:
            self._connection.execute("BEGIN")
            cursor = self._connection.execute(sql, params)
            updated_count = cursor.rowcount
            self._connection.commit()
            return updated_count
        except Exception:
            self._connection.rollback()
            raise

    def update_detail(
        self,
        record_id: int,
        rating: str,
        is_checked: int,
        is_favorite: int,
        comment: str | None,
        *,
        commit: bool = True,
    ) -> bool:
        """指定レコードの詳細項目を一括更新する。"""

        self._validate_detail_values(rating, is_checked, is_favorite)
        try:
            if commit:
                self._connection.execute("BEGIN")
            cursor = self._connection.execute(
                """
                UPDATE image_file_data
                SET
                    rating = ?,
                    is_checked = ?,
                    is_favorite = ?,
                    comment = ?
                WHERE id = ?
                """,
                (rating, is_checked, is_favorite, comment, record_id),
            )
            if commit:
                self._connection.commit()
            return cursor.rowcount > 0
        except Exception:
            if commit:
                self._connection.rollback()
            raise

    def update_detail_with_tags_and_model(
        self,
        detail: dict[str, object],
        tags: list[str],
        model_name: str | None,
    ) -> bool:
        """詳細項目、タグリンク、モデルリンクを1トランザクションで更新する。"""

        try:
            self._connection.execute("BEGIN")
            updated = self.update_detail(**detail, commit=False)
            if not updated:
                self._connection.rollback()
                return False
            record_id = int(detail["record_id"])
            self.replace_tags(record_id, tags)
            self.replace_image_model(record_id, model_name)
            self._connection.commit()
            return True
        except Exception:
            self._connection.rollback()
            raise

    def find_tags_by_image_ids(self, image_ids: list[int]) -> dict[int, list[str]]:
        """画像ID群に紐づくタグ一覧をまとめて取得する。"""

        if not image_ids:
            return {}

        placeholders = ", ".join("?" for _ in image_ids)
        rows = self._connection.execute(
            f"""
            SELECT
                tag_image_link.image_file_id,
                tag.id,
                tag.name
            FROM tag_image_link
            INNER JOIN tag ON tag.id = tag_image_link.tag_id
            WHERE tag_image_link.image_file_id IN ({placeholders})
            ORDER BY tag_image_link.image_file_id ASC, tag.id ASC
            """,
            image_ids,
        ).fetchall()

        tags_by_image_id = {image_id: [] for image_id in image_ids}
        for row in rows:
            tags_by_image_id[int(row["image_file_id"])].append(str(row["name"]))
        return tags_by_image_id

    def replace_tags(self, image_file_id: int, tags: list[str]) -> None:
        """指定画像に紐づくタグリンクを置換する。"""

        self._connection.execute(
            "DELETE FROM tag_image_link WHERE image_file_id = ?",
            (image_file_id,),
        )
        for tag_name in tags:
            tag_id = self._find_or_create_tag_id(tag_name)
            self._connection.execute(
                """
                INSERT OR IGNORE INTO tag_image_link (image_file_id, tag_id)
                VALUES (?, ?)
                """,
                (image_file_id, tag_id),
            )
        self.replace_tag_hash(image_file_id)

    def replace_tags_atomic(self, image_file_id: int, tags: list[str]) -> None:
        """指定画像のタグリンク置換を1トランザクションで完結させる。"""

        try:
            self._connection.execute("BEGIN")
            self.replace_tags(image_file_id, tags)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def merge_tags_atomic(self, image_file_id: int, tags: list[str]) -> bool:
        """既存タグを保持して指定タグを追加し、変更有無を返す。"""

        try:
            self._connection.execute("BEGIN")
            existing_tags = self.find_tags_by_image_ids([image_file_id]).get(image_file_id, [])
            merged_tags = self._merge_tag_names(existing_tags, tags)
            if merged_tags == existing_tags:
                self._connection.rollback()
                return False

            self.replace_tags(image_file_id, merged_tags)
            self._connection.commit()
            return True
        except Exception:
            self._connection.rollback()
            raise

    def find_by_id(self, record_id: int) -> ImageFileListItem | None:
        """IDに一致する画像ファイル情報を取得する。"""

        row = self._connection.execute(
            f"""
            {self._image_file_select_sql()}
            WHERE image_file.id = ?
            LIMIT 1
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        item = self._row_to_item(row)
        return self._attach_related_data([item])[0]

    def find_or_create_image_model_id(self, name: str) -> int:
        """モデル名に対応するIDを取得し、未登録の場合は作成する。"""

        self._connection.execute(
            "INSERT OR IGNORE INTO image_model (name) VALUES (?)",
            (name,),
        )
        row = self._connection.execute(
            "SELECT id FROM image_model WHERE name = ? LIMIT 1",
            (name,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Image model could not be created: {name}")
        return int(row["id"])

    def replace_image_model(self, image_file_data_id: int, model_name: str | None) -> None:
        """指定画像に紐づく生成元モデルリンクを置換する。"""

        self._connection.execute(
            "DELETE FROM image_model_to_file_data WHERE image_file_data_id = ?",
            (image_file_data_id,),
        )
        normalized_name = str(model_name or "").strip()
        if not normalized_name:
            return

        model_id = self.find_or_create_image_model_id(normalized_name)
        self._connection.execute(
            """
            INSERT INTO image_model_to_file_data (
                image_file_data_id,
                image_model_id
            )
            VALUES (?, ?)
            """,
            (image_file_data_id, model_id),
        )

    def replace_image_model_atomic(self, image_file_data_id: int, model_name: str | None) -> None:
        """指定画像のモデルリンク置換を1トランザクションで完結させる。"""

        try:
            self._connection.execute("BEGIN")
            self.replace_image_model(image_file_data_id, model_name)
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def replace_tag_hash(self, image_file_id: int) -> None:
        """指定画像の現在のタグ構成からtag_hashを更新する。"""

        rows = self._connection.execute(
            """
            SELECT
                tag.id,
                tag.name
            FROM tag_image_link
            INNER JOIN tag ON tag.id = tag_image_link.tag_id
            WHERE tag_image_link.image_file_id = ?
            ORDER BY tag.id ASC
            """,
            (image_file_id,),
        ).fetchall()
        if not rows:
            self.delete_tag_hash(image_file_id)
            return

        tag_set = ",".join(str(int(row["id"])) for row in rows)
        tag_names = ",".join(str(row["name"]) for row in rows)
        self._connection.execute(
            """
            INSERT INTO tag_hash (
                image_file_data_id,
                tag_names,
                tag_set,
                hash
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(image_file_data_id)
            DO UPDATE SET
                tag_names = excluded.tag_names,
                tag_set = excluded.tag_set,
                hash = excluded.hash
            """,
            (image_file_id, tag_names, tag_set, self._build_tag_hash_value(tag_set)),
        )

    def delete_tag_hash(self, image_file_id: int) -> None:
        """指定画像のtag_hashを削除する。"""

        self._connection.execute(
            "DELETE FROM tag_hash WHERE image_file_data_id = ?",
            (image_file_id,),
        )

    def delete_tag_hashes(self, image_file_ids: list[int]) -> None:
        """指定画像群のtag_hashを削除する。"""

        if not image_file_ids:
            return

        placeholders = ", ".join("?" for _ in image_file_ids)
        self._connection.execute(
            f"DELETE FROM tag_hash WHERE image_file_data_id IN ({placeholders})",
            image_file_ids,
        )

    def count_tag_hashes(self) -> int:
        """tag_hashの件数を返す。"""

        return int(
            self._connection.execute(
                "SELECT COUNT(*) AS count FROM tag_hash"
            ).fetchone()["count"]
        )

    def rebuild_all_tag_hashes(self) -> int:
        """既存タグリンクからtag_hashを全件再構築し、作成件数を返す。"""

        try:
            self._connection.execute("BEGIN")
            self._connection.execute("DELETE FROM tag_hash")
            rows = self._connection.execute(
                """
                SELECT DISTINCT image_file_id
                FROM tag_image_link
                ORDER BY image_file_id ASC
                """
            ).fetchall()
            for row in rows:
                self.replace_tag_hash(int(row["image_file_id"]))
            self._connection.commit()
            return len(rows)
        except Exception:
            self._connection.rollback()
            raise

    def ensure_tag_hashes_if_empty(self) -> int:
        """tag_hashが空の場合だけ全件再構築し、再構築件数を返す。"""

        if self.count_tag_hashes() > 0:
            return 0
        return self.rebuild_all_tag_hashes()

    def find_duplicate_tag_sets(self, limit: int = 256) -> list[DuplicateTagSetItem]:
        """重複しているタグ構成を画像件数の多い順で取得する。"""

        rows = self._connection.execute(
            """
            SELECT
                hash,
                tag_set,
                tag_names,
                COUNT(*) AS image_count
            FROM tag_hash
            GROUP BY
                hash,
                tag_set,
                tag_names
            HAVING COUNT(*) >= 2
            ORDER BY
                image_count DESC,
                tag_names ASC
            LIMIT :limit
            """,
            {"limit": max(1, min(int(limit), 256))},
        ).fetchall()
        return [
            DuplicateTagSetItem(
                hash=str(row["hash"]),
                tag_set=str(row["tag_set"]),
                tag_names=str(row["tag_names"]),
                image_count=int(row["image_count"]),
            )
            for row in rows
        ]

    def count_duplicate_tag_sets(self) -> int:
        """重複タグ構成の総件数を返す。"""

        return int(
            self._connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM (
                    SELECT
                        hash,
                        tag_set
                    FROM tag_hash
                    GROUP BY
                        hash,
                        tag_set
                    HAVING COUNT(*) >= 2
                ) duplicate_sets
                """
            ).fetchone()["count"]
        )

    def _row_to_item(self, row) -> ImageFileListItem:
        """SQLite行データを一覧表示用DTOへ変換する。"""

        return ImageFileListItem(
            id=int(row["id"]),
            filename=str(row["filename"]),
            path=str(row["path"]),
            folder=str(row["folder"]),
            folder_id=int(row["folder_id"]),
            folder_path=str(row["folder_path"]),
            rating=str(row["rating"]),
            is_checked=int(row["is_checked"]),
            is_favorite=int(row["is_favorite"]),
            comment=None if row["comment"] is None else str(row["comment"]),
            tags=[],
        )

    def _row_to_master_maintenance_item(self, row) -> MasterMaintenanceItem:
        """SQLite行データをマスタメンテナンス候補DTOへ変換する。"""

        return MasterMaintenanceItem(
            id=int(row["id"]),
            name=str(row["name"]),
            image_count=int(row["image_count"]),
        )

    def _attach_tags(self, items: list[ImageFileListItem]) -> list[ImageFileListItem]:
        """一覧項目群へタグ情報をまとめて付与する。"""

        tags_by_image_id = self.find_tags_by_image_ids([item.id for item in items])
        return [
            replace(item, tags=tags_by_image_id.get(item.id, []))
            for item in items
        ]

    def _attach_related_data(self, items: list[ImageFileListItem]) -> list[ImageFileListItem]:
        """一覧項目群へタグとモデル名をまとめて付与する。"""

        return self._attach_model_names(self._attach_tags(items))

    def _attach_model_names(self, items: list[ImageFileListItem]) -> list[ImageFileListItem]:
        """一覧項目群へ生成元モデル名をまとめて付与する。"""

        if not items:
            return items

        image_ids = [item.id for item in items]
        placeholders = ", ".join("?" for _ in image_ids)
        rows = self._connection.execute(
            f"""
            SELECT
                model_link.image_file_data_id,
                image_model.name
            FROM image_model_to_file_data model_link
            INNER JOIN image_model
                ON image_model.id = model_link.image_model_id
            WHERE model_link.image_file_data_id IN ({placeholders})
            """,
            image_ids,
        ).fetchall()
        models_by_image_id = {
            int(row["image_file_data_id"]): str(row["name"])
            for row in rows
        }
        return [
            replace(item, model_name=models_by_image_id.get(item.id))
            for item in items
        ]

    def _find_or_create_tag_id(self, tag_name: str) -> int:
        """タグ名に対応するIDを取得し、未登録の場合は作成する。"""

        self._connection.execute(
            "INSERT OR IGNORE INTO tag (name) VALUES (?)",
            (tag_name,),
        )
        row = self._connection.execute(
            "SELECT id FROM tag WHERE name = ? LIMIT 1",
            (tag_name,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Tag could not be created: {tag_name}")
        return int(row["id"])

    def _merge_tag_names(self, existing_tags: list[str], tags: list[str]) -> list[str]:
        """既存順を保ったまま追加タグを統合する。"""

        merged_tags: list[str] = []
        seen: set[str] = set()
        for tag in [*existing_tags, *tags]:
            if tag in seen:
                continue
            seen.add(tag)
            merged_tags.append(tag)
        return merged_tags

    def _find_tag_by_id(self, tag_id: int):
        """IDに一致するタグ行を取得する。"""

        return self._connection.execute(
            "SELECT id, name FROM tag WHERE id = ? LIMIT 1",
            (tag_id,),
        ).fetchone()

    def _find_tag_by_name(self, name: str):
        """名前に一致するタグ行を取得する。"""

        return self._connection.execute(
            "SELECT id, name FROM tag WHERE name = ? LIMIT 1",
            (name,),
        ).fetchone()

    def _find_model_by_id(self, model_id: int):
        """IDに一致するモデル行を取得する。"""

        return self._connection.execute(
            "SELECT id, name FROM image_model WHERE id = ? LIMIT 1",
            (model_id,),
        ).fetchone()

    def _find_model_by_name(self, name: str):
        """名前に一致するモデル行を取得する。"""

        return self._connection.execute(
            "SELECT id, name FROM image_model WHERE name = ? LIMIT 1",
            (name,),
        ).fetchone()

    def _find_image_ids_by_tag_id(self, tag_id: int) -> list[int]:
        """タグに紐づく画像ID一覧を取得する。"""

        rows = self._connection.execute(
            """
            SELECT image_file_id
            FROM tag_image_link
            WHERE tag_id = ?
            ORDER BY image_file_id ASC
            """,
            (tag_id,),
        ).fetchall()
        return [int(row["image_file_id"]) for row in rows]

    def _find_image_ids_by_model_id(self, model_id: int) -> list[int]:
        """モデルに紐づく画像ID一覧を取得する。"""

        rows = self._connection.execute(
            """
            SELECT image_file_data_id
            FROM image_model_to_file_data
            WHERE image_model_id = ?
            ORDER BY image_file_data_id ASC
            """,
            (model_id,),
        ).fetchall()
        return [int(row["image_file_data_id"]) for row in rows]

    def _replace_tag_hashes(self, image_ids: list[int]) -> None:
        """指定画像群の現在のタグ構成からtag_hashを再同期する。"""

        for image_id in image_ids:
            self.replace_tag_hash(image_id)

    def _replace_or_merge_tag(
        self,
        tag_id: int,
        source,
        target,
        new_name: str,
        image_ids: list[int],
    ) -> MasterReplaceResult:
        """タグ名更新または既存タグへのリンク統合を行う。"""

        if target is None:
            self._connection.execute(
                "UPDATE tag SET name = ? WHERE id = ?",
                (new_name, tag_id),
            )
            return MasterReplaceResult(
                source_id=tag_id,
                source_name=str(source["name"]),
                target_id=tag_id,
                target_name=new_name,
                affected_image_count=len(image_ids),
                merged=False,
            )

        target_id = int(target["id"])
        self._merge_tag_links(tag_id, target_id)
        return MasterReplaceResult(
            source_id=tag_id,
            source_name=str(source["name"]),
            target_id=target_id,
            target_name=str(target["name"]),
            affected_image_count=len(image_ids),
            merged=True,
        )

    def _merge_tag_links(self, source_tag_id: int, target_tag_id: int) -> None:
        """重複リンクを避けてsourceタグリンクをtargetタグへ統合する。"""

        self._connection.execute(
            """
            DELETE FROM tag_image_link
            WHERE tag_id = ?
              AND image_file_id IN (
                SELECT image_file_id
                FROM tag_image_link
                WHERE tag_id = ?
              )
            """,
            (source_tag_id, target_tag_id),
        )
        self._connection.execute(
            """
            UPDATE tag_image_link
            SET tag_id = ?
            WHERE tag_id = ?
            """,
            (target_tag_id, source_tag_id),
        )
        self._connection.execute(
            "DELETE FROM tag WHERE id = ?",
            (source_tag_id,),
        )

    def _replace_or_merge_model(
        self,
        model_id: int,
        source,
        target,
        new_name: str,
        image_ids: list[int],
    ) -> MasterReplaceResult:
        """モデル名更新または既存モデルへのリンク統合を行う。"""

        if target is None:
            self._connection.execute(
                "UPDATE image_model SET name = ? WHERE id = ?",
                (new_name, model_id),
            )
            return MasterReplaceResult(
                source_id=model_id,
                source_name=str(source["name"]),
                target_id=model_id,
                target_name=new_name,
                affected_image_count=len(image_ids),
                merged=False,
            )

        target_id = int(target["id"])
        self._connection.execute(
            """
            UPDATE image_model_to_file_data
            SET image_model_id = ?
            WHERE image_model_id = ?
            """,
            (target_id, model_id),
        )
        self._connection.execute(
            "DELETE FROM image_model WHERE id = ?",
            (model_id,),
        )
        return MasterReplaceResult(
            source_id=model_id,
            source_name=str(source["name"]),
            target_id=target_id,
            target_name=str(target["name"]),
            affected_image_count=len(image_ids),
            merged=True,
        )

    def _build_order_by(self, sort: str) -> str:
        """許可済みソート値からORDER BY句を生成する。"""

        mapping = {
            "id_desc": "image_file.id DESC",
            "id_asc": "image_file.id ASC",
            "filename_asc": "image_file.filename COLLATE NOCASE ASC, image_file.id DESC",
            "filename_desc": "image_file.filename COLLATE NOCASE DESC, image_file.id DESC",
            "rating_asc": "image_file.rating ASC, image_file.id DESC",
            "rating_desc": "image_file.rating DESC, image_file.id DESC",
        }
        return mapping.get(sort, mapping["id_desc"])

    def _build_search_conditions(
        self,
        *,
        path: str,
        rating: str | None,
        is_checked: bool | int | None,
        is_favorite: bool | int | None,
        tags: list[str] | None,
        folder_id: int | None,
        model: str | None,
        tag_hash: str | None,
        tag_set: str | None,
        tag_keyword: str | None,
    ) -> tuple[list[str], list[object]]:
        """画像検索のWHERE条件とパラメータを組み立てる。"""

        where_clauses: list[str] = []
        params: list[object] = []

        normalized_path = path.strip()
        if normalized_path:
            where_clauses.append("image_file.path LIKE ?")
            params.append(f"%{normalized_path}%")

        if rating:
            where_clauses.append("image_file.rating = ?")
            params.append(rating)

        if self._normalize_true_condition(is_checked):
            where_clauses.append("image_file.is_checked = 1")

        if self._normalize_true_condition(is_favorite):
            where_clauses.append("image_file.is_favorite = 1")

        if folder_id is not None:
            where_clauses.append("image_file.folder_id = ?")
            params.append(folder_id)

        self._append_model_condition(where_clauses, params, model)
        self._append_tag_conditions(where_clauses, params, tags)
        self._append_tag_keyword_condition(where_clauses, params, tag_keyword)
        self._append_tag_hash_condition(where_clauses, params, tag_hash, tag_set)
        return where_clauses, params

    def _append_tag_conditions(
        self,
        where_clauses: list[str],
        params: list[object],
        tags: list[str] | None,
    ) -> None:
        """タグAND検索条件をWHERE句へ追加する。"""

        normalized_tags = [tag for tag in (tags or []) if tag]
        if not normalized_tags:
            return

        placeholders = ", ".join("?" for _ in normalized_tags)
        where_clauses.append(
            f"""
            image_file.id IN (
                SELECT
                    tag_image_link.image_file_id
                FROM tag_image_link
                INNER JOIN tag
                    ON tag.id = tag_image_link.tag_id
                WHERE tag.name IN ({placeholders})
                GROUP BY tag_image_link.image_file_id
                HAVING COUNT(DISTINCT tag.name) = ?
            )
            """
        )
        params.extend(normalized_tags)
        params.append(len(normalized_tags))

    def _append_tag_hash_condition(
        self,
        where_clauses: list[str],
        params: list[object],
        tag_hash: str | None,
        tag_set: str | None,
    ) -> None:
        """タグ構成完全一致検索条件をWHERE句へ追加する。"""

        if not tag_hash or not tag_set:
            return

        where_clauses.append(
            """
            image_file.id IN (
                SELECT
                    tag_hash.image_file_data_id
                FROM tag_hash
                WHERE tag_hash.hash = ?
                  AND tag_hash.tag_set = ?
            )
            """
        )
        params.extend([tag_hash, tag_set])

    def _append_tag_keyword_condition(
        self,
        where_clauses: list[str],
        params: list[object],
        tag_keyword: str | None,
    ) -> None:
        """タグ名の部分一致検索条件をWHERE句へ追加する。"""

        keyword = str(tag_keyword or "").strip().lower()
        if not keyword:
            return

        where_clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM tag_image_link tag_link_keyword
                INNER JOIN tag tag_keyword
                    ON tag_keyword.id = tag_link_keyword.tag_id
                WHERE tag_link_keyword.image_file_id = image_file.id
                  AND tag_keyword.name LIKE ? ESCAPE '\\'
            )
            """
        )
        params.append(f"%{self._escape_like(keyword)}%")

    def _append_model_condition(
        self,
        where_clauses: list[str],
        params: list[object],
        model: str | None,
    ) -> None:
        """生成元モデル完全一致検索条件をWHERE句へ追加する。"""

        if not model:
            return

        where_clauses.append(
            """
            image_file.id IN (
                SELECT
                    model_link.image_file_data_id
                FROM image_model_to_file_data model_link
                INNER JOIN image_model
                    ON image_model.id = model_link.image_model_id
                WHERE image_model.name = ?
            )
            """
        )
        params.append(model)

    def _escape_like(self, value: str) -> str:
        """LIKE検索でワイルドカード扱いされる文字をエスケープする。"""

        return (
            value
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )

    def _build_tag_search_params(self, keyword: str | None, limit: int) -> dict[str, object]:
        """タグ候補検索SQL用のパラメータを作る。"""

        normalized_keyword = (keyword or "").strip()
        return {
            "keyword": normalized_keyword,
            "keyword_like": f"%{normalized_keyword}%",
            "limit": max(1, min(int(limit), 256)),
        }

    def _build_folder_search_params(self, keyword: str | None, limit: int) -> dict[str, object]:
        """フォルダ候補検索SQL用のパラメータを作る。"""

        normalized_keyword = (keyword or "").strip()
        return {
            "keyword": normalized_keyword,
            "keyword_like": f"%{normalized_keyword}%",
            "limit": max(1, min(int(limit), 256)),
        }

    def _build_model_search_params(self, keyword: str | None, limit: int) -> dict[str, object]:
        """モデル候補検索SQL用のパラメータを作る。"""

        normalized_keyword = (keyword or "").strip()
        return {
            "keyword": normalized_keyword,
            "keyword_like": f"%{normalized_keyword}%",
            "limit": max(1, min(int(limit), 256)),
        }

    def _build_tag_hash_value(self, tag_set: str) -> str:
        """tag_setから検索用MD5ハッシュを作る。"""

        return hashlib.md5(tag_set.encode("utf-8")).hexdigest()

    def _normalize_true_condition(self, value: bool | int | None) -> bool:
        """検索条件値をtrue条件として評価する。"""

        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return int(value) == 1

    def _normalize_page(self, value: object) -> int:
        """ページ番号を1以上の整数へ丸める。"""

        try:
            page = int(value or 1)
        except (TypeError, ValueError):
            return 1
        return max(1, page)

    def _normalize_page_size(self, value: object) -> int:
        """ページサイズを許可リスト内の値へ丸める。"""

        try:
            page_size = int(value or self._DEFAULT_PAGE_SIZE)
        except (TypeError, ValueError):
            return self._DEFAULT_PAGE_SIZE

        if page_size not in self._ALLOWED_PAGE_SIZES:
            return self._DEFAULT_PAGE_SIZE
        return page_size

    def _validate_detail_values(self, rating: str, is_checked: int, is_favorite: int) -> None:
        """詳細更新で許可する値か検証する。"""

        if rating not in {"General", "R-15", "R-18", "R-18G"}:
            raise ValueError("rating is invalid.")
        if is_checked not in {0, 1}:
            raise ValueError("is_checked must be 0 or 1.")
        if is_favorite not in {0, 1}:
            raise ValueError("is_favorite must be 0 or 1.")

    def _filter_bulk_attribute_updates(self, updates: dict | None) -> dict[str, object]:
        """一括属性更新で許可されたカラムだけを抽出する。"""

        allowed_columns = {"rating", "is_checked", "is_favorite"}
        return {
            key: value
            for key, value in (updates or {}).items()
            if key in allowed_columns
        }

    def _build_bulk_attribute_update_params(
        self,
        record_ids: list[int],
        update_values: dict[str, object],
    ) -> tuple[list[str], dict[str, object]]:
        """一括属性更新SQLのSET句とパラメータを組み立てる。"""

        set_clauses = []
        params = {}

        for key, value in update_values.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value

        for index, record_id in enumerate(record_ids):
            params[f"id_{index}"] = record_id

        return set_clauses, params
