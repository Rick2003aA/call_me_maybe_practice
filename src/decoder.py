import json

from llm_sdk import Small_LLM_Model
from typing import Any

from .models import Prompt, FunctionDefinition, validate_required_parameters
from .prompt_builder import build_prompt


# ＝＝＝　生成系の関数　＝＝＝

def get_valid_token_ids() -> list[int]:
    """
    生成途中のテキストを見て、次に出して良いtoken_idだけ返す
    """
    pass


def select_constrained_token(
        logits: list[float],
        valid_token_ids: list[int]
        ) -> int:
    """
    logitsとvalid_token_idsを受け取り、有効なtoken_idの中で一番スコアが高いものを選ぶ
    """
    if not valid_token_ids:
        raise ValueError("No valid tokens available")

    return max(valid_token_ids, key=lambda token_id: logits[token_id])


def generate_constrained_output() -> list[int]:
    """
    generate_greedy_outputの上位互換
    """
    pass


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


# ＝＝＝　生成後の確認用関数　＝＝＝

def parse_function_call(generated_text: str) -> dict[str, Any]:
    '''
    出力された文字列が辞書として正しいかどうかを確認
    - dictかどうか
    - name, parameters keyが含まれるか
    - name, parametersのvalueがそれぞれstr, dictかどうか
    OK: function_call(JSON)を返す
    NG: ValueError
    '''
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
    """関数名、パラメータ名、パラメータ値の型が正しいか検証する。"""
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
    """
    生成されたテキストが正しい形かどうかを確認する
    上記2つのfunctionを組み合わせる
    """
    try:
        function_call = parse_function_call(generated_text)
    except (json.JSONDecodeError, ValueError):
        return False

    return validate_function_call(function_call, functions)


def decode_result_to_function_call(
        result: list[int],
        functions: list[FunctionDefinition],
        llm: Small_LLM_Model,
        ) -> dict[str, Any]:
    """生成されたtoken_id: list[int]をfunction_call: dict{str: Any}へ変換する。"""
    generated_text = llm.decode(result)

    function_call = parse_function_call(generated_text)

    if not validate_function_call(function_call, functions):
        raise ValueError("Generated function call does not match definitions")

    return function_call
