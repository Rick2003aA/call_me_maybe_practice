# call me maybe 作業メモ

## 現在の目的

`Small_LLM_Model` を使って、自然言語プロンプトから Function Call JSON を生成するCLIを完成させる。

最終的には以下で動かす。

```sh
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json
```

出力は JSON の list。

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

## 今日できたこと

constrained decoding の中心部分がかなり進んだ。

特に `src/decoder.py` のここ。

- `is_valid_string_prefix()`
- `is_valid_number_prefix()`
- `is_valid_boolean_prefix()`
- `is_valid_function_call_prefix()`
- `get_valid_token_ids()`
- `generate_constrained_output()`

実際に全プロンプトで JSON 生成までできた。

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

つまり、JSON構造と schema-compliant という意味ではかなり前進している。

## constrained decoding の仕組み

LLMに全部自由に出させて、最後に検査するだけではない。

今の流れ:

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

要するに、

```text
間違ったJSONを後で落とす
```

ではなく、

```text
間違ったJSONになるtokenをそもそも選ばせない
```

という設計。

## is_valid_function_call_prefix() の考え方

この関数は「完成したJSONか」ではなく、

```text
この文字列は、まだ正しいFunction Call JSONになれる途中か？
```

を見る。

今の parser は左から順番に読む。

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

## value_text / index / end_index の意味

`value_text` は parameter の値部分から始まる文字列。

例:

```text
value_text = "123}}"
```

`index` は `value_text` の中で今見ている位置。

numberの場合:

```text
123}}
   ↑
   numberを読み終わった次の位置
```

この位置が `end_index`。

そのあと、

```python
remaining_text = value_text[end_index:]
```

で値の後ろを取り出す。

例:

```text
value_text = "123}}"
end_index = 3
remaining_text = "}}"
```

## 重要だった理解

`1}` は False ではない。

理由:

```text
1   -> number としてOK
}   -> JSONの閉じカッコ途中
1}  -> あと } が来れば完成できる
1}} -> 完成
```

つまり `}` を許可しているのは `is_valid_number_prefix()` ではない。

値を読んだあとに、

```python
expected_suffix = "}}"
expected_suffix.startswith(remaining_text)
```

で `}` や `}}` を許可している。

## 現在の既知問題

### 1. regex の意味が間違うケースがある

最後の方の regex 系で、JSONとしては正しいが意味が違う出力が出た。

例:

```json
{"regex":"[a-zA-Z]+","replacement":"dog"}
```

本当は、

```text
Substitute the word 'cat' with 'dog'
```

なら、

```json
{"regex":"cat"}
```

が期待値に近い。

原因候補:

- `prompt_builder.py` の regex hint に引っ張られている
- `word` という表現から `[a-zA-Z]+` を選んでしまっている

修正方針:

`prompt_builder.py` の regex 指示を強くする。

入れたい内容:

```text
If the prompt asks to replace a specific quoted word or literal text,
use that exact text as the regex.

Do not use broad patterns like [a-zA-Z]+ unless the user explicitly asks
to replace all words.
```

### 2. 出力JSONが1行になる

原因:

```python
json.dump(results, f)
```

`json.dump()` はデフォルトだと1行で出力する。

修正方針:

```python
json.dump(results, f, indent=2)
```

必要なら:

```python
json.dump(results, f, indent=2, ensure_ascii=False)
```

### 3. data/output がないと落ちる可能性

`data/output` が存在しない状態で出力しようとすると、ファイル作成で落ちる可能性がある。

修正方針:

```python
output_dir = os.path.dirname(output_path)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)
```

これは `save_results()` に入れるのが自然。

## 次にやること

今日は README / Makefile / flake8 などの雑務より、コード本体を優先する。

次の優先順位:

1. `prompt_builder.py` の regex 指示を修正する
2. regex 系の最後の2〜3件だけ再実行する
3. `save_results()` の `json.dump()` に `indent=2` を入れる
4. `data/output` がない場合の作成処理を入れる
5. `json_loader.py` のエラー処理をちゃんと書く
6. 全件再実行する

後回しでよいもの:

1. Makefile
2. README提出用の英語化
3. flake8
4. mypy

## パフォーマンスについて

今の constrained decoding は遅い。

理由:

```python
for token_id in range(logits_len):
    candidate_ids = output_ids + [token_id]
    candidate_text = llm.decode(candidate_ids)
```

毎step、全token候補を試して、毎回 decode している。

これは重いが、今は理解しやすくて検証しやすい。

余裕があれば将来やる改善:

- 毎回 full decode しない
- parser の状態を持つ
- 途中で候補functionを絞る
- token_id から token文字列を見て差分だけ判定する

ただし今は提出優先なので、

```text
遅いけど正しい
```

を優先する。

## 要件との関係

この方針は課題要件に沿っている。

理由:

- LLMが関数名を選んでいる
- if文やキーワード判定で関数選択していない
- constrained decoding で invalid token を除外している
- JSON構造と parameter type を生成中に制約している
- 最後に `parse_function_call()` と `validate_function_call()` で安全確認している

今の残り課題は主に、

```text
意味的な精度
出力ファイルまわり
エラー処理
提出用整備
```

であって、constrained decoding の中心は一旦かなり進んでいる。
