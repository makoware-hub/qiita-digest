---
paths:
  - "docs/design/{architecture,statemachine,data,error_handling,idempotency}.md"
---

# 設計ルール

`docs/design/` 配下の5ファイル（`architecture.md` / `statemachine.md` / `data.md` / `error_handling.md` / `idempotency.md`）に何を書くかを定める。

## 位置づけ

このファイルが扱うのは「何を・どのファイルに書くか」というプロセスであり、Step Functions の記法や Lambda のコーディング規約といった技術的な書き方は、既存の `.claude/rules/stepfunctions.md` / `lambda.md` / `sam.md` / `eventbridge.md` がそれぞれ定める。設計書はそれらの規約に従って書き、技術規約の内容をここに再定義しない。

## 5ファイルの役割分担

| ファイル | 書く内容 |
| --- | --- |
| `architecture.md` | システム全体の構成、親子ステートマシンと Lambda の一覧、コンポーネント間の依存関係 |
| `statemachine.md` | サービスごとの業務的な状態遷移・分岐条件（技術的な記法は `.claude/rules/stepfunctions.md` に従う） |
| `data.md` | S3 キー設計、DynamoDB スキーマ、状態間で運ぶ値の形 |
| `error_handling.md` | 業務エラーの分類と、Retry / FAILED のどちらに倒すかの判断（方針自体は `.claude/rules/stepfunctions.md` の「エラーハンドリング方針」に従う） |
| `idempotency.md` | サービスごとの冪等性の実現方法（S3 上書き・DynamoDB 条件付き書き込み・SNS 通知の重複防止など） |

## 進め方

1. `docs/design/requirements.md` の対象セクションを読み、スコープと受け入れ基準を確認する。
2. `.claude/rules/stepfunctions.md` / `lambda.md` / `sam.md` / `eventbridge.md` の制約内に収まる設計にする。規約を満たせない設計になりそうなら、要件のスコープ自体を見直す。
3. 既存サービス（fetch_feed / select_articles / summarize / publish_digest 等）の設計と粒度・命名を揃える。
4. 5ファイルのうち、変更が必要なものだけを更新する。サービスを1つ追加するたびに5ファイルすべてへ大きな変更が入るとは限らない。

## 完了条件

- 実装者が `docs/design/` だけを読んで着手できる粒度になっている（実装中に都度要件定義まで遡らなくてよい）。
- AWS の仕様・上限値に言及する場合は出典 URL が併記されている。
- 5ファイルの記述が既存サービスの設計と矛盾していない。

## 変更管理

実装中に設計との乖離が見つかった場合、コードを設計に無理やり合わせるのではなく、先に `docs/design/` を更新してから実装を続ける。乖離を放置すると `.claude/rules/unit_test.md` に基づくテスト設計にも影響する。
