from pydantic import BaseModel
from typing import Any


class ParameterDefinition(BaseModel):
    type: str


class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, ParameterDefinition]
    returns: ParameterDefinition


class Prompt(BaseModel):
    prompt: str


def create_function_call(
        name: str,
        parameters: dict[str, Any],
        ) -> dict[str, Any]:
    """関数名とパラメータから検証済みのFunction Callを作成する。"""
    raise NotImplementedError


def validate_parameter_value(
        value: Any,
        parameter_definition: ParameterDefinition,
        ) -> bool:
    """値が宣言されたパラメータ型と一致するか検証する。"""
    raise NotImplementedError


def validate_required_parameters(
        parameters: dict[str, Any],
        function_definition: FunctionDefinition,
        ) -> bool:
    """関数に必要なパラメータがすべて存在するか検証する。"""
    raise NotImplementedError
