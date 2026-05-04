from __future__ import annotations

import hashlib
from dataclasses import replace
from math import ceil
from sqlite3 import Connection

from backend.models import (
    DuplicateTagSetItem,
    FolderListItem,
    ImageFileListItem,
    ImageFileRecord,
    SearchImageFilesResult,
    TagListItem,
)


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
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                CHECK (length(name) <= 128)
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
        self._create_tag_hash_table()
        self._connection.commit()

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
        return self._attach_tags([self._row_to_item(row) for row in rows])

    def find_items_without_tags(self) -> list[ImageFileListItem]:
        """タグが1件も紐づいていない画像ファイル情報を取得する。"""

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
            FROM image_file_data image_file
            WHERE NOT EXISTS (
                SELECT 1
                FROM tag_image_link tag_link
                WHERE tag_link.image_file_id = image_file.id
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
        self.delete_tag_hashes(record_ids)

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
        return self._attach_tags([self._row_to_item(row) for row in rows])

    def find_by_ids(self, record_ids: list[int]) -> list[ImageFileListItem]:
        """指定ID群に一致する画像ファイル情報を取得する。"""

        if not record_ids:
            return []

        placeholders = ", ".join("?" for _ in record_ids)
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
            WHERE id IN ({placeholders})
            ORDER BY id ASC
            """,
            record_ids,
        ).fetchall()
        return self._attach_tags([self._row_to_item(row) for row in rows])

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
        folder: str | None = None,
        tag_hash: str | None = None,
        tag_set: str | None = None,
        page: int = 1,
        page_size: int = 25,
        sort: str = "id_desc",
    ) -> SearchImageFilesResult:
        """条件に一致する画像一覧をページング付きで取得する。"""

        safe_page = max(1, int(page))
        safe_page_size = max(1, int(page_size))
        where_clauses, params = self._build_search_conditions(
            path=path,
            rating=rating,
            is_checked=is_checked,
            is_favorite=is_favorite,
            tags=tags,
            folder=folder,
            tag_hash=tag_hash,
            tag_set=tag_set,
        )
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
        items = self._attach_tags(items)
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
                folder AS name,
                COUNT(*) AS image_count,
                MIN(id) AS first_id
            FROM image_file_data
            WHERE (:keyword = '' OR folder LIKE :keyword_like)
            GROUP BY folder
            ORDER BY first_id ASC
            LIMIT :limit
            """,
            params,
        ).fetchall()
        return [
            FolderListItem(name=str(row["name"]), image_count=int(row["image_count"]))
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
                FROM (
                    SELECT
                        folder
                    FROM image_file_data
                    WHERE (:keyword = '' OR folder LIKE :keyword_like)
                    GROUP BY folder
                ) folders
                """,
                params,
            ).fetchone()["count"]
        )

    def delete_by_id(self, record_id: int) -> bool:
        """IDに一致する画像ファイル情報を削除する。"""

        self.delete_tag_hash(record_id)
        cursor = self._connection.execute(
            "DELETE FROM image_file_data WHERE id = ?",
            (record_id,),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def delete_by_ids(self, record_ids: list[int]) -> int:
        """指定ID群に一致する画像ファイル情報を削除し、削除件数を返す。"""

        if not record_ids:
            return 0

        placeholders = ", ".join("?" for _ in record_ids)
        self.delete_tag_hashes(record_ids)
        cursor = self._connection.execute(
            f"DELETE FROM image_file_data WHERE id IN ({placeholders})",
            record_ids,
        )
        self._connection.commit()
        return cursor.rowcount

    def update_paths(self, updates: list[dict[str, object]]) -> int:
        """指定ID群のパスとフォルダを更新し、更新件数を返す。"""

        if not updates:
            return 0

        try:
            cursor = self._connection.executemany(
                """
                UPDATE image_file_data
                SET
                    path = :path,
                    folder = :folder
                WHERE id = :id
                """,
                updates,
            )
            updated_count = cursor.rowcount
            if updated_count != len(updates):
                raise RuntimeError("Some image file paths could not be updated.")
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

    def find_tags_by_image_ids(self, image_ids: list[int]) -> dict[int, list[str]]:
        """画像ID群に紐づくタグ一覧をまとめて取得する。"""

        if not image_ids:
            return {}

        placeholders = ", ".join("?" for _ in image_ids)
        rows = self._connection.execute(
            f"""
            SELECT
                tag_image_link.image_file_id,
                tag.name
            FROM tag_image_link
            INNER JOIN tag ON tag.id = tag_image_link.tag_id
            WHERE tag_image_link.image_file_id IN ({placeholders})
            ORDER BY tag_image_link.image_file_id ASC, tag.name ASC
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
        item = self._row_to_item(row)
        return self._attach_tags([item])[0]

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
            rating=str(row["rating"]),
            is_checked=int(row["is_checked"]),
            is_favorite=int(row["is_favorite"]),
            comment=None if row["comment"] is None else str(row["comment"]),
            tags=[],
        )

    def _attach_tags(self, items: list[ImageFileListItem]) -> list[ImageFileListItem]:
        """一覧項目群へタグ情報をまとめて付与する。"""

        tags_by_image_id = self.find_tags_by_image_ids([item.id for item in items])
        return [
            replace(item, tags=tags_by_image_id.get(item.id, []))
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

    def _build_search_conditions(
        self,
        *,
        path: str,
        rating: str | None,
        is_checked: bool | int | None,
        is_favorite: bool | int | None,
        tags: list[str] | None,
        folder: str | None,
        tag_hash: str | None,
        tag_set: str | None,
    ) -> tuple[list[str], list[object]]:
        """画像検索のWHERE条件とパラメータを組み立てる。"""

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

        if folder:
            where_clauses.append("folder = ?")
            params.append(folder)

        self._append_tag_conditions(where_clauses, params, tags)
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
            id IN (
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
            id IN (
                SELECT
                    tag_hash.image_file_data_id
                FROM tag_hash
                WHERE tag_hash.hash = ?
                  AND tag_hash.tag_set = ?
            )
            """
        )
        params.extend([tag_hash, tag_set])

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

    def _validate_detail_values(self, rating: str, is_checked: int, is_favorite: int) -> None:
        """詳細更新で許可する値か検証する。"""

        if rating not in {"General", "R-15", "R-18", "R-18G"}:
            raise ValueError("rating is invalid.")
        if is_checked not in {0, 1}:
            raise ValueError("is_checked must be 0 or 1.")
        if is_favorite not in {0, 1}:
            raise ValueError("is_favorite must be 0 or 1.")
