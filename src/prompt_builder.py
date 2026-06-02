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
        prompt += f"{function.name}\n"

    prompt += "Parameter rules:\n"

    for function in functions:
        prompt += f"{function.name}: {function.parameters}\n"

    prompt += "Regex hints: numbers use [0-9]+, vowels use [aeiouAEIOU], "\
        "literal words use the word itself.\n"
    prompt += 'Output format: {"name": "<function_name>", "parameters": {...}}\n'
    prompt += "Output:\n"

    return prompt
