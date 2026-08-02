---
paths:
  - "**/*.asl.json"
  - "docs/design/statemachine.md"
---

# Step Functions 設計ルール

## 親子の分割

- **親（`src/orchestrator/`）は各子ステートマシンを呼ぶだけ**。業務判断のための `Choice` やデータ加工を持たない。
- 子の呼び出しは `arn:aws:states:::states:startExecution.sync:2` を使う。`:2` なしの `.sync` は使わない — `:2` は子の出力と `Cause` を JSON で返すため、`$parse()` でそのまま扱えるため。
- **親・子とも Standard ワークフロー**にする。Express は Redrive できない。
- 子は「1 つの処理フェーズ」を担当し、2〜4 ステート程度の実体を持たせる（単一 Lambda のラッパにしない）。

## ペイロード上限（256KB）

Step Functions のステート入出力には 256KB の上限がある。Qiita の記事本文は 1 件で 6KB を超えるため、本文を状態に載せると数十件で破綻する。

- **ステート間で運ぶのは S3 キー・件数・日付などの小さな値だけ**。可変長データを `Output` に載せない。
- `Map` の入力も本文の配列ではなく **S3 キーの配列**にする。
- 1 ステートの出力は数 KB を超えない設計にする。超えそうなら S3 に置いてキーだけ返す。

## クエリ言語

- 定義はトップレベルで `"QueryLanguage": "JSONata"` を指定する。JSONPath（`Parameters` / `ResultPath` / `InputPath`）は使わない。
- 式は `{% ... %}` で記述し、`$states.input` / `$states.result` / `$states.errorOutput` を使う。
- Task の入力は `Arguments`、出力は `Output` で記述する。Lambda 呼び出しの出力は `"Output": "{% $states.result.Payload %}"` とし、Lambda のレスポンスだけを次のステートへ渡す。

## 変数（Assign）

- 複数ステートで使い回す値は `Assign` で変数化する（例: `$run_date`）。
- 省略可能な入力パラメータのデフォルト値は `$exists()` で補完する:

```json
"Assign": {
  "run_date": "{% $exists($states.input.run_date) ? $states.input.run_date : $substring($now(), 0, 10) %}"
}
```

## エラーハンドリング方針

優先順位は「**Retry（一時障害）→ FAILED（それ以外すべて）**」。このリポジトリにはフォールバック先が無いので、**Catch は原則書かない**。

### Retry — 一時的エラーのみ

- Lambda 呼び出しには AWS 側の一過性エラーに対する Retry を必ず付ける:

```json
"Retry": [
  {
    "ErrorEquals": [
      "Lambda.ServiceException",
      "Lambda.AWSLambdaException",
      "Lambda.SdkClientException",
      "Lambda.TooManyRequestsException"
    ],
    "IntervalSeconds": 10,
    "MaxAttempts": 3,
    "BackoffRate": 2
  }
]
```

- 外部要因の一時エラー（Qiita の 429、Bedrock のスロットリング）は、対応するカスタム例外名に対して個別に Retry を付ける。バックオフは長めにとる。
- 業務エラー（対象 0 件・バリデーション違反）にはリトライを設定しない。リトライで解決しないものを再実行するだけ無駄なため。

### Catch — 原則禁止

- `States.ALL` でのキャッチは禁止。想定外エラーまで握りつぶし、EventBridge 通知と Redrive が機能しなくなる。
- フォールバック先が実在する場合に限って使い、`Comment` に「何をキャッチし、なぜ他のエラーはキャッチしないか」を日本語で必ず書く。
- 補足: AWS 公式は `Catch(States.ALL)` → `Assign` でエラー情報を変数化 → `Fail` ステートで分かりやすい `Cause` を組み立てる「ユーザーフレンドリーなエラーメッセージ」パターンも紹介している（[Handling errors in Step Functions workflows](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)）。だがこのリポジトリでは意図的に使わない。理由は Redrive の実効性: 公式の [Redrive behavior of individual states](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html) によると、Task ステートの失敗（Catch せず例外を投げっぱなしにした場合）は Redrive すると「タスクが再スケジュールされ実際に再実行される」のに対し、Fail ステートに到達した失敗（Catch → Fail で誘導した場合）は Redrive すると「Fail ステートに再突入して同じ理由でまた失敗するだけ」で、意味のある復旧にならない。**Catch を避けて例外を投げっぱなしにすることが、Redrive を実効的な復旧手段にするための必須条件**。EventBridge 通知にも Catch は不要: `Step Functions Execution Status Change` イベントは実行ステータスが `FAILED` になった時点で Step Functions 側が自動送出し（[Automating Step Functions event delivery with EventBridge](https://docs.aws.amazon.com/step-functions/latest/dg/eventbridge-integration.html)）、`notify_failure` Lambda が引く `GetExecutionHistory` も Catch の有無に関わらずタスクの失敗を記録している（`eventbridge.md` 参照）。

### FAILED — 上記以外はすべて

- カスタム例外・想定外エラーは Catch せず実行を FAILED にする。EventBridge ルール（`eventbridge.md`）が検知して通知する。
- Lambda が正常終了し、その戻り値が業務的な失敗（対象 0 件など）を示す場合、親から分類したいときは Catch を挟まず `Choice` で判定して直接子SM の末尾の `Fail` ステートへ遷移させ、`Error` / `Cause` を JSONata で詰める（Lambda の例外を Catch して Fail に誘導するのではない。それだと Redrive しても Fail ステートに再突入して同じ結果を繰り返すだけになる — 上の Catch セクション参照）。親側は `$parse($states.errorOutput.Cause)` で取り出す。
- 復旧はデータや権限の問題を解消したあと **Redrive** で行う。ステートマシン側に再実行ロジックを作り込まない。

## Redrive の制約（設計時に必ず考慮する）

出典: [Restarting state machine executions with redrive](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html) / [Redriving Map Runs](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-map-run.html)

- Redrive できるのは **直近 14 日以内**に失敗・中断・タイムアウトした Standard ワークフローの実行だけ。
- **実行履歴が 25,000 イベントを超えた実行は Redrive できない**。長時間・大量 Map の設計時はこの上限を意識する。
- Redrive は失敗したステートから再開し、成功済みステートの結果と履歴は保持されたまま再実行されない。
- `Map` を含む親を Redrive すると、**失敗した子ワークフロー実行がまとめて再実行される**（成功した分は再実行されない）。
- **親子構成の落とし穴**: 子の Redrive 可否は子自身の 14 日ウィンドウで判定される。親がまだ Redrive 可能でも、先に閉じた子が期限切れで Redrive できないことがある。復旧は「気付いたら早めに」を運用ルールにする。
- 子SM は Redrive 時に**新しい実行として起動される**。したがって子の処理は必ず冪等でなければならない（`docs/design/idempotency.md`）。

## ログ

- ステートマシン内で通知やアプリログを出さない。各子は `{phase, status, counts, artifacts}` の構造化サマリを `Output` で返し、**親が `log_writer` Lambda を呼んで一箇所に集約する**。

## その他

- `TimeoutSeconds` をトップレベルに必ず設定する（処理内容に応じた値）。
- `Comment` はトップレベルとステート単位に日本語で書く。特にエラーハンドリングの判断理由を残す。
- エラーメッセージの整形には `$parse($error_cause).errorMessage` のように `$parse()` で Cause（JSON 文字列）を展開し、`$exists()` でフォールバックを用意する。
- 定義ファイルは `src/<service>/statemachine/<service>.asl.json`。ARN のような環境依存値は書かず、SAM の `DefinitionSubstitutions` で差し込む。
