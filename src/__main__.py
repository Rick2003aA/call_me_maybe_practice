from llm_sdk import Small_LLM_Model
from .json_loader import load_function_definitions, load_prompt_items
from .prompt_builder import build_prompt
# from .decoder import process


# 結果をJSONファイルに書き出す
def main():
    llm = Small_LLM_Model()
    # 材料を整える
    functions = load_function_definitions("data/input/functions_definition.json")
    # prompts = load_prompt_items("data/input/function_calling_tests.json")
    # print(prompts)
    # 材料をLLMに渡す
    # process(input_ids)
    build_prompt(functions, llm)


if __name__ == "__main__":
    main()
