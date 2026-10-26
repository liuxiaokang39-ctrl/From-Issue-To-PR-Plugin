#!/usr/bin/env bash
# 校验 Rust 公有函数的文档覆盖率、事实一致性，以及按模块生成的接口与数据结构文档。
#
# 用法：
#   bash verify_doc_coverage.sh --rustdoc <rustdoc.json> [--ast <ast.json>] \
#     [--docs-root <模块文档根目录>]
#
# 校验项：文档摘要、# Arguments（逐个参数）、# Returns、# Errors、源码中残留的
# 「未确认」占位、rustdoc JSON 是否已过期，以及每个模块的
# docs/data-struct-and-interface/<模块名>/README.md 是否覆盖公有接口、公有函数、
# 私有函数与数据结构。缺少 # Examples 只给出警告。
# 存在问题时有非零退出码。
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
generator="$script_dir/../scripts/generate_fn_docs.py"

if [[ ! -f "$generator" ]]; then
  echo "找不到校验脚本：$generator" >&2
  exit 2
fi

python_bin="${PYTHON:-}"
if [[ -z "$python_bin" ]]; then
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      python_bin="$candidate"
      break
    fi
  done
fi

if [[ -z "$python_bin" ]]; then
  echo "未找到 python3 / python，无法执行覆盖率校验。" >&2
  exit 2
fi

if [[ $# -eq 0 ]]; then
  echo "用法：bash verify_doc_coverage.sh --rustdoc <rustdoc.json> [--ast <ast.json>] [--docs-root <目录>]" >&2
  exit 2
fi

exec "$python_bin" "$generator" --verify "$@"
