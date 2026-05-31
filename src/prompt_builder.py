from .json_loader import load_function_definitions
from llm_sdk import Small_LLM_Model
from .models import FunctionDefinition


# ここで最初にLLMに渡す全てを準備する
# 渡すもの：
# 1. 自分で考えたプロンプト
# 2. 関数一覧（JSONファイルを読める形にする）
# 3. 42公式から配布された元プロンプト（JSONファイルを読める形にする）
def build_prompt(
        functions: list[FunctionDefinition],
        llm: Small_LLM_Model) -> None:
    function_names = []
    name_ids = []
    for function_name in functions:
        function_names.append(function_name.name)
        # print(f"Functions: {function_name.name}")
    print(f"Functions: {function_names}")
    for name in function_names:
        name_ids.append(llm.encode(name))
    print(f"IDs: {name_ids}")


# if __name__ == "__main__":
#     build_prompt()
