from __future__ import annotations

from backend.models import (
    BulkTagAddFailure,
    BulkTagAddResult,
    ImageFileListItem,
)
from backend.repositories import ImageFileRepository
from backend.services.tag_normalize_service import TagNormalizeService

MAX_FAILURE_DETAILS = 20


class BulkTagAddService:
    """指定画像群へ同一タグを追加登録する。"""

    def __init__(
        self,
        repository: ImageFileRepository,
        tag_normalize_service: TagNormalizeService,
    ) -> None:
        """タグ追加に必要なリポジトリと正規化サービスを保持する。"""

        self._repository = repository
        self._tag_normalize_service = tag_normalize_service

    def bulk_add_tags(self, image_ids: list[int], tags_text: str) -> BulkTagAddResult:
        """指定画像へ入力タグを追加し、集計結果を返す。"""

        tags = self._tag_normalize_service.normalize_tags([tags_text])
        if not tags:
            raise ValueError("追加するタグを入力してください。")

        items = self._repository.find_by_ids(image_ids)
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        failed_files: list[BulkTagAddFailure] = []

        for item in items:
            try:
                if self._repository.merge_tags_atomic(item.id, tags):
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception:
                failed_count += 1
                self._append_failure(failed_files, item)

        return BulkTagAddResult(
            target_count=len(items),
            updated_count=updated_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            failed_files=failed_files,
        )

    def _append_failure(
        self,
        failed_files: list[BulkTagAddFailure],
        item: ImageFileListItem,
    ) -> None:
        """失敗情報を最大件数まで追加する。"""

        if len(failed_files) >= MAX_FAILURE_DETAILS:
            return
        failed_files.append(
            BulkTagAddFailure(
                id=item.id,
                path=item.path,
                reason="タグ登録に失敗しました。",
            )
        )
