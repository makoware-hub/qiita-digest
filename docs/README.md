# ドキュメント索引

プロジェクトに依存しない勉強メモ・記事原稿・検証コードはこのリポジトリに置かない（`../../tech-notes/` `../../articles/` `../../sandbox/` へ）。
**ファイルを追加・削除したら、同じ作業の中でこの索引を更新する。**

規約（技術規約・SDLC の進め方）は `.claude/rules/` に置く。該当ファイルを扱うときに自動で読み込まれるため、ここには置かない（一覧は `.claude/README.md` 参照）。

## 要件・設計 `docs/design/`

このシステムが何をどう作るかの決定を残す。実装で迷ったらここに立ち返る。`requirements` スキルが requirements.md を、`design` スキルが architecture.md / statemachine.md / data.md / error_handling.md / idempotency.md を作成・更新する（現時点では雛形段階のため未作成）。

まだ 1 本も作成されていない（`requirements` / `design` スキルの初回実行時に作られる）。予定されるファイル: `requirements.md` / `architecture.md` / `statemachine.md` / `data.md` / `error_handling.md` / `idempotency.md`

## テスト仕様 `docs/tests/`

`unit-test` / `integration-test` スキルが作成・更新する。

まだ 1 本も作成されていない。予定されるファイル: `unit_test_spec.md` / `integration_test_spec.md` / `integration_test_cases.md`

## 解説 `docs/guides/`

本プロジェクトの規約・実コードにリンクする技術解説。

まだ無し（ファイルを追加したらここに 1 行追記する）。

## 開発記録 `docs/notes/`

まだ無し（`errors_and_fixes.md` 等を置いたらここに 1 行追記する）。
