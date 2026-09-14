# Claude Code クラウド環境（claude.ai/code）のガイド

このリポジトリを Claude Code on the web（クラウドセッション）から操作する際に知っておくべき、ローカル環境との違いと制限のまとめ。出典は Anthropic 公式ドキュメント。

## 1. ユーザーレベル設定・メモリは引き継がれない

クラウドセッションは毎回フレッシュな VM で立ち上がり、リポジトリを新規 clone するだけなので、**自分のマシンにしかないものは何も引き継がれない**。

| 項目 | クラウドで使えるか | 理由 |
|---|---|---|
| リポジトリの `CLAUDE.md` / `.claude/settings.json` のフック / `.mcp.json` / `.claude/rules/` / `.claude/skills,agents,commands` | **○** | git clone に含まれる |
| ユーザーの `~/.claude/CLAUDE.md` | **✗** | 自分のマシンにあるだけでリポジトリに含まれない |
| ユーザーの `~/.claude/skills,agents,commands` | **✗** | 同上。使いたいならリポジトリの `.claude/` にコミットする |
| ユーザースコープでのみ有効化したプラグイン（`~/.claude/settings.json` の `enabledPlugins`） | **✗** | リポジトリ側の `.claude/settings.json` に書くか、claude.ai アカウントで同期プラグインとして有効化する |
| `claude mcp add`（デフォルト local / user スコープ）で追加した MCP サーバー | **✗** | `~/.claude.json` に書かれるため。`--scope project` で `.mcp.json` に書いてコミットする |
| 対話型認証（AWS SSO など） | **✗** | ブラウザログインが必要な認証はクラウドセッションでは実行不可 |
| **auto memory（`MEMORY.md`）** | **✗**（そのマシン限定） | `~/.claude/projects/<project>/memory/` に保存されるマシンローカルなストレージ。"Files are not shared across machines or cloud environments." |
| 組織の managed CLAUDE.md（`/etc/claude-code/CLAUDE.md` など、デバイスに配布したファイル） | **✗** | Anthropic 管理 VM 上では読めない。ただし `managed-settings.json` の `claudeMd` キー（サーバー配信）は反映される |

このリポジトリの `CLAUDE.md` / `.claude/rules/deployment.md` / `.claude/skills/` は git 管理下にあるため、クラウドセッションでもそのまま有効。`aws-knowledge` MCP が使えるのも `.mcp.json` がコミットされているから成立している。

