from pydantic import BaseModel
from typing import Any


# ＝＝＝　インスタンス化のためのクラス　＝＝＝

class ParameterDefinition(BaseModel):
    type: str


class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, ParameterDefinition]
    returns: ParameterDefinition


class Prompt(BaseModel):
    prompt: str


# ＝＝＝　生成後の型チェック　＝＝＝

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
    """関数定義と比較して正しい出力かどうかを確認"""
    expected_parameters = function_definition.parameters

    if parameters.keys() != expected_parameters.keys():
        return False

    for name, definition in expected_parameters.items():
        if not validate_parameter_value(parameters[name], definition):
            return False

    return True
