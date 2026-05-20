from __future__ import annotations

from pathlib import Path

from backend.models import (
    CaptionTagImportFailure,
    CaptionTagImportResult,
    ImageFileListItem,
)
from backend.repositories import ImageFileRepository
from backend.services.tag_normalize_service import TagNormalizeService

MAX_FAILURE_DETAILS = 20


class CaptionTagImportService:
    """画像と同名のcaptionファイルからタグを追加登録する。"""

    def __init__(
        self,
        repository: ImageFileRepository,
        tag_normalize_service: TagNormalizeService,
    ) -> None:
        """タグ追加に必要なリポジトリと正規化サービスを保持する。"""

        self._repository = repository
        self._tag_normalize_service = tag_normalize_service

    def import_caption_tags(self, image_ids: list[int]) -> CaptionTagImportResult:
        """指定画像へcaption由来タグを追加し、集計結果を返す。"""

        items = self._repository.find_by_ids(image_ids)
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        failed_files: list[CaptionTagImportFailure] = []

        for item in items:
            try:
                tags = self._read_caption_tags(item)
                if not tags:
                    skipped_count += 1
                    continue
                if self._repository.merge_tags_atomic(item.id, tags):
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                failed_count += 1
                self._append_failure(failed_files, item, self._to_failure_reason(exc))

        return CaptionTagImportResult(
            target_count=len(items),
            updated_count=updated_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            failed_files=failed_files,
        )

    def _read_caption_tags(self, item: ImageFileListItem) -> list[str]:
        """1画像分のcaptionファイルを読み取り、保存用タグ一覧へ正規化する。"""

        caption_path = Path(item.path).with_suffix(".txt")
        if not caption_path.is_file():
            return []

        caption_text = caption_path.read_text(encoding="utf-8-sig")
        if not caption_text.strip():
            return []
        return self._tag_normalize_service.normalize_tags([caption_text])

    def _append_failure(
        self,
        failed_files: list[CaptionTagImportFailure],
        item: ImageFileListItem,
        reason: str,
    ) -> None:
        """失敗情報を最大件数まで追加する。"""

        if len(failed_files) >= MAX_FAILURE_DETAILS:
            return
        failed_files.append(CaptionTagImportFailure(id=item.id, path=item.path, reason=reason))

    def _to_failure_reason(self, error: Exception) -> str:
        """caption読み込み例外をユーザー向け理由へ変換する。"""

        if isinstance(error, UnicodeError):
            return "caption ファイルを UTF-8 として読み込めませんでした。"
        if isinstance(error, OSError):
            return "caption ファイルを読み込めませんでした。"
        if isinstance(error, ValueError):
            return str(error)
        return "タグ登録に失敗しました。"
