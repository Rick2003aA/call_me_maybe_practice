from llm_sdk import Small_LLM_Model
from typing import Any

from .json_loader import load_function_definitions, load_prompt_items
from .decoder import decode_prompts


# 結果をJSONファイルに書き出す
# 結果をJSONファイルに書き出す
def main():
    # LLMモデルを用意する
    llm = Small_LLM_Model()

    # =========================
    # 1. 材料を読み込む
    # =========================

    # 関数定義JSONを読み込む(インスタンス化)
    functions = load_function_definitions("data/input/functions_definition.json")

    # テスト用のプロンプトJSONを読み込む（インスタンス化）
    prompt_items = load_prompt_items("data/input/function_calling_tests.json")

    # =========================
    # 2. LLMを使ってJSONを作ってもらう
    # =========================
    result = decode_prompts(functions, prompt_items, llm)
    print(result)

    # # =========================
    # # 3. 結果をJSONファイルに書き出す
    # # =========================
    # print(answer)


def decode_result_to_function_call(
        output_ids: list[int],
        llm: Small_LLM_Model,
        ) -> dict[str, Any]:
    """生成されたトークンIDをFunction Callの辞書へ変換する。"""
    raise NotImplementedError


def save_results(results: list[dict[str, Any]], output_path: str) -> None:
    """Function Callの結果をJSONファイルへ書き込む。"""
    raise NotImplementedError


def create_error_result(prompt: str, error: Exception) -> dict[str, str]:
    """処理に失敗したプロンプトについて保存可能なエラー結果を作成する。"""
    raise NotImplementedError


if __name__ == "__main__":
    main()


fuck

