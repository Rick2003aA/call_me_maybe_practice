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
