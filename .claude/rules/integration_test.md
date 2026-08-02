---
paths:
  - "tools/run_integration_test.py"
  - "docs/tests/integration_test_spec.md"
  - "docs/tests/integration_test_cases.md"
---

# 結合テストルール

dev 環境にデプロイ済みのスタックに対する結合テストの進め方と、`docs/tests/integration_test_spec.md` / `integration_test_cases.md` の書き方、`tools/run_integration_test.py` の責務を定める。

## 目的・位置づけ

- 単体テストは AWS リソース間の結合（IAM 権限・ステートマシンの実際の遷移・EventBridge の検知等）を検証できない。結合テストはこれを実リソースに対して確認する。
- CI では自動実行しない。実 AWS 環境・認証情報・Bedrock 呼び出しの課金が発生するため、手動実行に限る。

## 実行環境・前提

- dev 環境がデプロイ済みであること。
- `.claude/rules/deployment.md` の初回セットアップ（Bedrock モデルアクセスの有効化とユースケース申請）が完了していること。未完了だと `ResourceNotFoundException` で全呼び出しが失敗する。

## integration_test_spec.md の章立て

シナリオ単位で書く。最低限含めるシナリオ:

- 正常系の一気通貫（親ステートマシンの起動から通知までが成功する）
- 異常系が FAILED に到達し、EventBridge 経由で通知されることの確認
- Redrive による復旧の確認（`.claude/rules/stepfunctions.md` の Redrive 制約を踏まえる）

## integration_test_cases.md の書式

ケースごとに、ケース ID・前提データ・実行方法・期待結果・後始末を書く。「後始末」は、このリポジトリの全処理が冪等（`docs/design/idempotency.md`）であることを前提に、同じ `run_date` で再実行すれば上書きされ後始末不要になる設計を基本とする。

## tools/run_integration_test.py との関係

- `template.yaml` の `Outputs`（親ステートマシンの ARN・バケット名等、`.claude/rules/sam.md` 参照）から実行対象を取得する。
- このファイルが定義する責務の実装であり、シナリオ追加時はスクリプトも合わせて更新する。

## 完了条件

- `integration_test_spec.md` の全シナリオを実行し、結果を記録している。
- 実行前に Bedrock 呼び出し等のコスト発生をユーザーに明示している。
