#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$DIR/.." && pwd)"

cd "$ROOT_DIR"

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD=("$ROOT_DIR/.venv/bin/python")
elif command -v uv >/dev/null 2>&1; then
    PYTHON_CMD=(uv run python)
else
    PYTHON_CMD=(python3)
fi

export PYTHONPATH="$ROOT_DIR/src:$ROOT_DIR:${PYTHONPATH:-}"

if [ $# -eq 0 ]; then
    # 引数なし: tests ディレクトリ配下の test_*.py を全実行
    TARGETS=("$DIR"/test_*.py)
else
    # 引数あり: 指定されたテストファイルのみ実行
    TARGETS=()
    for arg in "$@"; do
        if [ -f "$arg" ]; then
            TARGETS+=("$arg")
        elif [ -f "$DIR/$arg" ]; then
            TARGETS+=("$DIR/$arg")
        elif [ -f "$DIR/test_${arg}.py" ]; then
            TARGETS+=("$DIR/test_${arg}.py")
        elif [ -f "$DIR/${arg}.py" ]; then
            TARGETS+=("$DIR/${arg}.py")
        else
            echo "Error: Test file not found: $arg" >&2
            exit 1
        fi
    done
fi

exec "${PYTHON_CMD[@]}" -m unittest "${TARGETS[@]}"
