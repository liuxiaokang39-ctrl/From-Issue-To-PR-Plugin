#!/usr/bin/env python3
"""对任务文件的依赖关系做拓扑排序，生成执行顺序文件。

用法：
    python topo_sort.py <任务目录或任务文件> [-o 输出文件]

示例：
    python topo_sort.py docs/dev-docs/001/task-list -o docs/dev-docs/001/task-list/execution-order.md

输入为任务目录（扫描其中除「execution-order.md」外的所有 .md 任务文件），
或单个任务文件。每个任务文件的最开头须为 JSON 头：

    {
      "编号": "001",
      "依赖": ["002", "003"]
    }

无依赖时「依赖」填 `[]`；`任务：<标题>` 或文件中的首个一级标题用于在执行顺序中显示。

输出：按拓扑序排列的执行顺序，形如 `1. 001 创建订单表及索引`。
未指定 -o 时打印到标准输出；指定 -o 时写入该文件。
存在循环依赖、重复编号或引用了不存在的依赖时，打印错误并以非零状态码退出。
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from graphlib import CycleError, TopologicalSorter

_KEY = r"^\s*(?:[-*+]\s+)?(?:\*\*|`)?{key}(?:\*\*|`)?\s*[:：]\s*(.+?)\s*$"
_TITLE_RE = re.compile(_KEY.format(key="(?:任务|标题|title)"), re.IGNORECASE)
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_JSON_FENCE_RE = re.compile(r"^```(?:json)?[ \t]*\r?\n(.*?)\r?\n```[ \t]*(?:\r?\n|$)", re.DOTALL | re.IGNORECASE)
_ORDER_FILENAME = "execution-order.md"
_ID_KEYS = ("编号", "id", "number")
_DEP_KEYS = ("依赖", "depends_on", "depends", "dependencies")


def _clean(value: str) -> str:
    return value.strip().strip("`").strip('"').strip("'").strip()


def _metadata_value(metadata: dict, keys: tuple[str, ...], label: str):
    normalized = {str(key).strip().lower(): value for key, value in metadata.items()}
    for key in keys:
        if key.lower() in normalized:
            return normalized[key.lower()]
    raise ValueError(f"JSON 头缺少「{label}」字段")


def _parse_header(text: str) -> tuple[dict, str]:
    """解析文件开头的 JSON 头，返回 (元数据, 正文)。"""
    stripped = text.lstrip("\ufeff \t\r\n")
    match = _JSON_FENCE_RE.match(stripped)
    try:
        if match:
            metadata = json.loads(match.group(1))
            body = stripped[match.end():]
        else:
            metadata, end = json.JSONDecoder().raw_decode(stripped)
            body = stripped[end:]
    except json.JSONDecodeError as exc:
        raise ValueError(f"文件开头的 JSON 头解析失败：{exc.msg}（第 {exc.lineno} 行第 {exc.colno} 列）") from exc
    if not isinstance(metadata, dict):
        raise ValueError("文件开头的 JSON 头必须是对象")
    return metadata, body


def parse_task_file(path: str) -> tuple[str, str, list[str]]:
    """解析任务文件，返回 (编号, 标题, 依赖列表)。"""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    metadata, body = _parse_header(text)

    raw_number = _metadata_value(metadata, _ID_KEYS, "编号")
    if raw_number is None or isinstance(raw_number, bool):
        raise ValueError("「编号」必须是字符串")
    number = _clean(str(raw_number))
    if not number:
        raise ValueError("「编号」不能为空")

    raw_deps = _metadata_value(metadata, _DEP_KEYS, "依赖")
    if not isinstance(raw_deps, list):
        raise ValueError('「依赖」必须是数组，如 ["002", "003"]；无依赖填 []')
    deps: list[str] = []
    for item in raw_deps:
        if not isinstance(item, str):
            raise ValueError("「依赖」数组的元素必须是字符串编号")
        dep = _clean(item)
        if dep:
            deps.append(dep)

    title = ""
    for line in body.splitlines():
        match = _TITLE_RE.match(line)
        if match:
            title = _clean(match.group(1))
            break
    if not title:
        heading = _HEADING_RE.search(body)
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
