from llm_sdk import Small_LLM_Model
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
