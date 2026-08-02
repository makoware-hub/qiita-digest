---
name: integration-test
description: dev 環境にデプロイ済みのスタックに対して結合テストを実施し、docs/tests/integration_test_spec.md / integration_test_cases.md を整備し tools/run_integration_test.py を実行・保守する。「結合テストして」「デプロイ後の動作確認して」「一気通貫で動かして確認して」と言われたときに使うこと。
---

# 結合テスト

## 手順

1. dev 環境がデプロイ済みであること、`.claude/rules/deployment.md` の前提セットアップ（Bedrock モデルアクセス等）が完了していることを確認する。
2. `docs/design/architecture.md`（全体構成）・`statemachine.md`（状態遷移）を確認し、シナリオ設計の土台にする。
3. `template.yaml` の `Outputs`（ステートマシン ARN・バケット名）を確認する。
4. `.claude/rules/integration_test.md` に沿って、正常系一気通貫・異常系の FAILED 到達と EventBridge 通知・Redrive 確認のシナリオを `docs/tests/integration_test_spec.md` / `integration_test_cases.md` に定義する。
5. `tools/run_integration_test.py` を作成・更新し実行して、結果を確認する。
6. 冪等性（`docs/design/idempotency.md`）を利用し、後始末なしで再実行可能な形にする。

## 守ること

- このスキルの中で `sam deploy` は実行しない。デプロイの実施は別判断であり、`.claude/rules/deployment.md` の領分。
- 実コスト（Bedrock 呼び出し等）が発生することを実行前に必ずユーザーへ明示する。
- CI では自動実行しない前提を崩さない。
