Call me maybe

Function calling を実装する課題。
プロンプトに対してJSONフォーマットを遵守した出力をJSONファイルに書き出す。

全体の流れ
１プロンプト投げる
２LLMがJSONを作成
３JSONファイルに書き込む
４終了


JSONファイル
  ↓ 読み込む
Pythonのdict/list
  ↓ 整形する
LLMに渡すmessages
  ↓
LLMが「どの関数を呼ぶべきか」を判断
  ↓
function_call / tool_call が返る
  ↓
Python側で実際の関数を実行
  ↓
実行結果をLLMに返す
  ↓
最終回答を生成


現状（2026/06/01）
関数名とパラメータの抽出をすることができるようになった。
{"name": "fn_greet", "parameters": {"name": "shrek"}}
抽出の精度も申し分ない。今までなにに手こずってたのかわからないくらい精度が高い。
残りは、これらを組み合わせて書きを再現するだけ。

{
  "name": "fn_reverse_string",
  "description": "Reverse a string and return the reversed result.",
  "parameters": {
  "s": {
    "type": "string"
  }
},

prompt
  ↓
input_ids
  ↓
LLM
  ↓
logits
  ↓ ここで自分のコードが介入する
valid token だけ残す
  ↓
次tokenを選ぶ
  ↓
input_idsに追加
  ↓
繰り返し
