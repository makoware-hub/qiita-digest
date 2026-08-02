---
name: unit-test
description: 実装済みのコードに対する単体テストを tests/<service>/ に書き、docs/tests/unit_test_spec.md を更新する。「テスト書いて」「単体テスト追加して」「pytest 通して」と言われたときや、implement スキルでコードを書き終えた直後に使うこと。
---

# 単体テスト

## 手順

1. 対象の `src/<service>/` と、対応する `docs/design/error_handling.md`（例外一覧）・`docs/design/data.md`（S3 キー・DynamoDB スキーマ等、モックデータの形の根拠）を確認する。
2. `tests/<service>/` に、`src/<service>/` とファイル単位で対応するテストを作成・更新する。AWS 呼び出しは moto、Qiita API と Bedrock は必ずモックする。
3. `test_raise` を使って、カスタム例外全種の異常系を網羅する。
4. `.claude/rules/unit_test.md` のテンプレートに沿って `docs/tests/unit_test_spec.md` を更新する。
5. `uv run pytest` / `uv run ruff check .` / `uv run mypy .` がすべて green であることを確認する。

## 守ること

- 実装コードは変更しない。バグを見つけたら報告し、修正は implement スキルの領分として扱う。
- 課金が発生する AWS 呼び出し・実 Bedrock 呼び出しをテストに含めない。
- `tests/` と `src/` の 1:1 対応構造を崩さない。
