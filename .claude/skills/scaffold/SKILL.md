---
name: scaffold
description: このリポジトリの標準ディレクトリ構成（CLAUDE.md の「ディレクトリ構成」）に従って、新しいサービスの雛形一式（ファイル構成・最低限のテスト）を作る。「新しい〜の雛形だけ作りたい」「ファイル構成だけ用意して」「箱だけ作って」のように、中身のロジックまでは求められていないときに使うこと。ロジックまで実装したい場合は implement スキルを使う。
---

# 新しいサービスの雛形作成

サービスを手作業で作ると、既存のサービスと少しずつ形が違うものが増えていく。
差が開くほど「隣を見て真似する」が効かなくなるので、最初の一式をここで揃える。

## 作る構成

`src/<service>/` と `tests/<service>/` をミラーさせる（CLAUDE.md「ディレクトリ構成」が正）:

```text
src/<service>/
├── __init__.py
├── handler.py            # lambda_handler（処理フローのみ）
├── validate_event.py     # 入力イベントの検証
├── exceptions.py         # このサービス固有のカスタム例外
├── test_utils.py         # test_raise によるエラー強制発生
└── statemachine/<service>.asl.json
tests/<service>/          # src/<service>/ のファイルと対応させる
```

## 手順

1. サービス名（snake_case）と役割を確認する。未指定なら聞く。
2. CLAUDE.md の「ディレクトリ構成」と `.claude/rules/` 配下の規約（特に `lambda.md`・`stepfunctions.md`）を読み、それに従って上記一式を作る。
3. 既存サービスがあれば最も近いものを開き、書き方（例外の粒度・バリデーションの形・ASL の書式）を揃える。既存が無い段階なら、規約に忠実な最小形を作る。
4. `tests/<service>/` に最低 1 本のテストを一緒に作る（CI が pytest を実行するため）。`tests/conftest.py` の moto フィクスチャを使う。
5. `template.yaml` に Function と StateMachine を追加する（`CodeUri: src/`、`Handler: <service>.handler.lambda_handler` を守る。詳細は `rules/sam.md`）。
6. 作成後、`README.md` のサービス表と `docs/README.md` の索引を更新する。

## 守ること

- ランタイム依存は増やさない方針。boto3 は Lambda ランタイム同梱なので `src/requirements.txt` は空のまま保つ。どうしても必要になったら `pyproject.toml` の `[dependency-groups]` に宣言し、`uv export` で生成する（手書きしない）。
- CLAUDE.md の規約にない独自構成を勝手に増やさない。構成を変えたい場合は、先に CLAUDE.md の更新を提案する。
- アプリケーションログを個々の Lambda から出さない（アーキテクチャ原則 4）。構造化サマリを戻り値で返す形にする。
- エラーを握りつぶさない（アーキテクチャ原則 2）。握りつぶす `except` を書かない。
