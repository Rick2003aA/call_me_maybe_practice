import json
from typing import Any
from pydantic import ValidationError

from .models import FunctionDefinition, Prompt


# 関数一覧をを読み込んでインスタンス化する
# →それをリストに格納して返す
def load_function_definitions(file_path: str) -> list[FunctionDefinition]:
    data = load_json_file(file_path)
    return validate_function_definitions(data)


def load_prompt_items(file_path: str) -> list[Prompt]:
    data = load_json_file(file_path)
    return validate_prompt_items(data)


def load_json_file(file_path: str) -> Any:
    """ファイルを開いてjson.loadする"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise ValueError(f"Input file not found: {file_path}") from e
    except PermissionError as e:
        raise ValueError(
            f"Permission denied while reading: {file_path}"
        ) from e
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in {file_path} "
            f"at line {e.lineno}, column {e.colno}: {e.msg}"
        ) from e
    except OSError as e:
        raise ValueError(f"Could not read file {file_path}: {e}") from e


def validate_function_definitions(data: Any) -> list[FunctionDefinition]:
    """JSONの生データを関数定義のリストとして検証する。"""
    if not isinstance(data, list):
        raise ValueError("Function definition file must contain a JSON array")
    try:
        return [FunctionDefinition(**item) for item in data]
    except ValidationError as e:
        raise ValueError(
            f"Invalid function definition format: {e}"
        ) from e


def validate_prompt_items(data: Any) -> list[Prompt]:
    """JSONの生データをプロンプト項目のリストとして検証する。"""
    if not isinstance(data, list):
        raise ValueError("Prompt input file must contain a JSON array")
    try:
        return [Prompt(**item) for item in data]
    except ValidationError as exc:
        raise ValueError(
            f"Invalid prompt input format: {exc}"
        ) from exc
