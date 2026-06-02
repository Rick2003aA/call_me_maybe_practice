from llm_sdk import Small_LLM_Model
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


if __name__ == "__main__":
    main()
