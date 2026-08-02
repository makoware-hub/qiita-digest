---
name: review
description: 実装・テストが一区切りついたときにコードレビューを行う。「レビューして」「実装を確認して」「PR 前に見て」と言われたら、code-reviewer サブエージェントに直接頼むのではなく必ずこのスキルを使うこと。コードの修正はしない。
disallowed-tools: Edit, Write
---

# レビュー

実体は code-reviewer サブエージェントへの委任。直接委任せずこのスキルを挟むのは、
code-reviewer 自身の指示に `docs/design/` への言及がなく、**対象範囲と設計文脈をこちらで補って渡す**ぶんレビュー精度が上がるため。

## 手順

1. レビュー対象範囲を確認する。指示があればそれに従う。指示が無ければ、code-reviewer 自身の `git status` / `git diff` による検出に任せ、ここで二重に特定しない。
2. 対象サービスに対応する `docs/design/error_handling.md` / `idempotency.md` など関連ファイルを探す。
3. Agent ツールで code-reviewer サブエージェントに委任する。委任タスクには対象範囲と、2 で見つけた関連 `docs/design/` のパスを明示する（code-reviewer 自身の指示には `docs/design/` への言及がないため、ここで補う）。
4. 返ってきたレポートをそのまま提示する。重大な指摘があれば、implement / unit-test スキルに戻って修正することをユーザーに案内する。

## 守ること

- レポートの指摘を薄めたり、このスキル側の判断を上乗せしすぎない。
- コードの修正はしない（code-reviewer 自身の制約の再掲）。
- 対象範囲の特定に迷ったらユーザーに確認する。