出典: [How Claude remembers your project](https://code.claude.com/docs/en/memory) / [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments)

## 2. その他のローカル環境との主な違い

- **VM は使い捨て**: 非アクティブが続くと VM が回収される（"Environment expired"）。再開すると会話履歴は復元されるが、実行中だったバックグラウンドプロセス（サブエージェント・シェルコマンド）は復元されない。
- **リソース上限**: 目安で 4 vCPU / 16GB RAM / ディスク 30GB。超えるビルド・テストはタスクが停止する可能性あり。
- **GitHub 認証はプロキシ経由**: 実トークンはセッション VM に入らない。`git push` はセッションの作業ブランチにしか通らない。GraphQL は PR ワークフロー用の限定操作のみ（Projects v2 等は不可）。
- **環境変数は平文共有**: その環境を使う人なら誰でも読める。秘密情報は入れない。
- **設定変更のタイミング**: 環境変数・許可ドメインの変更は「新しく開始するセッション」にのみ反映され、実行中セッションには反映されない。
- **`NODE_EXTRA_CA_CERTS` や mTLS 用環境変数は無視される**: クラウド側が API 接続を管理しているため。
- **共有時の注意**: セッションを Public/Team 共有すると、プライベートリポジトリのコードや認証情報が含まれうる。

出典: [Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web) / [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments)

## 3. ネットワークアクセス制限

**環境（environment）単位**の設定であり、セッション単位で個別設定するものではない。1セッションは必ず1つの環境に紐づき、その設定を引き継ぐ。「セッションごとに変えたい」場合は、レベルの異なる環境を複数用意し、セッション作成時にどれを使うか選ぶ。

| レベル | 内容 |
|---|---|
| `None` | 外部通信は一切不可 |
| `Trusted`（デフォルト） | npm・PyPI・GitHub・主要クラウド SDK など許可リスト済みドメインのみ |
| `Full` | 任意のドメインに到達可能 |
| `Custom` | 自分で許可ドメインを列挙（"Also include default list" で Trusted の許可リストも維持可） |

レベルに関わらず常に到達可能なもの:

- GitHub（専用プロキシ経由）
- 有効化した MCP コネクタ（Anthropic サーバー経由の通信のため。このリポジトリの `aws-knowledge` MCP はこれに該当）
- 登録済みの API credentials のホスト（後述、一部除く）
- Anthropic API 自体

出典: [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments)

## 4. API credentials

- **Pro / Max プランのみ**（Team / Enterprise は未対応。Team/Enterprise では外部 API キーは環境変数に置くしかない）
- 組織の admin ロールが必要
- **既存の環境にしか追加できない**（新規作成ダイアログには項目がない）
- 手順: 環境の編集画面 → **API credentials** → **Add credential** → Name / Allowed websites（ホスト） / Credential type（デフォルト Bearer）/ Custom headers にキーを入力 → **Connect**
- 保存後は値を再表示できない（変更するには削除して作り直す）
- エージェントプロキシが登録ホスト宛のリクエストにのみキーを付与する。**キーは Claude 本体にもセッションの環境変数にも見えない**。ネットワークアクセスが `None` でも登録ホストへは届く（ただし GitHub・`api.anthropic.com`・主要パッケージレジストリ・セットアップスクリプト実行中は対象外）
- 登録すると、その環境を使う全セッション・全ユーザーに有効

出典: [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments)

## 5. 設定画面へのアクセス方法

環境の作成・編集は UI操作であり、リポジトリやセッション内から変更するものではない。

### Web（claude.ai/code）— 唯一すべての設定ができる場所

1. https://claude.ai/code を開く
2. メッセージ入力欄の**すぐ上の行**にある、現在の環境名が書かれた**雲アイコン**をクリック
3. **Local** / **Cloud** のメニューが開く。既存環境にマウスを乗せると出る**歯車アイコン**から編集、または **Add cloud environment** で新規作成
4. 編集ダイアログに **Network access** / **Environment variables** / **Setup script** があり、既存の Pro/Max 環境の編集画面にのみ **API credentials** が出る（新規作成ダイアログにはない）

専用の設定ページや直接開ける URL は無く、必ずこの雲アイコン経由。

### Team/Enterprise の組織共有環境

Owner 権限者が https://claude.ai/admin-settings の **Cloud environments** ページで作成・編集。組織のデフォルト環境の指定は https://claude.ai/admin-settings/claude-code 。

### デスクトップアプリ

セッション開始時の環境ドロップダウンから **Add cloud environment** で、ネットワークアクセスと環境変数を指定して**新規作成**は可能（web と同じ環境オブジェクトなので web からも見える）。ただし**既存クラウド環境の編集**や **API credentials** の設定導線はドキュメントに記載がない。

### モバイルアプリ

環境の作成・編集 UI は無い。リポジトリ・ブランチを選んでタスクを投げる、進行中セッションを見る・操作するだけのクライアント。設定変更が必要な場合はブラウザで claude.ai/code を開く。

| 操作 | モバイル | デスクトップ | Web |
|---|---|---|---|
| 新規クラウド環境の作成 | ✗ | ○ | ○ |
| 既存環境の編集 | ✗ | 未確認（記載なし） | ○ |
| API credentials | ✗ | 記載なし | ○ |

出典: [Claude Code on mobile](https://code.claude.com/docs/en/mobile) / [Desktop application](https://code.claude.com/docs/en/desktop) / [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments)

## 6. このリポジトリでの含意

- `CLAUDE.md` の「AWS の仕様・制限値を記憶で書かない」方針は `aws-knowledge` MCP（`.mcp.json` にコミット済み）で成立しており、ネットワークアクセスレベルに関係なく動作する。
- `.claude/rules/deployment.md` の「ローカルからのデプロイは原則行わない」方針は、そもそもクラウド環境に AWS SSO 等の対話型認証手段がなく構造的にも困難であることと整合している。デプロイは GitHub OIDC 経由の GitHub Actions で完結させる設計が、この制約と相性が良い。
- Team/Enterprise プランでは API credentials が使えないため、外部 API キーが必要になった場合は環境変数（誰でも読める）以外の選択肢が今のところ無い点に留意する。
