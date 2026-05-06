from __future__ import annotations

import re

from backend.models import ImageFileListItem, PromptTagImportFailure, PromptTagImportResult
from backend.repositories import ImageFileRepository
from backend.services.image_metadata_service import ImageMetadataService
from backend.services.tag_normalize_service import TagNormalizeService

BREAK_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_])break(?![A-Za-z0-9_])",
    flags=re.IGNORECASE,
)
MAX_FAILURE_DETAILS = 20
MAX_MODEL_NAME_LENGTH = 512


class PromptTagImportService:
    """タグ未登録画像からWebUIプロンプトを読み取り、タグとして一括登録する。"""

    def __init__(
        self,
        repository: ImageFileRepository,
        metadata_service: ImageMetadataService,
        tag_normalize_service: TagNormalizeService,
    ) -> None:
        """一括登録で利用するリポジトリと各変換サービスを保持する。"""

        self._repository = repository
        self._metadata_service = metadata_service
        self._tag_normalize_service = tag_normalize_service

    def import_prompt_tags(self) -> PromptTagImportResult:
        """タグ未登録画像へタグを、モデル未設定画像へモデル名を登録する。"""

        target_items = self._repository.find_items_without_tags()
        processed_count = 0
        tagged_count = 0
        skipped_count = 0
        failed_count = 0
        failed_files: list[PromptTagImportFailure] = []

        for item in target_items:
            processed_count += 1
            try:
                tags = self._extract_tags(item)
                if not tags:
                    skipped_count += 1
                    continue
                self._repository.replace_tags_atomic(item.id, tags)
                tagged_count += 1
            except Exception as exc:
                failed_count += 1
                self._append_failure(failed_files, item, f"タグ登録に失敗しました。{str(exc)}")

        model_result = self._import_missing_models(failed_files)

        return PromptTagImportResult(
            target_count=len(target_items),
            processed_count=processed_count,
            tagged_count=tagged_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            failed_files=failed_files,
            model_target_count=model_result["target_count"],
            model_processed_count=model_result["processed_count"],
            model_linked_count=model_result["linked_count"],
            model_skipped_count=model_result["skipped_count"],
            model_failed_count=model_result["failed_count"],
        )

    def _import_missing_models(self, failed_files: list[PromptTagImportFailure]) -> dict[str, int]:
        """モデル未設定画像へメタ情報由来のモデル名を登録する。"""

        target_items = self._repository.find_items_without_model()
        result = {
            "target_count": len(target_items),
            "processed_count": 0,
            "linked_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
        }

        for item in target_items:
            result["processed_count"] += 1
            try:
                model_name = self._extract_model_name(item)
                if not model_name:
                    result["skipped_count"] += 1
                    continue

                self._repository.replace_image_model_atomic(item.id, model_name)
                result["linked_count"] += 1
            except Exception as exc:
                result["failed_count"] += 1
                self._append_failure(failed_files, item, f"モデル情報の登録に失敗しました。{str(exc)}")

        return result

    def _extract_tags(self, item: ImageFileListItem) -> list[str]:
        """1画像からプロンプトを抽出して保存用タグ一覧へ正規化する。"""

        prompt = self._metadata_service.extract_stable_diffusion_prompt(item.path)
        if not prompt:
            return []

        prompt = BREAK_TOKEN.sub("", prompt)
        return self._tag_normalize_service.normalize_tags([prompt])

    def _extract_model_name(self, item: ImageFileListItem) -> str | None:
        """1画像からモデル名を抽出して保存用に検証する。"""

        model_name = self._metadata_service.extract_stable_diffusion_model_name(item.path)
        if not model_name:
            return None
        if len(model_name) > MAX_MODEL_NAME_LENGTH:
            raise ValueError("モデル名は512文字以内で入力してください。")
        return model_name

    def _append_failure(
        self,
        failed_files: list[PromptTagImportFailure],
        item: ImageFileListItem,
        reason: str,
    ) -> None:
        """APIへ返す失敗詳細を上限件数まで追加する。"""

        if len(failed_files) >= MAX_FAILURE_DETAILS:
            return

        failed_files.append(
            PromptTagImportFailure(
                id=item.id,
                path=item.path,
                reason=reason or "メタ情報を取得できませんでした。",
            )
        )
