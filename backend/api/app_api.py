from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    success: bool
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }


class AppApi:
    """Public API exposed to Vue through pywebview."""

    def initialize(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Application initialized.",
            data={
                "initialized_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

    def get_app_info(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Application information loaded.",
            data={
                "name": "AZViewer",
                "version": "0.1.0",
                "description": "pywebview + Vue + Bootstrap application foundation.",
            },
        ).to_dict()

    def get_menu_definitions(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Menu definitions loaded.",
            data=[
                {
                    "key": "home",
                    "label": "Home",
                    "description": "基盤の概要とアプリ情報を表示します。",
                },
                {
                    "key": "sample",
                    "label": "Sample",
                    "description": "今後の機能追加用プレースホルダです。",
                },
            ],
        ).to_dict()

    def health_check(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Python API is available.",
            data={
                "status": "ok",
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

