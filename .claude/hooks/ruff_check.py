"""PostToolUse フック: 編集された Python ファイルに ruff check をかける。

指摘があれば exit 2 で stderr の内容が Claude にフィードバックされ、その場で修正させる。
uv が未導入の環境では何もせずスキップする（フックがブロッカーにならないように）。
"""

import json
import shutil
import subprocess
import sys

# Windows のロケールエンコーディング（cp932）で文字化けしないよう UTF-8 に固定
sys.stderr.reconfigure(encoding="utf-8")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path.endswith(".py"):
        sys.exit(0)

    if shutil.which("uv") is None:
        sys.exit(0)

    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", file_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        sys.exit(0)

    if result.returncode != 0:
        print(result.stdout or result.stderr, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
