---
name: implement
description: docs/design/ の決定に沿って src/<service>/ にコードとステートマシン定義を実装する。「実装して」「ロジックを書いて」「〇〇サービスを実装して」のように、動く処理そのものを求められたときに使うこと。対象の構成単位が未作成なら scaffold スキルで雛形を作ってから実装する。雛形（ファイル構成）だけでよい場合はこのスキルではなく scaffold を直接使うこと。
---

# 実装

## 手順

1. 対象サービスの `docs/design/architecture.md` / `statemachine.md` / `data.md` / `error_handling.md` / `idempotency.md` を確認する。無ければ design スキルを先に使うようユーザーに促す。
2. `src/<service>/` が未作成なら、scaffold スキルを使って雛形一式を作る。
3. `.claude/rules/lambda.md` / `stepfunctions.md` / `sam.md` / `eventbridge.md` に従って、handler・例外・バリデーション・ASL 定義・`template.yaml` を実装する。
4. `uv run ruff check .` / `uv run ruff format .` / `uv run mypy .` と、ASL 定義の妥当性確認（`.claude/rules/sam.md` 参照）をローカルで通す。
5. 設計と食い違いが出た場合は、先に `docs/design/` を design スキルで更新してから実装を続ける。
6. 実装が完了したら、次は unit-test スキルでテストを書くことをユーザーに案内する。

## 守ること

- アプリケーションログを個々の Lambda から出さない、Catch を安易に使わない、環境依存値を直書きしないなど、CLAUDE.md のアーキテクチャ原則に反するコードを書かない。
- `docs/design/` にない独自判断をしない。設計と乖離したら先に design へ差し戻す。
- テストの本実装は unit-test スキルの領分。ここでは scaffold 由来の最低限のテスト以上を作り込まない。
