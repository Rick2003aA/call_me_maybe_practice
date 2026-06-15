from llm_sdk import Small_LLM_Model
from typing import Any

from .models import Prompt, FunctionDefinition
from .prompt_builder import build_prompt


def generate_output(
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


def decode_prompts(functions: list[FunctionDefinition],
                   prompt_items: list[Prompt],
                   llm: Small_LLM_Model) -> list[list[int]]:
    # 各プロンプトに対してオリジナルのプロンプトを作成してencodeする
    results = []
    for item in prompt_items:
        prompt = build_prompt(functions, item)
        encoded_prompt = llm.encode(prompt)
        input_ids = encoded_prompt[0].tolist()
        output = generate_output(input_ids, llm)
        results.append(output)

        # 1プロンプト分が終わったタイミングで出力
        print(llm.decode(output), flush=True)
        print("---", flush=True)

    return results


def get_valid_token_ids(
        generated_text: str,
        functions: list[FunctionDefinition],
        llm: Small_LLM_Model,
        ) -> list[int]:
    """生成途中のFunction Call JSONに続けられる有効なトークンIDを返す。"""
    raise NotImplementedError


def select_constrained_token(
        logits: list[float],
        valid_token_ids: list[int],
        ) -> int:
    """許可されたトークンIDの中からスコアが最も高いものを選択する。"""
    raise NotImplementedError


def is_complete_function_call(generated_text: str) -> bool:
    """生成テキストに完全なFunction Call JSONが1つ含まれるか判定する。"""
    raise NotImplementedError


def parse_function_call(generated_text: str) -> dict[str, Any]:
    """生成されたJSONテキストをFunction Callの辞書へ変換する。"""
    raise NotImplementedError


def validate_function_call(
        function_call: dict[str, Any],
        functions: list[FunctionDefinition],
        ) -> bool:
    """関数名、パラメータ名、パラメータ値の型が正しいか検証する。"""
    raise NotImplementedError


def generate_constrained_output(
        input_ids: list[int],
        functions: list[FunctionDefinition],
        llm: Small_LLM_Model,
        max_tokens: int = 100,
        ) -> list[int]:
    """次に選択できるトークンを制限しながらFunction Call JSONを生成する。"""
    raise NotImplementedError
