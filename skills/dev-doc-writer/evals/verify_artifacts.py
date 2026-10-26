#!/usr/bin/env python3
"""校验 dev-doc-writer 执行后是否在约定位置生成产物。

用法：
    python evals/verify_artifacts.py <开发序号目录>

示例：
    python evals/verify_artifacts.py docs/dev-docs/001

开发序号目录即 docs/dev-docs/<开发序号>。约定产物为同目录下的
`<标题>流程图.md`、`<标题>公有接口契约.md`、`<标题>开发文档.md`，
须同时存在、内容非空，且三者的 `<标题>` 保持一致。

退出码：全部通过为 0；有缺失或不符合约定为 1；参数错误为 2。
"""

from __future__ import annotations

import sys
from pathlib import Path

_SUFFIXES = ("流程图.md", "公有接口契约.md", "开发文档.md")


def _is_non_empty(path: Path) -> bool:
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

    print(f"[产物校验] dev-doc-writer —— {root}")
    failures = 0
    titles: dict[str, str] = {}

    for suffix in _SUFFIXES:
        matches = sorted(
            path for path in root.iterdir() if path.is_file() and path.name.endswith(suffix)
        )
        if not matches:
            print(f"  ✗ 缺少产物：<标题>{suffix}")
            failures += 1
            continue
        if len(matches) > 1:
            names = "、".join(path.name for path in matches)
            print(f"  ✗ <标题>{suffix} 存在多份：{names}")
            failures += 1
            continue

        path = matches[0]
        title = path.name[: -len(suffix)]
        if not title:
            print(f"  ✗ 产物缺少标题：{path.name}")
            failures += 1
            continue
        if not _is_non_empty(path):
            print(f"  ✗ 产物内容为空：{path}")
            failures += 1
            continue

        titles[suffix] = title
        print(f"  ✓ 产物：{path}")

    if len(set(titles.values())) > 1:
        detail = "、".join(f"{suffix[:-3]}={title}" for suffix, title in titles.items())
        print(f"  ✗ 三份产物的标题不一致：{detail}")
        failures += 1

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
