import json
from typing import Any
from pydantic import ValidationError

from .models import FunctionDefinition, Prompt


# 関数一覧をを読み込んでインスタンス化する
# →それをリストに格納して返す
def load_function_definitions(file_path: str) -> list[FunctionDefinition]:
    """Load and validate function definitions from a JSON file.

    Args:
        file_path: Path to the function definition JSON file.

    Returns:
        Validated function definitions.

    Raises:
        ValueError: If the file cannot be read or does not match the schema.
    """
    data = load_json_file(file_path)
    return validate_function_definitions(data)


def load_prompt_items(file_path: str) -> list[Prompt]:
    """Load and validate prompt items from a JSON file.

    Args:
        file_path: Path to the prompt input JSON file.

    Returns:
        Validated prompt items.

    Raises:
        ValueError: If the file cannot be read or does not match the schema.
    """
    data = load_json_file(file_path)
    return validate_prompt_items(data)


def load_json_file(file_path: str) -> Any:
    """Read and parse a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        ValueError: If the file is missing, unreadable, or invalid JSON.
    """
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
    """Validate raw JSON data as function definitions.

    Args:
        data: Raw parsed JSON data.

    Returns:
        Validated function definitions.

    Raises:
        ValueError: If the data is not a valid function definition array.
    """
    if not isinstance(data, list):
        raise ValueError("Function definition file must contain a JSON array")
    try:
        return [FunctionDefinition(**item) for item in data]
    except ValidationError as e:
        raise ValueError(
            f"Invalid function definition format: {e}"
        ) from e


def validate_prompt_items(data: Any) -> list[Prompt]:
    """Validate raw JSON data as prompt items.

    Args:
        data: Raw parsed JSON data.

    Returns:
        Validated prompt items.

    Raises:
        ValueError: If the data is not a valid prompt array.
    """
    if not isinstance(data, list):
        raise ValueError("Prompt input file must contain a JSON array")
    try:
        return [Prompt(**item) for item in data]
    except ValidationError as exc:
        raise ValueError(
            f"Invalid prompt input format: {exc}"
        ) from exc
