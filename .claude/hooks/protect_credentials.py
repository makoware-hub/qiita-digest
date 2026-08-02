"""PreToolUse フック: 認証情報ファイル（.env / *.pem）への書き込みをブロックする。

リポジトリ規約（認証情報はリポジトリに置かない。鍵は ~/.ssh/ へ）を
Claude Code のツール実行レベルで強制する。
exit 2 でツール呼び出しをブロックし、stderr のメッセージが Claude に返る。
"""

import json
import os
import sys

# Windows のロケールエンコーディング（cp932）で文字化けしないよう UTF-8 に固定
sys.stderr.reconfigure(encoding="utf-8")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    name = os.path.basename(file_path).lower()
    # .env だけでなく .env.local / .env.production のような環境別ファイルも実体の秘密情報を持つ。
    # 一方 .env.example / .env.sample は共有前提の雛形なので許可する。
    is_env = name == ".env" or name.startswith(".env.")
    is_sample = name.endswith((".example", ".sample", ".template"))
    if (is_env and not is_sample) or name.endswith(".pem"):
        print(
            f"ブロック: {file_path} は認証情報ファイルのため編集禁止。"
            "環境変数はデプロイ先の設定で、鍵は ~/.ssh/ で管理する（リポジトリ規約）。",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
