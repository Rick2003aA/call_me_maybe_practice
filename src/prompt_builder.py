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
    prompt = (
        "Return exactly one JSON object for a function call.\n"
        "Choose the best function from the list and fill all parameters.\n"
        "Return no markdown, no explanation, no extra text.\n\n"
        "Available functions:\n"
    )

    for function in functions:
        parameters = ", ".join(
            f"{name}:{definition.type}"
            for name, definition in function.parameters.items()
        )
        prompt += (
            f"- {function.name}({parameters}): "
            f"{function.description}\n"
        )

    prompt += (
        "\nExtraction rules:\n"
        "- Copy quoted text without the surrounding quote marks.\n"
        "- Keep literal words and phrases literal.\n"
        "- Do not add punctuation that is not part of the value.\n"
        "- For source_string, use the full text being edited.\n"
        "- For regex, output a regex pattern, not a natural-language label.\n"
        "- For replacement, use only the new replacement text.\n"
        "- For a named set of characters, use a regex character class.\n"
        "- If the request replaces each matching character, match one "
        "character at a time.\n"
        "- For a specific word, phrase, or symbol, "
        "use that literal target.\n\n"
        "- If the same target appears multiple times, regex is still only "
        "one occurrence of that target.\n\n"
        "Word replacement example:\n"
        "Request: Substitute the word 'red' with 'blue' in "
        "'red car and red bus'\n"
        'Parameters: {"source_string":"red car and red bus",'
        '"regex":"red","replacement":"blue"}\n\n'
        "Replacement mapping:\n"
        "- asterisks -> *\n\n"
        'Output format: '
        '{"name":"function_name","parameters":{"key":"value"}}\n'
        f"User prompt: {prompt_item.prompt}\n"
        "Output:\n"
    )

    return prompt
