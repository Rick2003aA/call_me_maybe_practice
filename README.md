# call me maybe 引き継ぎメモ

## 2026/07/07 現在の作業方針

このリポジトリでは 42 課題 `call me maybe` を進めている。

最終目標は、`Small_LLM_Model` を使って自然言語プロンプトから Function Call JSON を生成するCLIを完成させること。

最終コマンド:

```sh
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json
```

出力形式:

```json
[
  {
    "prompt": "What is the sum of 2 and 3?",
    "name": "fn_add_numbers",
    "parameters": {
      "a": 2,
      "b": 3
    }
  }
]
```

## スレッドの役割分担

このREADMEを書いた時点で、今後は以下のように作業を分ける。

- このスレッド: `prompt_builder.py` のプロンプト修正・出力精度改善に特化する
- 別スレッド: プロジェクト本体を前に進める
  - `json_loader.py`
  - `__main__.py`
  - Makefile
  - README提出用英語化
  - flake8 / mypy
  - 最終CLI確認

別スレッドでは、プロンプト修正に深入りしすぎず、まず提出に必要なコード整備を進める。

## 現在できていること

`src/decoder.py` の constrained decoding 本体は大きく進んでいる。

実装済みの中心関数:

- `is_valid_string_prefix()`
- `is_valid_number_prefix()`
- `is_valid_boolean_prefix()`
- `is_valid_function_call_prefix()`
- `get_valid_token_ids()`
- `generate_constrained_output()`
- `parse_function_call()`
- `validate_function_call()`
- `decode_result_to_function_call()`

constrained decoding の流れ:

```text
generate_constrained_output()
  ↓
LLMから logits を取る
  ↓
get_valid_token_ids()
  ↓
候補tokenを1個ずつ output_ids に足して decode
  ↓
is_valid_function_call_prefix(candidate_text, functions)
  ↓
正しいJSONになれる途中なら True
  ↓
True の token だけ残す
  ↓
select_constrained_token()
  ↓
valid token の中で一番logitsが高いtokenを選ぶ
```

つまり、完成後に壊れたJSONを落とすだけではなく、生成中に invalid token を選ばせない設計。

## prefix parser の重要ポイント

`is_valid_function_call_prefix()` は「完成JSONか」ではなく、

```text
この文字列は、まだ正しいFunction Call JSONになれる途中か？
```

を判定する。

現在の読み方:

```text
function_prefix を読む
remaining_text を作る

for parameter:
  parameter名を読む
  parameter値を読む
  remaining_text を値の後ろへ進める

最後に }} を読む
```

例:

```json
{"name":"fn_add_numbers","parameters":{"a":2,"b":3}}
```

読み方:

```text
{"name":"fn_add_numbers","parameters":{
"a":
2
,"b":
3
}}
```

`value_text`, `index`, `end_index` の意味:

- `value_text`: parameter値から始まる文字列
- `index`: `value_text` の中で今見ている位置
- `end_index`: 値を読み終わった次の位置

例:

```text
value_text = "123}}"
end_index = 3
remaining_text = value_text[end_index:]  # "}}"
```

`1}` は False ではない。

```text
1   -> number としてOK
}   -> JSONの閉じカッコ途中
1}  -> あと } が来れば完成できる
1}} -> 完成
```

## 実行確認済みのこと

一度、全プロンプトで JSON 生成まで到達している。

出力例:

```json
{"name":"fn_add_numbers","parameters":{"a":2,"b":3}}
{"name":"fn_add_numbers","parameters":{"a":265,"b":345}}
{"name":"fn_greet","parameters":{"name":"shrek"}}
{"name":"fn_greet","parameters":{"name":"john"}}
{"name":"fn_reverse_string","parameters":{"s":"'hello'"}}
{"name":"fn_reverse_string","parameters":{"s":"'world'"}}
{"name":"fn_get_square_root","parameters":{"a":16}}
{"name":"fn_get_square_root","parameters":{"a":144}}
{"name":"fn_substitute_string_with_regex","parameters":{"source_string":"Hello 34 I'm 233 years old","regex":"[0-9]+","replacement":"NUMBERS"}}
```

JSON構造と parameter type という意味ではかなり通っている。

ただし、regex系は意味的な精度がまだ不安定。

## 現在のプロンプト状況

`src/prompt_builder.py` は現在、成功例を参考にした構造になっている。

現在の主な構成:

```text
You are a strict AI assistant designed for function calling.

[Available Functions]
json.dumps(function_data, indent=2)

[Rules]
1. available functions から選ぶ
2. function definition に基づいて required parameters を抽出する
3. literal values を generalize しない
4. quoted text は中身だけ使う
5. 余計な punctuation を足さない
6. valid JSON object だけ返す

[Regex Parameter Rules]
source_string / regex / replacement の役割を説明

[Output Format]
{"name": "function_name", "parameters": {"key": "value"}}

[User Prompt]
...
```

