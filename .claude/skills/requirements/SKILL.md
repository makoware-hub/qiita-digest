---
name: requirements
description: 新しい機能・変更の要件を整理し docs/design/requirements.md を作成・更新する。「要件を整理して」「〇〇を追加したいんだけどまず要件から」「これは何のためにやるんだっけ」のように目的・スコープが曖昧なまま設計や実装に進みそうなときに使うこと。requirements → design → implement → unit-test → integration-test → review という開発フローの入口。
---

# 要件定義

## 手順

1. 対象が既存サービスの変更か新規サービスかを確認する。
2. `docs/design/requirements.md` が既にあれば読み、既存の要件との差分を意識する。
3. 目的・スコープ（やる/やらない）・機能要件・非機能要件・制約・受け入れ基準を、`.claude/rules/requirements.md` の章立てに沿ってユーザーと詰める。
4. 詰まった内容を `docs/design/requirements.md` に書く（新規セクション追加、または既存セクションの更新）。
5. `docs/README.md` の索引を更新する。
6. 要件が固まったことをユーザーに伝え、次は design スキルで設計に進むことを案内する。

## 守ること

- 曖昧なまま断定して書かない。決めきれないことは「オープンな論点」として残す（`.claude/rules/requirements.md` 参照）。
- 外部サービス（Qiita API・Bedrock）の制限値を記憶で書かない。裏取りする。
- このスキルでは設計判断（どの AWS サービスをどう組むか）やコードを書かない。
