import json
from typing import Any

from .models import FunctionDefinition, Prompt


# 関数一覧をを読み込んでインスタンス化する
# →それをリストに格納して返す
def load_function_definitions(file_path: str) -> list[FunctionDefinition]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [FunctionDefinition(**item) for item in data]


def load_prompt_items(file_path: str) -> list[Prompt]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Prompt(**item) for item in data]


def load_json_file(file_path: str) -> Any:
    """JSONデータを読み込み、ファイル操作またはJSON構文のエラーを通知する。"""
    raise NotImplementedError


def validate_function_definitions(data: Any) -> list[FunctionDefinition]:
    """JSONの生データを関数定義のリストとして検証する。"""
    raise NotImplementedError


def validate_prompt_items(data: Any) -> list[Prompt]:
    """JSONの生データをプロンプト項目のリストとして検証する。"""
    raise NotImplementedError
