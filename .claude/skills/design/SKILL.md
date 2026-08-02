---
name: design
description: docs/design/requirements.md を踏まえて architecture.md / statemachine.md / data.md / error_handling.md / idempotency.md を作成・更新する。「設計して」「ステートマシンの構成を考えて」「このエラーは Retry と FAILED どっちにする?」「冪等性どう担保する?」と言われたときや、要件が固まって実装に入る前に使うこと。
---

# 設計

## 手順

1. `docs/design/requirements.md` の対象セクションの有無を確認する。無ければ requirements スキルを先に使うようユーザーに促す。
2. `.claude/rules/stepfunctions.md` / `lambda.md` / `sam.md` / `eventbridge.md` の技術規約の制約内で設計する。
3. `.claude/rules/design.md` の役割分担表に沿って、`docs/design/architecture.md` / `statemachine.md` / `data.md` / `error_handling.md` / `idempotency.md` のうち必要なファイルを作成・更新する。
4. 既に設計済みのサービスがあれば、粒度・命名をそれに揃える（対象は README.md のサービス表: fetch_feed / select_articles / summarize / publish_digest）。まだ 1 つも無い段階なら、規約に忠実な最小形を基準にする。
5. `docs/README.md` の索引を更新する。
6. 設計が固まったことをユーザーに伝え、次は implement スキルで実装に進むことを案内する。

## 守ること

- 技術的な「書き方」（JSONata 記法・Retry 設定・IAM 最小権限等）をここで再定義せず、既存の `.claude/rules/` 該当ファイルを参照する形にとどめる。
- AWS の仕様・上限値は記憶で書かず、aws-knowledge MCP で公式ドキュメントを引いて裏取りし、出典 URL を併記する（CLAUDE.md の共通規約）。
- このスキルではコードを書かない。
