#!/usr/bin/env python3
"""对任务文件的依赖关系做拓扑排序，生成执行顺序文件。

用法：
    python topo_sort.py <任务目录或任务文件> [-o 输出文件]

示例：
    python topo_sort.py docs/dev-docs/001 -o docs/dev-docs/001/执行顺序.md

输入为任务目录（扫描其中除「执行顺序.md」外的所有 .md 任务文件），
或单个任务文件。每个任务文件需含 `编号：<编号>` 与 `依赖：<编号, 编号>` 两行，
无依赖填 NONE；`任务：<标题>` 用于在执行顺序中显示。

输出：按拓扑序排列的执行顺序，形如 `1. 001 创建订单表及索引`。
未指定 -o 时打印到标准输出；指定 -o 时写入该文件。
存在循环依赖、重复编号或引用了不存在的依赖时，打印错误并以非零状态码退出。
"""

from __future__ import annotations

import glob
import os
import re
import sys
from graphlib import CycleError, TopologicalSorter

_KEY = r"^\s*(?:[-*+]\s+)?(?:\*\*|`)?{key}(?:\*\*|`)?\s*[:：]\s*(.+?)\s*$"
_ID_RE = re.compile(_KEY.format(key="(?:编号|id)"), re.IGNORECASE)
_TITLE_RE = re.compile(_KEY.format(key="(?:任务|标题|title)"), re.IGNORECASE)
_DEP_RE = re.compile(_KEY.format(key="(?:依赖|depends_on|depends)"), re.IGNORECASE)
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$")
_SEP_RE = re.compile(r"[,，、;；/\s]+")
_NO_DEP = {"none", "null", "n/a", "-", "无", "空"}
_ORDER_FILENAME = "执行顺序.md"


def _clean(value: str) -> str:
    return value.strip().strip("`").strip('"').strip("'").strip()


def parse_task_file(path: str) -> tuple[str, str, list[str]]:
    """解析任务文件，返回 (编号, 标题, 依赖列表)。"""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    number: str | None = None
    title = ""
    deps: list[str] = []
    for line in text.splitlines():
        if number is None:
            match = _ID_RE.match(line)
            if match:
                number = _clean(match.group(1))
                continue
        match = _TITLE_RE.match(line)
        if match and not title:
            title = _clean(match.group(1))
            continue
        match = _DEP_RE.match(line)
        if match:
            deps = [
                d
                for d in (_clean(x) for x in _SEP_RE.split(_clean(match.group(1))))
                if d and d.lower() not in _NO_DEP
            ]

    if number is None:
        raise ValueError(f"{path} 缺少「编号」行")
    if not title:
        heading = _HEADING_RE.match(text.lstrip().splitlines()[0]) if text.strip() else None
        title = _clean(heading.group(1)) if heading else ""
    return number, title, deps


def collect_files(target: str) -> list[str]:
    if os.path.isdir(target):
        files = [
            path
            for path in sorted(glob.glob(os.path.join(target, "*.md")))
            if os.path.basename(path) != _ORDER_FILENAME
        ]
        if not files:
            raise ValueError(f"{target} 下没有任务文件")
        return files
    if os.path.isfile(target):
        return [target]
    raise ValueError(f"找不到任务目录或任务文件：{target}")


def topological_order(tasks: dict[str, tuple[str, list[str]]]) -> list[str]:
    for number, (_, deps) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                raise ValueError(f"任务 {number} 依赖了不存在的任务：{dep}")
    graph = {number: set(deps) for number, (_, deps) in tasks.items()}
    return list(TopologicalSorter(graph).static_order())


def render(order: list[str], tasks: dict[str, tuple[str, list[str]]]) -> str:
    lines = [
        "# 执行顺序",
        "",
        "> 由 `scripts/topo_sort.py` 对任务文件的「依赖」做拓扑排序生成，禁止手工排序。",
        "",
    ]
    for index, number in enumerate(order, start=1):
        title = tasks[number][0]
        lines.append(f"{index}. {number}{f' {title}' if title else ''}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    positionals: list[str] = []
    output: str | None = None
    index = 1
    while index < len(argv):
        arg = argv[index]
        if arg in ("-o", "--output"):
            index += 1
            if index >= len(argv):
                print("-o 需要指定输出文件路径", file=sys.stderr)
                return 2
            output = argv[index]
        else:
            positionals.append(arg)
        index += 1

    if len(positionals) != 1:
        print("用法：python topo_sort.py <任务目录或任务文件> [-o 输出文件]", file=sys.stderr)
        return 2

    try:
        files = collect_files(positionals[0])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    tasks: dict[str, tuple[str, list[str]]] = {}
    for path in files:
        try:
            number, title, deps = parse_task_file(path)
        except (OSError, ValueError) as exc:
            print(f"任务文件解析失败：{exc}", file=sys.stderr)
            return 2
        if number in tasks:
            print(f"任务编号重复：{number}", file=sys.stderr)
            return 2
        tasks[number] = (title, deps)

    try:
        order = topological_order(tasks)
    except CycleError as exc:
        cycle = exc.args[1] if len(exc.args) > 1 else []
        print("检测到循环依赖，涉及以下任务：", file=sys.stderr)
        for number in cycle:
            print(f"  - {number}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    content = render(order, tasks)
    if output:
        try:
            with open(output, "w", encoding="utf-8") as handle:
                handle.write(content)
        except OSError as exc:
            print(f"写入执行顺序文件失败：{exc}", file=sys.stderr)
            return 2
        print(f"已写入 {output}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
