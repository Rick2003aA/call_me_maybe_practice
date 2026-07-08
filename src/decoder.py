import json
import heapq

from llm_sdk import Small_LLM_Model  # type: ignore[attr-defined]
from typing import Any

from .models import Prompt, FunctionDefinition, validate_required_parameters
from .prompt_builder import build_prompt


# ＝＝＝　生成系の関数　＝＝＝

def select_constrained_token(
        logits: list[float],
        valid_token_ids: list[int]
        ) -> int:
    """Select the highest-scoring token from the valid token IDs.

    Args:
        logits: Model scores for the next token.
        valid_token_ids: Token IDs allowed by the current constraint state.

    Returns:
        The valid token ID with the highest score.

    Raises:
        ValueError: If no valid token IDs are available.
    """
    if not valid_token_ids:
        raise ValueError("No valid tokens available")

    return max(valid_token_ids, key=lambda token_id: logits[token_id])


def generate_outputs(functions: list[FunctionDefinition],
                     prompt_items: list[Prompt],
                     llm: Small_LLM_Model) -> list[list[int]]:
    """Generate constrained token outputs for every prompt item.

    Args:
        functions: Available function definitions.
        prompt_items: Prompt items to process.
        llm: Model wrapper used for tokenization, logits, and decoding.

    Returns:
        Generated token IDs for each prompt item.
    """
    # 各プロンプトに対してオリジナルのプロンプトを作成してencodeする
    results = []
    for item in prompt_items:
        prompt = build_prompt(functions, item)
        encoded_prompt = llm.encode(prompt)
        input_ids = encoded_prompt[0].tolist()
        output = generate_constrained_output(input_ids, functions, llm)
        results.append(output)

        # 1プロンプト分が終わったタイミングで出力
        print(llm.decode(output), flush=True)
        print("---", flush=True)

    return results


# ＝＝＝　Parameterのタイプ別の挙動　＝＝＝

def is_valid_string_prefix(value_text: str) -> tuple[bool, int | None]:
    """Check whether a partial JSON string can still become valid.

    Args:
        value_text: Candidate text starting at a JSON string value.

    Returns:
        A tuple containing validity and the string end index when complete.
    """
    if not value_text:
        return True, None

    if value_text[0] != '"':
        return False, None

    index = 1

    while index < len(value_text):
        if value_text[index] == '"':
            return True, index + 1
        index += 1

    return True, None


def is_valid_number_prefix(value_text: str) -> tuple[bool, int | None]:
    """Check whether a partial JSON number can still become valid.

    Args:
        value_text: Candidate text starting at a JSON number value.

    Returns:
        A tuple containing validity and the number end index when complete.
    """
    if not value_text:
        return True, None

    index = 0

    if value_text[index] == "-":
        index += 1

        if index == len(value_text):
            return True, None

    if index == len(value_text) or not value_text[index].isdigit():
        return False, None

    while index < len(value_text) and value_text[index].isdigit():
        index += 1

    # 小数点に関する処理
    if index < len(value_text) and value_text[index] == ".":
        index += 1

        if index == len(value_text):
            return True, None

        if not value_text[index].isdigit():
            return False, None

        while index < len(value_text) and value_text[index].isdigit():
            index += 1

    return True, index


def is_valid_boolean_prefix(value_text: str) -> tuple[bool, int | None]:
    """Check whether a partial JSON boolean can still become valid.

    Args:
        value_text: Candidate text starting at a JSON boolean value.

    Returns:
        A tuple containing validity and the boolean end index when complete.
    """
    if not value_text:
        return True, None

    if value_text.startswith("true"):
        return True, 4

    # 途中用
    if "true".startswith(value_text):
        return True, None

    if value_text.startswith("false"):
        return True, 5

    # 途中用
    if "false".startswith(value_text):
        return True, None

    return False, None


# ==== Constrained Decoding を調整する関数 ====


