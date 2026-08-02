---
paths:
  - "template.yaml"
  - "samconfig.toml"
---

# AWS SAM テンプレート設計ルール

## 基本方針

- **テンプレートは `template.yaml` の 1 枚**。ネストスタックは使わない（規模的に不要で、読みづらくなるため）。
- 環境（`dev` / `prod`）の切り替えは `Parameters` の `Env` と `samconfig.toml` の `--config-env` で行う。テンプレートを環境ごとに分けない。
- 検査は `sam validate --lint` と `cfn-lint template.yaml` の両方を CI で回す。

## Lambda Function

- **全 Function で `CodeUri: src/` を共有し、`Handler: <service>.handler.lambda_handler` で切り替える**。これにより `src/` 配下の絶対 import がテストと実行時で一致する（`lambda.md` 参照）。
- 共通設定は `Globals` にまとめる:

```yaml
Globals:
  Function:
    Runtime: python3.14
    Architectures: [arm64]
    Timeout: 60
    MemorySize: 256
    Environment:
      Variables:
        ENV: !Ref Env
        DATA_BUCKET: !Ref DataBucket
```

- 関数名は `FunctionName: !Sub "qiita_digest_<service>_${Env}"`。
- IAM は `Policies` で最小権限を宣言する。`AdministratorAccess` や `*` リソースを書かない。S3 は該当バケット、DynamoDB は該当テーブルに限定する。

## ステートマシン

- `AWS::Serverless::StateMachine` を使い、定義は外部ファイルを参照する:

```yaml
FetchFeedStateMachine:
  Type: AWS::Serverless::StateMachine
  Properties:
    Name: !Sub "qiita_digest_fetch_feed_${Env}"
    Type: STANDARD          # Redrive のため必須。EXPRESS にしない
    DefinitionUri: src/fetch_feed/statemachine/fetch_feed.asl.json
    DefinitionSubstitutions:
      FetchFeedFunctionArn: !GetAtt FetchFeedFunction.Arn
    Policies:
      - LambdaInvokePolicy:
          FunctionName: !Ref FetchFeedFunction
```

- **`.asl.json` に ARN を直書きしない**。`${...}` プレースホルダを置き `DefinitionSubstitutions` で差し込む。
- 親が子を `.sync:2` で呼ぶ場合、親のロールには子への `states:StartExecution` / `states:DescribeExecution` / `states:StopExecution` と、`events:PutRule` / `events:PutTargets`（マネージドルール用）が必要になる。`StepFunctionsExecutionPolicy` では足りないので明示する。

## パラメータと環境依存値

- **アカウント ID・バケット名・ARN・トークンをテンプレートに直書きしない**（このリポジトリは将来 public にする）。
- 環境ごとに変わる値は `Parameters` で受け、`samconfig.toml` の `parameter_overrides` で渡す。
- 秘密情報は SSM Parameter Store（SecureString）に置き、パラメータ名だけを環境変数で渡して実行時に取得する。テンプレートに値を書かない。
- S3 バケット名は衝突を避けるため `!Sub "qiita-digest-${Env}-${AWS::AccountId}"` のように組み立てる（`AWS::AccountId` は擬似パラメータなので直書きに当たらない）。

## 命名

- 論理 ID は PascalCase（`FetchFeedFunction`）、生成されるリソース名は snake_case + 環境サフィックス（`qiita_digest_fetch_feed_dev`）。
- S3 バケットと DynamoDB テーブルは kebab-case（`qiita-digest-dev-...`）。AWS の命名制約に合わせる。

## その他

- `sam build` の対象は `CodeUri` 配下すべて。`.asl.json` も zip に含まれるが数 KB なので許容する。
- スタックの削除保護は `prod` のみ有効にする。
- 出力（`Outputs`）には結合テストで使う ARN（親ステートマシン・バケット名）を並べ、`tools/run_integration_test.py` から参照できるようにする。
