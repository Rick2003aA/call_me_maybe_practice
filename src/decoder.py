import json

from llm_sdk import Small_LLM_Model
from typing import Any

from .models import Prompt, FunctionDefinition, validate_required_parameters
from .prompt_builder import build_prompt


def generate_greedy_output(
        input_ids: list[int],
        llm: Small_LLM_Model) -> list[int]:

    # generate response
    output_ids = []
    for _ in range(100):
        logits = llm.get_logits_from_input_ids(input_ids)
        selected_token_id = max(range(len(logits)), key=lambda i: logits[i])
        output_ids.append(selected_token_id)
        input_ids.append(selected_token_id)

        text = llm.decode(output_ids).strip()
        if text.startswith("{") and text.count("{") == text.count("}"):
            break

    return output_ids


def generate_outputs(functions: list[FunctionDefinition],
                     prompt_items: list[Prompt],
                     llm: Small_LLM_Model) -> list[list[int]]:
    # 各プロンプトに対してオリジナルのプロンプトを作成してencodeする
    results = []
    for item in prompt_items:
        prompt = build_prompt(functions, item)
        encoded_prompt = llm.encode(prompt)
        input_ids = encoded_prompt[0].tolist()
        output = generate_greedy_output(input_ids, llm)
        results.append(output)

        # 1プロンプト分が終わったタイミングで出力
        print(llm.decode(output), flush=True)
        print("---", flush=True)

    return results


def parse_function_call(generated_text: str) -> dict[str, Any]:
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


def decode_result_to_function_call(
        result: list[int],
        llm: Small_LLM_Model,
        ) -> dict[str, Any]:
    """生成されたトークンIDをFunction Callの辞書へ変換する。"""
    generated_text = llm.decode(result)
    return parse_function_call(generated_text)


def validate_function_call(
        function_call: dict[str, Any],
        functions: list[FunctionDefinition],
        ) -> bool:
    """関数名、パラメータ名、パラメータ値の型が正しいか検証する。"""
    function_name = function_call["name"]

    for function_definition in functions:
        if function_definition.name == function_name:
            return validate_required_parameters(
                function_call["parameters"],
                function_definition,
            )

    return False
