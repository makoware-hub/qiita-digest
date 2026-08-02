---
paths:
  - "tests/**/*.py"
  - "docs/tests/unit_test_spec.md"
---

# 単体テストルール

`tests/<service>/` に書く単体テストと、`docs/tests/unit_test_spec.md` の書き方を定める。

## 目的・位置づけ

- 単体テストは `.github/workflows/ci.yml` で push・PR のたびに自動実行される。ローカルで完結し、実 AWS 環境や実 Bedrock 呼び出しに依存しない。
- `tests/<service>/` は `src/<service>/` とファイル単位でミラーする既存構造（`.claude/rules/lambda.md` 参照）。新しいファイルを `src/` に追加したら、対応するテストファイルも `tests/` に作る。

## テスト方針

- AWS 呼び出しは `moto` でモックする。Qiita API と Bedrock は必ずモックし、テスト実行で課金・外部通信を発生させない。
- カスタム例外は `test_raise`（`.claude/rules/lambda.md` 参照）を使って強制発生させ、正常系だけでなく異常系（`exceptions.py` の全クラス）を網羅する。
- `validate_event.py` は分岐（必須パラメータ欠落・空値）ごとにテストケースを用意する。

## unit_test_spec.md の章立て

サービスごとに、観点（正常系 / バリデーションエラー / カスタム例外別）を行、対応するテストファイル・関数名を列で並べたマトリクス形式にする。実装が先行してテストが後付けになった場合も、このファイルを見ればカバレッジの抜けが一目でわかるようにする。

## カバレッジの最低ライン

- `validate_event.py` の全分岐（必須パラメータ欠落・空文字・空白のみ）
- `exceptions.py` の全カスタム例外クラス
- `test_raise` 経由の `RuntimeError`（マップにない値を渡した場合の想定外エラー経路）

## 完了条件

- `uv run pytest` / `uv run ruff check .` / `uv run mypy .` がすべて green。
- 新規・変更した `src/<service>/` の各ファイルに対応するテストが存在する。
