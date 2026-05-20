from __future__ import annotations

from pathlib import Path

from backend.models import (
    ImageFileListItem,
    TagCaptionExportFailure,
    TagCaptionExportResult,
)


class TagCaptionExportService:
    """画像ごとのタグcaptionファイル出力を担当する。"""

    def export(
        self,
        items: list[ImageFileListItem],
        tags_by_image_id: dict[int, list[str]],
    ) -> TagCaptionExportResult:
        """画像ごとの同名txtへタグを出力し、集計結果を返す。"""

        exported_count = 0
        skipped_count = 0
        failed_count = 0
        failed_files: list[TagCaptionExportFailure] = []
        tag_frequency = self._build_frequency_map(tags_by_image_id)

        for item in items:
            tags = self._sort_tags_by_frequency(tags_by_image_id.get(item.id, []), tag_frequency)
            if not tags:
                skipped_count += 1
                continue

            try:
                self._write_caption_file(item, tags)
                exported_count += 1
            except Exception:
                failed_count += 1
                self._append_failure(failed_files, item)

        return TagCaptionExportResult(
            target_count=len(items),
            exported_count=exported_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            failed_files=failed_files,
        )

    def _write_caption_file(self, item: ImageFileListItem, tags: list[str]) -> None:
        """1画像分のcaptionファイルをUTF-8で上書き保存する。"""

        caption_path = Path(item.path).with_suffix(".txt")
        caption_path.write_text(", ".join(tags) + "\n", encoding="utf-8")

    def _build_frequency_map(self, tags_by_image_id: dict[int, list[str]]) -> dict[str, int]:
        """選択画像群内でタグを含む画像数を集計する。"""

        frequency: dict[str, int] = {}
        for tags in tags_by_image_id.values():
            for tag in set(tags):
                frequency[tag] = frequency.get(tag, 0) + 1
        return frequency

    def _sort_tags_by_frequency(self, tags: list[str], frequency: dict[str, int]) -> list[str]:
        """出現画像数の多い順、同頻度はタグ名昇順で並べ替える。"""

        return sorted(tags, key=lambda tag: (-frequency.get(tag, 0), tag))

    def _append_failure(
        self,
        failed_files: list[TagCaptionExportFailure],
        item: ImageFileListItem,
    ) -> None:
        """失敗情報を最大20件まで追加する。"""

        if len(failed_files) >= 20:
            return
        failed_files.append(
            TagCaptionExportFailure(
                id=item.id,
                path=item.path,
                reason="caption ファイルを書き込めませんでした。",
            )
        )
