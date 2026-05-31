from llm_sdk import Small_LLM_Model


def process(input_ids: list[int]) -> None:
    llm = Small_LLM_Model()
    given_text = """Return ONLY valid JSON.
    Do not explain.
    Do not write any text outside JSON.

    Answer:
    """
    encoded_text = llm.encode(given_text)

    print("=== Processing ===")
    input_ids = encoded_text[0].tolist()
    print(input_ids)

    # generate response
    response = []
    decoded_response = ""
    for _ in range(100):
        logits = llm.get_logits_from_input_ids(input_ids)
        selected_token_id = max(range(len(logits)), key=lambda i: logits[i])
        response.append(selected_token_id)
        input_ids.append(selected_token_id)
    print(response)
    for i in range(len(response)):
        answer = llm.decode(response[i])
        decoded_response += answer

    print("=== Response ===")
    print(decoded_response)