現在の regex ルール方針:

```text
When a function has source_string, regex, and replacement parameters:
- source_string is the full text to edit.
- regex is only the target part to find inside source_string.
- replacement is only the new text to insert.
- If the target is a broad class such as numbers or vowels, use a compact character class pattern.
- If the target is a specific word, phrase, symbol, or quoted value, use that literal target.
- Keep regex as short as possible while matching the requested target.
```

このプロンプト修正後の最新出力はまだ未確定。regex系2件を再実行して確認する必要がある。

## 最近の regex 問題

プロンプト修正前後で、以下のような問題が出ていた。

期待:

```json
{
  "source_string": "Programming is fun",
  "regex": "[aeiouAEIOU]",
  "replacement": "*"
}
```

実際に出た悪い例:

```json
{
  "source_string": "'Programming is fun'",
  "regex": ".+?([aeiouAEIOU])",
  "replacement": "*"
}
```

期待:

```json
{
  "source_string": "The cat sat on the mat with another cat",
  "regex": "cat",
  "replacement": "dog"
}
```

実際に出た悪い例:

```json
{
  "source_string": "'The cat sat on the mat with another cat'",
  "regex": ".+cat",
  "replacement": ".+dog"
}
```

原因として考えていること:

- `regex` という単語に小さいLLMが引っ張られ、過剰に regex 記号を足している
- 否定形ルールや `.+`, `.*`, `()` などの禁止例をプロンプトに出すと、逆にその記号に引っ張られる可能性がある
- そのため、現在は危険な具体記号をプロンプトから消し、`source_string / regex / replacement` の役割を肯定文で説明する方針に変更した

## 別スレッドで最初にやるべきこと

プロンプト確認をこのスレッドに任せるなら、別スレッドは以下から進める。

### 1. `__main__.py` の状態確認

`save_results()` に以下は入っている。

```python
output_dir = os.path.dirname(output_path)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
```

目的:

- `data/output` がない場合も落ちない
- 出力JSONを複数行で見やすくする

まず `python -m py_compile src/__main__.py` を通すこと。

### 2. `json_loader.py` の3関数を実装する

現在残っている未実装:

```python
load_json_file()
validate_function_definitions()
validate_prompt_items()
```

これらは絶対にこの名前で必要というより、課題要件の例外処理・入力検証を満たすために実装した方がよい。

役割:

```text
load_json_file()
  open + json.load
  FileNotFoundError / JSONDecodeError を ValueError などに変換

validate_function_definitions()
  data が list か確認
  各要素を FunctionDefinition にする
  pydantic の ValidationError を扱う

validate_prompt_items()
  data が list か確認
  各要素を Prompt にする
  pydantic の ValidationError を扱う
```

最終的には:

```python
def load_function_definitions(file_path: str) -> list[FunctionDefinition]:
    data = load_json_file(file_path)
    return validate_function_definitions(data)


def load_prompt_items(file_path: str) -> list[Prompt]:
    data = load_json_file(file_path)
    return validate_prompt_items(data)
```

に寄せるとよい。

### 3. `prompt_builder.py` の未使用関数を整理する

現在、下のような未実装関数が残っている可能性がある。

```python
build_function_schema()
format_function_description()
build_output_format_instruction()
```

使わないなら削除、使うなら最低限実装。

`raise NotImplementedError` が残っている状態は提出前に避けたい。

### 4. CLIとして最終確認

個別スクリプトではなく、最終的に必ずこれで確認する。

```sh
uv run python -m src
```

確認すること:

- `data/output/function_calling_results.json` が生成される
- JSONが list
- 各要素に `prompt`, `name`, `parameters` がある
- `name` が function definition に存在する
- `parameters` の key と type が定義と一致する

## 後回しでよいもの

コード本体が動いてからでよい。

- Makefile
- README提出用の英語化
- flake8
- mypy
- pycache / venv / 出力ファイルなどの整理

ただし提出前には必須。

## 注意: git status が汚れている

現時点で `git status --short` には多数の変更・未追跡ファイルが出ている。

特に注意:

- `src/__pycache__/...`
- `venv/...`
- `data/output/function_calling_results.json`
- `config/`

これらは提出物に含めるべきでない可能性が高い。

別スレッドで提出準備に入るときは `.gitignore` と不要ファイル整理を確認すること。

## 今日のゴール案

本体進行スレッドのゴール:

1. `json_loader.py` の未実装を消す
2. `__main__.py` の構文チェックを通す
3. `prompt_builder.py` の未実装関数を整理する
4. `uv run python -m src` で全件出力できる状態にする
5. 出力JSONが schema-compliant か確認する

プロンプト修正スレッドのゴール:

1. regex系2〜3件だけを再実行する
2. `source_string`, `regex`, `replacement` の精度を確認する
3. 必要なら `prompt_builder.py` の文言をさらに調整する
4. 改善したプロンプトを本体進行スレッドに共有する
