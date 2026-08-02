---
paths:
  - "src/orchestrator/eventbridge/**"
  - "template.yaml"
---

# EventBridge 設計ルール

## 役割

Step Functions の実行失敗を検知して通知するのは EventBridge の責務とする。
ステートマシン内に通知ロジックを組み込まない（疎結合）。これにより:

- ステートマシンは処理に専念でき、失敗時は素直に FAILED で終わる
- 通知先の変更・追加がステートマシンの変更なしにできる
- FAILED のまま残るため Redrive による復旧が可能

日次起動には EventBridge Scheduler を使う（ルールではなくスケジューラ。実行時刻のタイムゾーン指定とリトライ設定ができるため）。

## イベントパターン

- **失敗検知は親ステートマシンにだけ設定する**。子は親経由で失敗が伝播するので、子ごとにルールを作ると同じ障害で通知が多重に飛ぶ。
- イベントパターンは JSON ファイルとして `src/orchestrator/eventbridge/` 配下に保存し、`template.yaml` から参照する。
- 検知対象ステータスは `FAILED` / `TIMED_OUT` / `ABORTED` の 3 つ:

```json
{
  "source": ["aws.states"],
  "detail-type": ["Step Functions Execution Status Change"],
  "detail": {
    "status": ["FAILED", "TIMED_OUT", "ABORTED"],
    "stateMachineArn": ["${OrchestratorStateMachineArn}"]
  }
}
```

- `stateMachineArn` で必ず対象を絞る。アカウント内の全ステートマシンを拾うパターンは作らない。
- ARN は直書きせず、SAM 側で差し込む（`sam.md` 参照）。

## 命名

- ルール名・ファイル名は `qiita_digest_<service>_failure_notify`（snake_case）。SAM 側で `_${Env}` を付ける。

## 通知

- ターゲットは `notify_failure` Lambda。Lambda が `GetExecutionHistory` を引いて**どのステートでどのエラーが出たか**を特定し、整形して SNS へ publish する。
  - EventBridge のイベント本体には失敗ステート名が含まれないため、Input Transformer だけでは通知内容が不十分になる。Lambda を挟む理由はここにある。
- `notify_failure` は通知と同時に、失敗の事実を `log_writer` と同じロググループへ構造化ログとして書く（親が続行できず集約ログが途切れるため、その補完）。
- 通知メッセージにはエラー分類（カスタム例外名）・Cause・実行 ARN・Redrive 可否（Redrive 可能期間は 14 日。`stepfunctions.md` 参照）を含める。
- SNS 通知の Subject は `【エラー】` などの接頭辞で重要度を示す。
- 正常終了の通知が必要になったら別ルール（`<name>_success_notify.json`）として分け、失敗ルールに status を追加しない。
