from pydantic import BaseModel
from typing import Any


# ＝＝＝　インスタンス化のためのクラス　＝＝＝

class ParameterDefinition(BaseModel):
    """Function parameter metadata loaded from the definition file.

    Attributes:
        type: Declared JSON-compatible parameter type.
    """

    type: str


class FunctionDefinition(BaseModel):
    """Callable function schema loaded from the function definition file.

    Attributes:
        name: Function name that may be selected by the model.
        description: Natural-language description of the function behavior.
        parameters: Mapping of parameter names to parameter definitions.
        returns: Return value metadata from the definition file.
    """

    name: str
    description: str
    parameters: dict[str, ParameterDefinition]
    returns: ParameterDefinition


class Prompt(BaseModel):
    """Single natural-language prompt item loaded from the input file.

    Attributes:
        prompt: User request that should be converted into a function call.
    """

    prompt: str


# ＝＝＝　生成後の型チェック　＝＝＝

def validate_parameter_value(
        value: Any,
        parameter_definition: ParameterDefinition,
        ) -> bool:
    """Check whether a generated value matches a parameter definition.

    Args:
        value: Generated parameter value to validate.
        parameter_definition: Expected parameter metadata.

    Returns:
        True if the value matches the declared type, otherwise False.
    """
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
    """Check generated parameters against a function definition.

    Args:
        parameters: Generated parameter mapping.
        function_definition: Function schema to validate against.

    Returns:
        True if all required parameters are present with valid types,
        otherwise False.
    """
    expected_parameters = function_definition.parameters

    if parameters.keys() != expected_parameters.keys():
        return False

    for name, definition in expected_parameters.items():
        if not validate_parameter_value(parameters[name], definition):
            return False

    return True
