from .models import FunctionDefinition, Prompt


# ここで最初にLLMに渡す全てを準備する
# 渡すもの：
# 1. 自分で考えたプロンプト
# 2. 関数一覧（JSONファイルを読める形にする）
# 3. 42公式から配布された元プロンプト（JSONファイルを読める形にする）
def build_prompt(
        functions: list[FunctionDefinition],
        prompt_item: Prompt,
        ) -> str:
    prompt = "Return ONLY one valid JSON object. "\
        "Choose the best function from the list and fill every required "\
        "parameter using values extracted from the user prompt. "\
        "Do not leave parameters empty unless the function has no parameters. "\
        "Do not explain. DO NOT write Answer:.\n"

    prompt += f"User prompt: {prompt_item.prompt}\n"
    prompt += "Available functions:\n"

    for function in functions:
        prompt += f"Function Name: {function.name}\n"
        prompt += f"Description: {function.description}\n"
        prompt += f"Parameters: {function.parameters}\n"

    prompt += "Parameter rules:\n"

    for function in functions:
        prompt += f"{function.name}: {function.parameters}\n"

    prompt += "Regex hints: numbers use [0-9]+, vowels use [aeiouAEIOU], "\
        "literal words use the word itself.\n"
    prompt += 'Output format: {"name": "<function_name>", "parameters": {...}}\n'
    prompt += "Output:\n"

    return prompt


def build_function_schema(functions: list[FunctionDefinition]) -> dict:
    """生成するFunction Callを制約するJSONスキーマを作成する。"""
    raise NotImplementedError


def format_function_description(function_definition: FunctionDefinition) -> str:
    """1つの関数定義をLLMのプロンプトに含める形式へ整形する。"""
    raise NotImplementedError


def build_output_format_instruction(functions: list[FunctionDefinition]) -> str:
    """必要なFunction Callの出力形式を説明する指示文を作成する。"""
    raise NotImplementedError