def is_valid_function_call_prefix(
        generated_text: str,
        functions: list[FunctionDefinition],
        ) -> bool:
    """Check whether generated text can become a valid function call.

    Args:
        generated_text: Current decoded output prefix.
        functions: Available function definitions.

    Returns:
        True if the prefix can still become schema-compliant JSON,
        otherwise False.
    """
    for function in functions:
        # ==== 関数の選択 ====
        parameter_names = list(function.parameters.keys())
        function_prefix = (
            f'{{"name":"{function.name}",'
            f'"parameters":{{'
        )

        if function_prefix.startswith(generated_text):
            return True

        if not generated_text.startswith(function_prefix):
            continue

        # ==== パラメータの抽出 ====
        remaining_text = generated_text[len(function_prefix):]
        for parameter_index, parameter_name in enumerate(parameter_names):
            parameter_prefix = f'"{parameter_name}":'
            if parameter_index > 0:
                parameter_prefix = "," + parameter_prefix
            if parameter_prefix.startswith(remaining_text):
                return True
            if not remaining_text.startswith(parameter_prefix):
                return False

            remaining_text = remaining_text[len(parameter_prefix):]

            parameter_type = function.parameters[parameter_name].type
            value_text = remaining_text

            if parameter_type == "string":
                is_valid, end_index = is_valid_string_prefix(value_text)
            elif parameter_type == "number":
                is_valid, end_index = is_valid_number_prefix(value_text)
            elif parameter_type == "boolean":
                is_valid, end_index = is_valid_boolean_prefix(value_text)
            else:
                return False

            if not is_valid:
                return False

            if end_index is None:
                return True

            remaining_text = value_text[end_index:]

        expected_suffix = "}}"
        if expected_suffix.startswith(remaining_text):
            return True

        return False
    return False


def get_valid_token_ids(output_ids: list[int],
                        functions: list[FunctionDefinition],
                        llm: Small_LLM_Model,
                        logits_len: int
                        ) -> list[int]:
    """Return token IDs that preserve the function-call constraint.

    Args:
        output_ids: Token IDs generated so far.
        functions: Available function definitions.
        llm: Model wrapper used for decoding token candidates.
        logits_len: Number of candidate token IDs to check.

    Returns:
        Token IDs that keep the decoded output prefix valid.
    """
    valid_token_ids: list[int] = []
    current_text = llm.decode(output_ids)

    for token_id in range(logits_len):
        candidate_ids = output_ids + [token_id]
        candidate_text = llm.decode(candidate_ids)

        if candidate_text == current_text:
            continue

        if is_valid_function_call_prefix(candidate_text, functions):
            valid_token_ids.append(token_id)

    return valid_token_ids


def get_cached_token_text(token_id: int,
                          llm: Small_LLM_Model,
                          token_text_cache: dict[int, str]
                          ) -> str:
    """Decode one token ID and cache the result.

    Args:
        token_id: Token ID to decode.
        llm: Model wrapper used for decoding.
        token_text_cache: Cache from token ID to decoded text.

    Returns:
        Decoded token text.
    """
    if token_id not in token_text_cache:
        token_text_cache[token_id] = llm.decode([token_id])

    return token_text_cache[token_id]


def select_fast_constrained_token(output_ids: list[int],
                                  functions: list[FunctionDefinition],
                                  llm: Small_LLM_Model,
                                  logits: list[float],
                                  token_text_cache: dict[int, str]
                                  ) -> int | None:
    """Try to select a valid token from high-logit candidates first.

    Args:
        output_ids: Token IDs generated so far.
        functions: Available function definitions.
        llm: Model wrapper used for decoding candidates.
        logits: Model scores for the next token.
        token_text_cache: Cache from token ID to decoded text.

    Returns:
        A valid high-scoring token ID, or None if the fast path fails.
    """
    current_text = llm.decode(output_ids)
    top_token_ids = heapq.nlargest(
        4096,
        range(len(logits)),
        key=lambda token_id: logits[token_id]
    )

    for token_id in top_token_ids:
        token_text = get_cached_token_text(token_id, llm, token_text_cache)
        candidate_text = current_text + token_text

        if is_valid_function_call_prefix(candidate_text, functions):
            confirmed_text = llm.decode(output_ids + [token_id])
            if is_valid_function_call_prefix(confirmed_text, functions):
                return token_id
    return None


