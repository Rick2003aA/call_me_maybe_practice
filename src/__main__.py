from llm_sdk import Small_LLM_Model
from typing import Any
import argparse
import json

from .json_loader import load_function_definitions, load_prompt_items
from .decoder import generate_outputs, decode_result_to_function_call


def save_results(results: list[dict[str, Any]], output_path: str) -> None:
    """Function Callの結果をJSONファイルへ書き込む。"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f)


# 結果をJSONファイルに書き出す
# 結果をJSONファイルに書き出す
def main() -> None:
    # LLMモデルを用意する
    llm = Small_LLM_Model()

    # =========================
    # 1. 材料を読み込む
    # =========================

    parser = argparse.ArgumentParser()

    parser.add_argument('--functions_definition',
                        default='data/input/functions_definition.json')
    parser.add_argument('--input',
                        default='data/input/function_calling_tests.json')
    parser.add_argument('--output',
                        default='data/output/function_calling_results.json')

    args = parser.parse_args()

    # 関数定義JSONを読み込む(インスタンス化)
    functions = load_function_definitions(args.functions_definition)

    # テスト用のプロンプトJSONを読み込む（インスタンス化）
    prompt_items = load_prompt_items(args.input)

    # =========================
    # 2. LLMを使ってJSONを作ってもらう
    # ここで生成されるのは各テストプロンプトに対するtokenのlist[list[]]
    # =========================
    output_ids_list = generate_outputs(functions, prompt_items, llm)

    function_call_results = []
    for item, output_ids in zip(prompt_items, output_ids_list):
        function_call = decode_result_to_function_call(output_ids,
                                                       functions,
                                                       llm)
        function_call_results.append({
                "prompt": item.prompt,
                "name": function_call["name"],
                "parameters": function_call["parameters"]
        })

    # # =========================
    # # 3. 結果をdecodeして辞書に変換してからJSONファイルに書き出す
    # # =========================
    save_results(function_call_results, args.output)


if __name__ == "__main__":
    main()
