#!/usr/bin/env python3
"""校验 pr-creator 执行后是否在约定位置生成 PR 本地副本。

用法：
    python evals/verify_artifacts.py <开发序号目录>

示例：
    python evals/verify_artifacts.py docs/dev-docs/001

开发序号目录即 docs/dev-docs/<开发序号>。约定产物为
`<repo>-<pr>-pr.md`（`<repo>` 为仓库名的英文 kebab-case，`<pr>` 为 PR 编号），
须存在于该目录下且内容非空。

退出码：全部通过为 0；有缺失或内容为空为 1；参数错误为 2。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PR_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d+-pr\.md$")


def _is_non_empty(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return bool(path.read_text(encoding="utf-8", errors="replace").strip())
    except OSError:
        return False


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("用法：python evals/verify_artifacts.py <开发序号目录>", file=sys.stderr)
        return 2

    root = Path(argv[1])
    if not root.is_dir():
        print(f"开发序号目录不存在：{root}", file=sys.stderr)
        return 2

    print(f"[产物校验] pr-creator —— {root}")
    failures = 0

    candidates = sorted(
        path for path in root.iterdir() if path.is_file() and _PR_RE.match(path.name)
    )
    if not candidates:
        print("  ✗ 未找到 PR 本地副本：<repo>-<pr>-pr.md")
        failures += 1
    else:
        for path in candidates:
            if _is_non_empty(path):
                print(f"  ✓ PR 本地副本：{path}")
            else:
                print(f"  ✗ PR 本地副本内容为空：{path}")
                failures += 1

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
