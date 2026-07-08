*This project has been created as part of the 42 curriculum by rtsubuku.*

# call me maybe

## Description

`call me maybe` is a function-calling project for small language models.
The program reads natural-language prompts and a list of available function
definitions, then produces structured JSON function calls.

For example, given the prompt:

```text
What is the sum of 2 and 3?
```

the program should not calculate and return `5`. Instead, it should return a
machine-readable function call:

```json
{
  "prompt": "What is the sum of 2 and 3?",
  "name": "fn_add_numbers",
  "parameters": {
    "a": 2,
    "b": 3
  }
}
```

The main goal is to make the output valid, parseable, and schema-compliant even
when using a small LLM. The implementation uses the provided `llm_sdk`
`Small_LLM_Model` wrapper and applies constrained decoding during generation.

## Instructions

### Requirements

- Python 3.10 or later
- `uv`
- The provided `llm_sdk` directory at the repository root

The project dependencies are managed through `pyproject.toml` and `uv.lock`.
The reviewer can install them with:

```sh
uv sync
```

or:

```sh
make install
```

### Usage

Run the default input files:

```sh
uv run python -m src
```

Run with explicit paths:

```sh
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json
```

The default paths are:

- Function definitions: `data/input/functions_definition.json`
- Prompts: `data/input/function_calling_tests.json`
- Output: `data/output/function_calling_results.json`

The output file is generated at runtime. The `data/output/` directory is ignored
by Git and is not meant to be submitted.

### Makefile Commands

```sh
make install
```

Installs project dependencies with `uv sync`.

```sh
make run
```

Runs the main CLI with the default arguments.

```sh
make debug
```

Runs the program through Python's debugger.

```sh
make clean
```

Removes Python caches and local tooling caches.

```sh
make lint
```

Runs:

