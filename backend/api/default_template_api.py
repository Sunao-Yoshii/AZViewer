from __future__ import annotations

from datetime import datetime

from .api_response import ApiResponse


class DefaultTemplateApi:
    """テンプレート表示用の基本APIを提供する。"""

    def initialize_app(self) -> dict[str, object]:
        """Vue側の起動時に必要な初期化済みアプリ情報を返す。"""

        return ApiResponse(
            success=True,
            message="",
            data={
                "appName": "AZViewer",
                "initialized_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

    def get_app_info(self) -> dict[str, object]:
        """アプリケーション名やバージョンなどの基本情報を返す。"""

        return ApiResponse(
            success=True,
            message="Application information loaded.",
            data={
                "name": "AZViewer",
                "version": "0.2.0",
                "description": "pywebview + Vue + Bootstrap application foundation.",
            },
        ).to_dict()

    def health_check(self) -> dict[str, object]:
        """Python APIが呼び出し可能か確認するための応答を返す。"""

        return ApiResponse(
            success=True,
            message="Python API is available.",
            data={
                "status": "ok",
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()