def generate_constrained_output(input_ids: list[int],
                                functions: list[FunctionDefinition],
                                llm: Small_LLM_Model
                                ) -> list[int]:
    """Generate one complete function-call JSON object token by token.

    Args:
        input_ids: Encoded prompt token IDs, extended during generation.
        functions: Available function definitions.
        llm: Model wrapper used for logits and decoding.

    Returns:
        Generated token IDs for a complete function call.

    Raises:
        ValueError: If no complete function call is generated in time.
    """
    output_ids: list[int] = []
    token_text_cache: dict[int, str] = {}
    max_generated_tokens = 100
    for _ in range(max_generated_tokens):
        logits = llm.get_logits_from_input_ids(input_ids)
        selected_token_id = select_fast_constrained_token(
            output_ids,
            functions,
            llm,
            logits,
            token_text_cache
        )
        if selected_token_id is None:
            valid_token_ids = get_valid_token_ids(
                output_ids,
                functions,
                llm,
                len(logits)
            )

            selected_token_id = select_constrained_token(
                logits,
                valid_token_ids
            )

        output_ids.append(selected_token_id)
        input_ids.append(selected_token_id)

        generated_text = llm.decode(output_ids)

        if is_complete_function_call(generated_text, functions):
            return output_ids

    raise ValueError("Could not generate a complete function call")

# ＝＝＝　生成後の確認用関数　＝＝＝


def parse_function_call(generated_text: str) -> dict[str, Any]:
    """Parse generated text as the expected function-call object.

    Args:
        generated_text: Decoded generated text.

    Returns:
        Parsed function-call dictionary.

    Raises:
        ValueError: If the JSON shape is not a function-call object.
        json.JSONDecodeError: If the text is not valid JSON.
    """
    function_call = json.loads(generated_text)

    if not isinstance(function_call, dict):
        raise ValueError("Function call must be a JSON object")

    if "name" not in function_call:
        raise ValueError("Function call must contain name")

    if "parameters" not in function_call:
        raise ValueError("Function call must contain parameters")

    if not isinstance(function_call["name"], str):
        raise ValueError("Function call name must be a string")

    if not isinstance(function_call["parameters"], dict):
        raise ValueError("Function call parameters must be an object")

    return function_call


def validate_function_call(
        function_call: dict[str, Any],
        functions: list[FunctionDefinition],
        ) -> bool:
    """Validate a parsed function call against available definitions.

    Args:
        function_call: Parsed function-call object.
        functions: Available function definitions.

    Returns:
        True if the name and parameters match a definition, otherwise False.
    """
    function_name = function_call["name"]

    for function_definition in functions:
        if function_definition.name == function_name:
            return validate_required_parameters(
                function_call["parameters"],
                function_definition,
            )

    return False


def is_complete_function_call(
        generated_text: str,
        functions: list[FunctionDefinition]
        ) -> bool:
    """Check whether generated text is a complete valid function call.

    Args:
        generated_text: Decoded generated text.
        functions: Available function definitions.

    Returns:
        True if the text is parseable and schema-compliant, otherwise False.
    """
    try:
        function_call = parse_function_call(generated_text)
    except (json.JSONDecodeError, ValueError):
        return False

    return validate_function_call(function_call, functions)


# ＝＝＝　生成後の後処理　＝＝＝

def decode_result_to_function_call(
        result: list[int],
        functions: list[FunctionDefinition],
        llm: Small_LLM_Model,
        ) -> dict[str, Any]:
    """Decode generated token IDs into a validated function call.

    Args:
        result: Generated token IDs.
        functions: Available function definitions.
        llm: Model wrapper used for decoding.

    Returns:
        Validated function-call dictionary.

    Raises:
        ValueError: If the decoded function call does not match a definition.
    """
    generated_text = llm.decode(result)

    function_call = parse_function_call(generated_text)

    if not validate_function_call(function_call, functions):
        raise ValueError("Generated function call does not match definitions")

    return function_call
