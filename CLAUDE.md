# qiita-digest

Qiita の指定タグから新着記事を収集し、Amazon Bedrock で要約して日次ダイジェストを S3 と SNS へ配信する Step Functions ジョブ群。

## アーキテクチャ原則

1. **オーケストレーションは親ステートマシン、処理本体は子ステートマシン + Lambda**。親は各子を `.sync:2` で呼ぶだけで、業務ロジックを持たない。
2. **エラーは Step Functions 内で原則キャッチしない**。実行を FAILED のまま終わらせ、EventBridge ルールで検知して通知する（疎結合）。復旧は Redrive で行い、再実行ロジックをステートマシンに作り込まない。
3. **ステート間で運ぶのは S3 キーと件数だけ**。記事本文のような可変長データを状態に載せない（Step Functions のペイロード上限 256KB を超えるため）。本文は必ず S3 経由で読む。
4. **アプリケーションログを個々の Lambda から出さない**。各子は構造化サマリを `Output` で返し、親が `log_writer` Lambda を呼んで一箇所へ集約する。失敗時は EventBridge 経由の `notify_failure` が実行履歴から補完する。
5. **すべての処理を冪等にする**。同じ `run_date` で何度実行しても、S3 は同一キーへ上書き、DynamoDB は条件付き書き込み、SNS 通知は冪等性ガードで二重化させない。
6. **Retry は一時的エラーのみ**（スロットリング・AWS 側の一過性障害）。業務エラー・データ起因のエラーはリトライしても無駄なので即 FAILED にする。

## ディレクトリ構成

**コードと定義は `src/<サービス>/`、テストは `tests/<サービス>/` にミラーする**（雛形の「1 アプリ型」でも「構成単位型」でもない、このリポジトリ固有の形）。

```text
src/
├── common/              # 全 Lambda に同梱される共有モジュール（S3/DynamoDB・冪等性・ログ）
├── orchestrator/        # 親（Lambda を持たない構成単位）
│   ├── statemachine/orchestrator.asl.json
│   └── eventbridge/failure_notify.json
└── <service>/           # fetch_feed / select_articles / summarize / publish_digest
    ├── __init__.py
    ├── handler.py       # lambda_handler（処理フローのみ）
    ├── validate_event.py
    ├── exceptions.py
    ├── test_utils.py    # test_raise によるエラー強制発生
    └── statemachine/<service>.asl.json
tests/
├── conftest.py          # moto フィクスチャの共通化
└── <service>/           # src/<service>/ のファイルと対応させる
```

新しいサービスはこの形に従って作る（`/scaffold`）。この構成を成立させている設定は 2 つあり、どちらを外してもテストから Lambda を import できなくなる:

- SAM は全 Function で `CodeUri: src/`、`Handler: <service>.handler.lambda_handler`。
- `pyproject.toml` の `pythonpath = ["src"]`。`from common.s3_io import ...` の絶対 import が、テストでも Lambda 実行時でも同じ文のまま通る。

## 共通ディレクトリ

- `tools/` — 補助スクリプト（デプロイ対象外）。`bin/` は作らない。
- `docs/` — 横断ドキュメント（要件・設計 `design/`、テスト仕様 `tests/`、解説 `guides/`、開発記録 `notes/`）。索引は `docs/README.md`。
- 勉強メモ・記事原稿・使い捨て検証はこのリポジトリに置かない（`../../tech-notes/`、`../../articles/`、`../../sandbox/` へ）。

## 共通規約

- リージョンは `ap-northeast-1`。Python は **3.14**（`.python-version` と Lambda ランタイム `python3.14` を必ず一致させる）。
- 命名は snake_case。ステートマシンと Lambda は `qiita_digest_<service>_<env>`、EventBridge ルールは `qiita_digest_<service>_failure_notify_<env>`。
- **環境依存値（アカウント ID・バケット名・ARN・トークン）をコードと `template.yaml` に直書きしない**。SSM 参照か、デプロイ時の `--parameter-overrides`（値は GitHub の Variables / Secrets 側に置く）で渡す。**このリポジトリは public なので、`samconfig.toml` も追跡対象＝公開される**。アカウント ID・ARN を書かないこと。git 履歴に一度でも入ると実質消せない。
- Bedrock は boto3 `bedrock-runtime` から `jp.` 推論プロファイルを指定して呼ぶ（日本国内完結。Anthropic SDK の Mantle クライアントは推論プロファイル非対応）。
- ランタイム依存は増やさない方針。boto3 は Lambda ランタイム同梱なので `src/requirements.txt` は空を保つ。どうしても必要になったら `[dependency-groups]` に宣言し、`uv export` で生成する（手書きしない）。
- 開発ツールは uv で管理する（`uv run pytest` / `uv run ruff check .` / `uv run ruff format .` / `uv run mypy .`）。push すると GitHub Actions（`.github/workflows/ci.yml`）でも同じチェックが走る。
- **AWS の仕様・制限値を記憶で書かない**。上限値・対応リージョン・API の挙動を規約や設計書に書くときは、`aws-knowledge` MCP（`.mcp.json`・project スコープ・認証不要）で公式ドキュメントを引いて裏取りし、**出典 URL を併記する**。実際に「Redrive は 24 時間以内」と誤記したことがある（正しくは 14 日）。
- コメント・docstring・通知文は日本語で書く。Claude からの説明・報告も日本語で行う。
- 詳細ルールは `.claude/rules/` に置く。該当ファイル（`*.asl.json`・`src/**/*.py`・`docs/design/*.md` 等）を扱うときに自動で読み込まれる（一覧は `.claude/README.md` 参照）。