```sh
uv run flake8 .
uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

```sh
make lint-strict
```

Runs `flake8` and `mypy --strict`.

## Input Format

The function definition file must contain a JSON array. Each function has:

- `name`: function name
- `description`: natural-language description
- `parameters`: object mapping parameter names to their types
- `returns`: return type metadata

Example:

```json
[
  {
    "name": "fn_add_numbers",
    "description": "Add two numbers together and return their sum.",
    "parameters": {
      "a": {
        "type": "number"
      },
      "b": {
        "type": "number"
      }
    },
    "returns": {
      "type": "number"
    }
  }
]
```

The prompt file must contain a JSON array of objects with a `prompt` key:

```json
[
  {
    "prompt": "What is the sum of 2 and 3?"
  }
]
```

Malformed JSON, missing files, and invalid input shapes are reported with clear
error messages.

## Output Format

The program writes a JSON array. Each item contains exactly:

- `prompt`: the original prompt
- `name`: the selected function name
- `parameters`: the extracted arguments

Example:

```json
[
  {
    "prompt": "Greet john",
    "name": "fn_greet",
    "parameters": {
      "name": "john"
    }
  }
]
```

## Algorithm Explanation

The implementation uses constrained decoding instead of trusting the model to
freely generate valid JSON.

For each prompt, the program builds an instruction prompt containing:

- the available function names
- their parameter names and types
- extraction rules
- the user prompt
- the required output shape

The model is then asked to generate a compact JSON object shaped like:

```json
{"name":"function_name","parameters":{"key":"value"}}
```

During generation, the program does not accept arbitrary next tokens. It repeats
the following loop:

1. Send the current input token IDs to `Small_LLM_Model.get_logits_from_input_ids`.
2. Check the highest-scoring token IDs first.
3. Reuse cached single-token decode results when building candidate prefixes.
4. Confirm promising candidates with a full decode of the generated token IDs.
5. If no valid token is found in the fast path, fall back to checking every
   possible next token ID from the logits range.
6. Keep only tokens whose decoded text can still become a valid function-call
   JSON object.
7. Select the valid token with the highest logit score.
8. Append it to the generated output.
9. Stop when the generated text is complete JSON and matches the selected
   function schema.

The prefix validator enforces the following structure:

```text
{"name":"<known function name>","parameters":{...}}
```

It also validates parameter order, parameter names, and supported parameter
types:

- `number`
- `string`
- `boolean`

After generation, the output is parsed with `json.loads` and checked again
against the selected `FunctionDefinition` Pydantic model. This second validation
step ensures that only schema-compliant function calls are written to the final
output file.

## Design Decisions

### Pydantic Models

All structured project data is represented with Pydantic classes:

- `FunctionDefinition`
- `ParameterDefinition`
- `Prompt`

This keeps validation centralized and makes invalid input files easier to reject
with useful errors.

### Compact JSON Generation

The constrained decoder targets compact JSON without spaces. This reduces the
number of possible valid prefixes and makes the prefix parser simpler.

### LLM-Based Function Selection

The implementation does not select functions with keyword heuristics. The LLM
logits decide which valid token is preferred at each generation step. The
constraint layer only prevents invalid structure and schema violations.

### Graceful Error Handling

Input loading catches common file and JSON errors, then reports them as readable
`ValueError` messages. The CLI catches those errors and prints them to standard
error instead of crashing with a traceback.

## Performance Analysis

The implementation prioritizes correctness and JSON validity. On the included
test inputs, it produces valid JSON and schema-compliant function calls.

The current decoder first checks the top 4096 token IDs by logit score. It
caches the decoded text for individual token IDs, uses that cached text for a
quick prefix check, and only performs a full decode for candidates that still
look valid. If no valid token is found in this fast path, it falls back to the
complete vocabulary scan. This keeps the exact constrained-decoding behavior
while avoiding most full decode calls during normal generation.

Long outputs, especially functions with several string parameters, are still
slower than short arithmetic or greeting calls because each generated token
requires another model forward pass.

Possible optimizations include:

- precomputing valid literal prefixes for function names and parameter names
- using the vocabulary file directly for token filtering
- using model key-value caching to avoid recomputing the full prompt history at
  every generated token

## Reliability

The output is protected by two layers:

1. Prefix-level constrained decoding during generation.
2. Full JSON parsing and schema validation after generation.

This prevents malformed JSON from being written when generation succeeds. The
program also reports malformed input files, missing files, and invalid schemas
with clear messages.

Current limitations:

- The string prefix parser is intentionally simple and is best suited for normal
  JSON strings without complex escaping.
- The implementation supports the subject's common parameter types, but does not
  implement complex nested argument schemas.
- Runtime can increase for long string-heavy outputs.

## Challenges Faced

The main challenge was that small LLMs can choose the right function
semantically while still producing invalid or inconsistent JSON when prompted
normally. To solve this, generation was moved from free text output to
token-by-token constrained decoding.

Another challenge was extracting regex-related arguments. The model sometimes
over-produced regex syntax or included surrounding quote marks in string
parameters. The prompt rules were adjusted to clearly separate:

- the full source string
- the target regex
- the replacement text

The final validation step was added to catch any mismatch between generated
arguments and the function definition schema.

## Testing Strategy

The project was tested with the provided sample data in `data/input/`.

Checks performed:

- Running the default CLI:

```sh
uv run python -m src
```

- Running lint and type checks:

```sh
make lint
```

- Inspecting the generated JSON output.
- Confirming each result contains only `prompt`, `name`, and `parameters`.
- Confirming selected function names exist in the definition file.
- Confirming parameter names and value types match each function definition.
- Testing arithmetic, greeting, string reversal, square root, and regex
  replacement prompts.

Additional useful edge cases:

- missing input files
- invalid JSON files
- empty prompt arrays
- strings with punctuation
- negative and decimal numbers
- boolean parameters
- ambiguous prompts with similar function names

## Resources

Classic references used for this project:

- Python documentation: `argparse`, `json`, and file handling
- Pydantic documentation for data validation
- mypy documentation for static type checking
- flake8 documentation for style checking
- JSON specification and JSON object syntax
- General references on constrained decoding and structured generation for LLMs

AI assistance was used as a development aid for:

- reviewing the subject requirements
- organizing the project structure
- improving error handling
- checking README coverage against the subject
- discussing constrained decoding design and edge cases

All generated suggestions were reviewed and adapted before being included in the
project.
