---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Lambda コーディングルール

## ファイル分割

役割ごとにモジュールを分ける。1 ファイルに詰め込まない。すべて `src/<service>/` 配下に置く。

| ファイル | 役割 |
| --- | --- |
| `handler.py` | ハンドラ本体（`lambda_handler`）。処理フローのみを書く |
| `validate_event.py` | 入力イベントのバリデーション |
| `exceptions.py` | カスタム例外の定義（ロジックは持たない） |
| `test_utils.py` | `test_raise` によるエラー強制発生 |
| `<外部依存>_client.py` | 外部 API・AWS サービスのクライアント（例: `qiita_client.py`、`bedrock_client.py`） |

テストは `tests/<service>/` に、対象ファイルと 1 対 1 で対応させて置く（`test_handler.py`・`test_validate_event.py` …）。

## import の書き方

`pyproject.toml` の `pythonpath = ["src"]` と SAM の `CodeUri: src/` により、**テストでも Lambda 実行時でも同じ絶対 import が通る**。相対 import（`from .exceptions import ...`）は使わない — Lambda は `handler` をトップレベルモジュールとして読み込むため失敗する。

```python
from common.s3_io import put_json          # 共有モジュール
from fetch_feed.exceptions import QiitaApiError  # 同じサービス内
```

## カスタム例外

- 失敗モード 1 つにつき例外クラス 1 つを `exceptions.py` に定義する。クラス名が Step Functions の `ErrorEquals` でそのままエラー名になるため、**クラス名 = エラー分類**として設計する。
- 各クラスには日本語 1 行の docstring で失敗モードを説明する。継承は `Exception` 直下、`pass` のみでよい:

```python
class QiitaRateLimitError(Exception):
    """Qiita API のレート制限に達した（一時的エラー・リトライ対象）"""

    pass
```

- ライブラリが投げる汎用例外は、内容で判別してカスタム例外に変換して raise し直す。変換時は元のメッセージとコンテキスト（タグ名・記事 ID 等）を含める。
- ハンドラ末尾でカスタム例外は **そのまま再 raise** する（Step Functions 側で `ErrorEquals` により分類可能にするため）。握りつぶし・汎用例外への変換は禁止。
- 想定外エラーも raise し直し、Step Functions 側で FAILED にさせる。

```python
except (InputValidationError, QiitaRateLimitError, ...):
    # カスタム例外はそのまま再 raise → Step Functions の ErrorEquals で捕捉
    raise
```

## ログ — アプリケーションログを出さない

**これはこのリポジトリ固有の重要ルール。個々の Lambda は `print()` / `logging` によるアプリログを出さない。**

- 各ハンドラは処理結果を `{phase, status, counts, artifacts}` の構造化サマリとして **戻り値で返す**。親ステートマシンがそれを `log_writer` Lambda に渡し、CloudWatch Logs の単一ロググループへ JSON 1 行で書く。
- 失敗時は親が続行しないため、EventBridge から呼ばれる `notify_failure` が実行履歴（`GetExecutionHistory`）を引いて失敗ログを補完する。
- デバッグ目的で一時的に `print()` を入れるのは構わないが、コミット前に必ず外す。
- 例外は握りつぶさず raise するので、スタックトレースは Lambda のランタイムログに残る。これは「アプリログ」ではないので問題ない。

## 入力バリデーション

- ハンドラ冒頭で `validate_event(event)` を呼び、必須パラメータの存在・空値（None / 空文字 / 空白のみ）をチェックする。不正なら `InputValidationError` を raise。
- バリデーション通過後の値を tuple で返し、ハンドラ側でアンパックして使う。

## テストモード（test_raise）

- イベントに `test_raise: "<例外クラス名>"` が含まれる場合、対応するカスタム例外を強制発生させる仕組みを `test_utils.py` に持つ。ハンドラの先頭で `raise_if_test_mode(event)` を呼ぶ。
- マップにない値の場合は `RuntimeError` を投げる（想定外エラー経路の動作確認用）。
- ステートマシン定義側では `test_raise` を `$exists()` で省略可能にし、本番投入時のイベントには含めない。

## コーディングスタイル

- 処理フェーズの区切りは `# ====...====` のバナーコメント＋日本語の見出しで明示する。
- docstring は NumPy スタイル・日本語（Parameters / Returns / Raises）。
- リソース（コネクション等）は `finally` で確実にクローズする。クローズ自体の失敗は握りつぶしてよい。
- 定数（リージョン等）はモジュール先頭に大文字で定義する。環境依存値は環境変数から読み、既定値を直書きしない。

## デプロイ・依存

- Lambda は **Zip 形式**。ランタイムは `python3.14`（`.python-version` と一致させる）。
- **ランタイム依存を増やさない**。boto3 は Lambda ランタイム同梱なので `src/requirements.txt` は空を保つ。増やす場合は `pyproject.toml` の `[dependency-groups]` に宣言し、`uv export` で生成する（手書きしない）。
- 単体テストは `tests/` 配下に pytest で書き、AWS 呼び出しは moto、外部 API と Bedrock は必ずモックする（テストで課金を発生させない）。
