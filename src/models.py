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
    return {
        "name": name,
        "parameters": parameters
    }


def validate_parameter_value(
        value: Any,
        parameter_definition: ParameterDefinition,
        ) -> bool:
    """値が宣言されたパラメータ型と一致するか検証する。"""
    parameter_type = parameter_definition.type

    if parameter_type == "number":
        return (
            isinstance(value, (int, float)) and
            not isinstance(value, bool)
        )

    if parameter_type == "string":
        return (
            isinstance(value, str)
        )

    if parameter_type == "boolean":
        return (
            isinstance(value, bool)
        )

    return False


def validate_required_parameters(
        parameters: dict[str, Any],
        function_definition: FunctionDefinition,
        ) -> bool:
    """生成された辞書に必要なパラメータがすべて存在するか検証する。"""
    expected_parameters = function_definition.parameters

    if parameters.keys() != expected_parameters.keys():
        return False

    for name, definition in expected_parameters.items():
        if not validate_parameter_value(parameters[name], definition):
            return False

    return True
