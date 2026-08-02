# qiita-digest

Qiita の指定タグから新着記事を収集し、Amazon Bedrock（Claude Haiku 4.5）で要約して、日次ダイジェストを S3 と SNS へ配信する Step Functions ジョブ群。
親ステートマシンが 4 つの子ステートマシンをオーケストレーションする構成で、AWS SAM と GitHub Actions（OIDC）でデプロイする。

> **現在のステータス: 設計フェーズ（実装はこれから）**
>
> このリポジトリで確定しているのは **規約・設計ルールと Claude Code の運用設定** で、`src/` 配下の実装コードと `template.yaml`・`bootstrap/` はまだありません。
> 以下に出てくるサービス名・ディレクトリ構成は「これから実装する対象」として設計済みのものです。
>
> Claude Code のコンテキスト設計（`CLAUDE.md` / `.claude/rules/` / `.claude/skills/` / `.claude/agents/` / hooks）の実例として公開しています。
> そちらが目的なら [.claude/README.md](.claude/README.md) から読むのが早いです。

## 構成

親（`orchestrator`）が以下の子ステートマシンを順に呼ぶ。コードと定義は `src/<サービス>/`、テストは `tests/<サービス>/`。

| サービス | 役割 |
| --- | --- |
| `fetch_feed` | 対象タグごとに Qiita API から新着記事を取得して S3 へ保存（タグ単位で Map 並列） |
| `select_articles` | 処理済み記事との重複排除・いいね数/期間でのフィルタ |
| `summarize` | 記事ごとに Bedrock で要約（記事単位で Map 並列） |
| `publish_digest` | Markdown ダイジェストを生成して S3 へ出力し SNS 通知 |

親が横断的に使う Lambda（子ステートマシンではない）:

| Lambda | 役割 |
| --- | --- |
| `log_writer` | 各子が返した構造化サマリを親が集約して一箇所へ書き出す（個々の Lambda はアプリログを出さない） |
| `notify_failure` | EventBridge が実行失敗を検知したときに、実行履歴から情報を補完して通知する |

- 規約・設計ルール: [CLAUDE.md](CLAUDE.md) と [docs/README.md](docs/README.md)（ドキュメント索引）
- 要件・設計は `docs/design/`、テスト仕様は `docs/tests/`

## 開発環境

ローカルの開発ツール（pytest・ruff・mypy）は uv で管理する:

```powershell
uv sync              # .venv 作成 + 開発ツール導入（uv.lock どおり）
uv run pytest        # テスト実行
uv run ruff check .  # Lint
uv run ruff format . # 整形
uv run mypy .        # 型チェック
```

- Python は **3.14**。`.python-version` と Lambda ランタイム `python3.14` を一致させる
- テストは `pyproject.toml` の `pythonpath = ["src"]` により `from fetch_feed.handler import ...` の形で Lambda を import する（Lambda 実行時も `CodeUri: src/` なので同じ import 文が通る）
- ランタイム依存は増やさない方針（boto3 は Lambda ランタイム同梱）。必要になったら `[dependency-groups]` に宣言し `uv export` で `src/requirements.txt` を生成する（手書きしない）
- push / PR で GitHub Actions（[.github/workflows/ci.yml](.github/workflows/ci.yml)）が ruff（lint・format）・mypy・pytest を自動実行する
- Claude Code のフック・スキル・サブエージェントは [.claude/README.md](.claude/README.md) を参照
- [.mcp.json](.mcp.json) で [AWS Knowledge MCP Server](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server) を project スコープで接続している（認証不要のリモートサーバー。ローカルに導入物は増えない）。AWS の仕様・制限値はこれで裏取りしてから書く

## デプロイ

AWS SAM + GitHub Actions（OIDC で AssumeRole。長期キーは持たせない）。手順は [.claude/rules/deployment.md](.claude/rules/deployment.md) を参照（設計のみ。ワークフローと `bootstrap/` は未作成）。

## ライセンス

[MIT License](LICENSE)
