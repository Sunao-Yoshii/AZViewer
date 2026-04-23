from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    """Vueへ返却するpywebview APIレスポンスの共通形式を表す。"""

    success: bool
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        """pywebview経由で返却しやすい辞書形式に変換する。"""

        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }
