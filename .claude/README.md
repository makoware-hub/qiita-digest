# .claude — Claude Code プロジェクト設定

| パス | 役割 | コミット |
| --- | --- | --- |
| `settings.json` | チーム共有設定（言語・フック定義） | する |
| `settings.local.json` | 個人設定（権限の許可リスト等） | しない（.gitignore 済み） |
| `hooks/` | フックスクリプト本体（stdlib のみで書く） | する |
| `rules/<name>.md` | プロジェクト規約（パススコープで該当ファイルを扱うときだけ自動読み込み） | する |
| `skills/<name>/SKILL.md` | プロジェクト固有スキル | する |
| `agents/<name>.md` | プロジェクト固有サブエージェント（隔離コンテキストで動く委任ワーカー） | する |

## 入っているフック

- **PreToolUse** `hooks/protect_credentials.py` — `.env` / `*.pem` への書き込みをブロック
- **PostToolUse** `hooks/ruff_check.py` — 編集した `.py` に `uv run ruff check` を実行し、指摘を Claude に返す（uv 未導入ならスキップ）

## 入っているスキル

開発フローは requirements → design → implement（scaffold を内包）→ unit-test → integration-test → review の順。

- `skills/requirements/` — 要件を整理し `docs/design/requirements.md` を作成・更新する
- `skills/design/` — `docs/design/` の architecture / statemachine / data / error_handling / idempotency を作成・更新する
- `skills/implement/` — `docs/design/` の決定を `src/<service>/` に実装する。未作成のサービスは scaffold を呼び出す
- `skills/scaffold/` — CLAUDE.md の「ディレクトリ構成」に従って、新しい構成単位（ジョブ・サービス等）の雛形一式を生成する
- `skills/unit-test/` — `tests/<service>/` の単体テストと `docs/tests/unit_test_spec.md` を作成・更新する
- `skills/integration-test/` — dev 環境への結合テストを実施し `docs/tests/` と `tools/run_integration_test.py` を保守する
- `skills/review/` — 対象範囲と `docs/design/` の文脈を添えて code-reviewer サブエージェントへ委任する

## 入っている規約

`rules/*.md` に YAML frontmatter の `paths` で対象ファイルパターンを指定してある。Claude がそのパターンにマッチするファイルを読み書きするときだけ、そのルールが自動でコンテキストに読み込まれる（`paths` を書かなければ `CLAUDE.md` と同じく毎セッション常時ロードされる）。`deployment.md` はコマンド実行が中心でファイル編集を伴わずスコープしにくいため意図的に常時ロードにしてあり、他の8本は `paths` 指定済み。

- `rules/requirements.md` — `docs/design/requirements.md` を扱うときに読み込まれる。要件定義の書き方
- `rules/design.md` — `docs/design/` の設計書5ファイルを扱うときに読み込まれる。ファイルの役割分担
- `rules/stepfunctions.md` — `*.asl.json`・`docs/design/statemachine.md` を扱うときに読み込まれる。親子分割・JSONata・256KB 制限・Redrive の制約
- `rules/lambda.md` — `src/**/*.py`・`tests/**/*.py` を扱うときに読み込まれる。ファイル分割・カスタム例外・**アプリログを出さない**ルール
- `rules/sam.md` — `template.yaml`・`samconfig.toml` を扱うときに読み込まれる。`CodeUri: src/` 共有・環境依存値を直書きしない
- `rules/eventbridge.md` — `src/orchestrator/eventbridge/**`・`template.yaml` を扱うときに読み込まれる。失敗検知は親のみ
- `rules/unit_test.md` — `tests/**/*.py`・`docs/tests/unit_test_spec.md` を扱うときに読み込まれる。単体テストの方針
- `rules/integration_test.md` — `tools/run_integration_test.py`・`docs/tests/integration_test_spec.md` 等を扱うときに読み込まれる。結合テストの実施方法
- `rules/deployment.md` — **常時ロード**（`paths` 指定なし）。OIDC セットアップ・通常デプロイ・ロールバック

## 入っているサブエージェント

- `agents/code-reviewer.md` — 読み取り専用（`permissionMode: plan`）のコードレビュアー。「コードレビューして」と頼むと委任され、CLAUDE.md・`.claude/rules/` を根拠にしたレビューレポートだけが会話に返る。コードの修正はしない。`skills/review/` 経由でも委任される。

## 増やすときの型

- フック: `hooks/` に stdlib のみの Python スクリプトを追加し、`settings.json` の `hooks` に登録する。ブロック・指摘は exit 2 + stderr で返す。無関係なイベントでは exit 0 で静かに抜け、外部ツール不在時はスキップしてブロッカーにしない。
- ルール: `rules/<name>.md` を追加し、frontmatter の `paths` にそのルールが必要になるファイルパターン（glob）を書く。特定のファイル群に紐づかない内容（`deployment.md` のようにコマンド実行が中心のもの）に限り `paths` を省略し常時ロードにする。1 トピック 1 ファイルを保ち、既存規約との重複を作らない。
- スキル: `skills/<kebab-case名>/SKILL.md` を追加する。frontmatter の `description` には「いつ使うか」を書く（Claude はこれを見て読み込むか判断する）。**ツール制限（`allowed-tools` / `disallowed-tools`）は、制限すること自体に意味があるときだけ書く**。ここでは `review` だけが `disallowed-tools: Edit, Write` を持つ（レビューが勝手に直さないための歯止め）。他のスキルは実装・調査・MCP 参照と必要なツールが広く、先回りして絞ると後から壊れるので宣言しない。スキル固有の詳細ルール・チェックリストは SKILL.md に書き込まず、`rules/<name>.md` として上記の規約体系に一本化する。
- サブエージェント: `agents/<kebab-case名>.md` を追加する。対話が不要で結果レポートだけ欲しい定型ジョブに限る（会話履歴は渡らない）。`description` に「いつ委任するか」を書き、`tools`・`permissionMode` は最小権限にする。
