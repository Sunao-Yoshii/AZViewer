from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageOps

from backend.models import ImageFileListItem

LOGGER = logging.getLogger(__name__)
THUMBNAIL_SIZE = 200


class ThumbnailCacheService:
    """画像サムネイルの生成・取得・削除を担当する。"""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """サムネイル保存先ディレクトリを初期化する。"""

        self._cache_dir = cache_dir or Path.cwd() / "data" / "thumbs"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def ensure_thumbnails(self, items: list[ImageFileListItem], *, missing_only: bool = True) -> None:
        """画像一覧項目からサムネイルキャッシュを生成する。"""

        for item in items:
            thumb_path = self.get_thumb_path(item.id)
            if missing_only and thumb_path.is_file():
                continue
            self.create_thumbnail(item.id, item.path)

    def create_thumbnail(self, record_id: int, source_path: str) -> None:
        """指定画像からPNGサムネイルを生成する。"""

        source = Path(source_path)
        if not source.is_file():
            raise FileNotFoundError(f"Source image was not found: {source}")

        thumb_path = self.get_thumb_path(record_id)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(source) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGBA")
            normalized.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
            normalized.save(thumb_path, format="PNG")

    def delete_thumbnails(self, record_ids: list[int]) -> None:
        """指定ID群に対応するサムネイルを削除する。"""

        for record_id in record_ids:
            self.delete_thumbnail(record_id)

    def delete_thumbnail(self, record_id: int) -> None:
        """指定IDに対応するサムネイルを削除する。"""

        thumb_path = self.get_thumb_path(record_id)
        try:
            thumb_path.unlink(missing_ok=True)
        except OSError:
            LOGGER.exception("Failed to delete thumbnail cache: %s", thumb_path)

    def get_thumbnail_bytes(self, record_id: int) -> bytes | None:
        """指定IDのサムネイルファイルを読み込む。"""

        thumb_path = self.get_thumb_path(record_id)
        if not thumb_path.is_file():
            return None
        return thumb_path.read_bytes()

    def get_thumb_path(self, record_id: int) -> Path:
        """指定IDに対応するサムネイル保存パスを返す。"""

        return self._cache_dir / f"{record_id}.png"
