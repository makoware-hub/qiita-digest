# デプロイ手順

**手順が未定義のままデプロイしない。** 変更したら必ずこのファイルを更新する。

このファイルは `paths` を指定せず常時ロードする。デプロイ作業はコマンド実行が中心でファイル編集を伴わないことが多く、特定ファイルへの `paths` スコープでは発火機会が乏しいため。

> **未実施**: このリポジトリは設計フェーズで、`bootstrap/github_oidc_role.yaml`・`template.yaml`・`.github/workflows/deploy.yml` はまだ存在しない。
> 以下は「実装時にこの手順で作る」という設計であり、実行済みの記録ではない。

## 全体像

```text
初回だけ（手動）        bootstrap/github_oidc_role.yaml を aws cloudformation deploy
                       └→ GitHub OIDC プロバイダ + デプロイ用 IAM ロール

以後（自動）            PR       → ci.yml     : ruff / mypy / pytest / sam validate / cfn-lint
                       main へ  → deploy.yml : OIDC で AssumeRole → sam build → sam deploy (dev)
```

長期の AWS アクセスキーを GitHub Secrets に置かない。認証は OIDC の一時クレデンシャルだけで行う。

## 初回セットアップ

1. **OIDC ロールを作る**（ローカルから 1 回だけ）:

   ```powershell
   aws cloudformation deploy `
     --template-file bootstrap/github_oidc_role.yaml `
     --stack-name qiita-digest-github-oidc `
     --capabilities CAPABILITY_NAMED_IAM `
     --parameter-overrides GitHubOwner=<owner> GitHubRepo=qiita-digest
   ```

   - 信頼ポリシーの `sub` は `repo:<owner>/qiita-digest:*` ではなく、**ブランチ・環境を絞った条件**にする（例: `repo:<owner>/qiita-digest:ref:refs/heads/main` と `repo:<owner>/qiita-digest:environment:dev`）。フォークからの実行でロールを引けないようにするため。
2. 出力されたロール ARN を GitHub の **Variables**（Secrets ではない。ARN は秘密情報ではないため）に `AWS_DEPLOY_ROLE_ARN` として登録する。
3. Bedrock のモデルアクセスを有効化し、**Anthropic のユースケース申請フォームを提出**する（未提出だと `ResourceNotFoundException` で全呼び出しが失敗する。反映まで約 15 分）。
4. 任意: Qiita のアクセストークンを SSM Parameter Store に SecureString で登録する（未登録なら未認証で動作。レート制限が 60 req/h → 1000 req/h に緩和される）。

   ```powershell
   aws ssm put-parameter --name /qiita-digest/dev/qiita_token --type SecureString --value "<token>" --region ap-northeast-1
   ```

## 通常のデプロイ

- **`dev`**: `main` への push で `deploy.yml` が自動実行される。手動実行は GitHub Actions の `workflow_dispatch` から。
- **`prod`**: `workflow_dispatch` で環境に `prod` を指定して実行する（自動デプロイしない）。GitHub Environments の承認を必須にする。
- ローカルからのデプロイは**原則行わない**（誰が何をデプロイしたか追えなくなるため）。デバッグでどうしても必要なときは `dev` に限る:

  ```powershell
  sam build
  sam deploy --config-env dev
  ```

## ロールバック

- CloudFormation のスタック更新は失敗時に自動ロールバックされる。`UPDATE_ROLLBACK_FAILED` になった場合のみ手動介入が必要。
- 正常にデプロイされたあとで問題が判明した場合は、**直前のコミットに revert して main へ push する**（前方復旧）。スタックを手で戻さない。
- スケジュール実行を止めたいときは EventBridge Scheduler を無効化する（スタックごと消さない）。

## デプロイ前チェック

デプロイ前に、以下がすべて通っていること:

- `uv run ruff check .` / `uv run ruff format --check .` / `uv run mypy .` / `uv run pytest`
- `sam validate --lint` / `cfn-lint template.yaml`
- 各 `.asl.json` が `aws stepfunctions validate-state-machine-definition` を通る
- 環境依存値（アカウント ID・ARN・トークン）がコードとテンプレートに直書きされていない
