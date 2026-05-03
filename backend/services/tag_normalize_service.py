from __future__ import annotations

import re

BRACKET_CHARS = frozenset("()[]{}")
TRAILING_WEIGHT = re.compile(r":\d+(?:\.\d+)?$")
MAX_TAG_LENGTH = 128


class TagNormalizeService:
    """タグ入力値の正規化を担当する。"""

    def normalize_tags(self, values: object) -> list[str]:
        """タグ入力値を保存用タグ一覧へ正規化する。"""

        if values is None:
            return []
        if not isinstance(values, list):
            raise ValueError("tags must be a list.")

        normalized_tags: list[str] = []
        seen: set[str] = set()
        for value in values:
            for tag in self._normalize_tag_values(value):
                if tag in seen:
                    continue
                seen.add(tag)
                normalized_tags.append(tag)
        return normalized_tags

    def _normalize_tag_values(self, value: object) -> list[str]:
        """1入力値をカンマで分割し、タグとして正規化する。"""

        tags: list[str] = []
        for part in str(value).split(","):
            tag = self._normalize_tag_text(part)
            if not tag:
                continue
            if len(tag) > MAX_TAG_LENGTH:
                raise ValueError("tag must be 128 characters or less.")
            tags.append(tag)
        return tags

    def _normalize_tag_text(self, value: str) -> str:
        """タグ文字列1件を保存用表記へ正規化する。"""

        tag = value.strip()
        tag = self._remove_unescaped_brackets(tag)
        tag = TRAILING_WEIGHT.sub("", tag)
        return tag.strip().lower()

    def _remove_unescaped_brackets(self, value: str) -> str:
        """バックスラッシュでエスケープされていない括弧だけ除去する。"""

        chars: list[str] = []
        previous = ""
        for char in value:
            if char in BRACKET_CHARS and previous != "\\":
                previous = char
                continue

            chars.append(char)
            previous = char
        return "".join(chars)
