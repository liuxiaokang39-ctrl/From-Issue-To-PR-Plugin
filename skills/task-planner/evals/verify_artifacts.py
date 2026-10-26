#!/usr/bin/env python3
"""校验 task-planner 执行后的产物位置，以及任务文件 JSON 头的格式。

用法：
    python evals/verify_artifacts.py <开发序号目录>

示例：
    python evals/verify_artifacts.py docs/dev-docs/001

开发序号目录即 docs/dev-docs/<开发序号>，任务目录为其中的 `task-list/`。
校验项：

1. `task-list/` 存在，且至少有一个任务文件；
2. 任务文件名为 `<编号>-<任务标题>.md`；
3. 每个任务文件最开头是合法 JSON 头：`编号` 为非空字符串且与文件名前缀一致，
   `依赖` 为字符串数组（无依赖填 `[]`），依赖指向存在的任务，且无自依赖与循环依赖；
4. `执行顺序.md` 存在，覆盖全部任务，且顺序满足依赖的先后关系。

退出码：全部通过为 0；有缺失或不符合约定为 1；参数错误为 2。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_ORDER_NAME = "执行顺序.md"
_JSON_FENCE_RE = re.compile(
    r"^```(?:json)?[ \t]*\r?\n(.*?)\r?\n```[ \t]*(?:\r?\n|$)",
    re.DOTALL | re.IGNORECASE,
)
_ORDER_LINE_RE = re.compile(r"^\s*\d+\.\s+(\S+)")


def _parse_header(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """解析文件开头的 JSON 头，返回 (元数据, 错误信息)。"""
    stripped = text.lstrip("\ufeff \t\r\n")
    match = _JSON_FENCE_RE.match(stripped)
    try:
        if match:
            metadata = json.loads(match.group(1))
        else:
            metadata, _ = json.JSONDecoder().raw_decode(stripped)
    except json.JSONDecodeError as exc:
        return None, f"JSON 头解析失败：{exc.msg}（第 {exc.lineno} 行第 {exc.colno} 列）"
    if not isinstance(metadata, dict):
        return None, "JSON 头必须是对象"
    return metadata, None


def _validate_filename(name: str) -> list[str]:
    if "-" not in name:
        return ["文件名不符合 `<编号>-<任务标题>.md`"]
    number, rest = name.split("-", 1)
    problems: list[str] = []
    if not number.strip():
        problems.append("文件名缺少编号")
    if not rest[:-3].strip():
        problems.append("文件名缺少任务标题")
    return problems


def _validate_task(path: Path) -> tuple[str | None, list[str], list[str]]:
    """返回 (编号, 依赖列表, 问题列表)。"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, [], [f"读取失败：{exc}"]
    if not text.strip():
        return None, [], ["文件为空"]

    metadata, error = _parse_header(text)
    if error:
        return None, [], [error]

    problems: list[str] = []
    raw_number = metadata.get("编号")
    number: str | None = None
    if not isinstance(raw_number, str) or not raw_number.strip():
        problems.append("JSON 头「编号」必须是非空字符串")
    else:
        number = raw_number.strip()
        prefix = path.name.split("-", 1)[0] if "-" in path.name else path.name
        if number != prefix:
            problems.append(f"JSON 头「编号」（{number}）与文件名前缀（{prefix}）不一致")

    raw_deps = metadata.get("依赖")
    deps: list[str] = []
    if not isinstance(raw_deps, list):
        problems.append("JSON 头「依赖」必须是数组，无依赖填 []")
    else:
        for item in raw_deps:
            if not isinstance(item, str) or not item.strip():
                problems.append("「依赖」数组元素必须是非空字符串编号")
                break
            deps.append(item.strip())
        else:
            if len(set(deps)) != len(deps):
                problems.append("「依赖」数组存在重复编号")

    return number, deps, problems


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if state.get(dep) == 1:
                return stack[stack.index(dep):] + [dep]
            if state.get(dep, 0) == 0:
                cycle = visit(dep)
                if cycle:
                    return cycle
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state.get(node, 0) == 0:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def _validate_order(
    order_path: Path, numbers: set[str], deps_map: dict[str, list[str]]
) -> list[str]:
    try:
        text = order_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"读取失败：{exc}"]

    order: list[str] = []
    for line in text.splitlines():
        match = _ORDER_LINE_RE.match(line)
        if match:
            order.append(match.group(1))

    problems: list[str] = []
    if not order:
        problems.append("未解析到任何任务条目")
        return problems

    missing = sorted(numbers - set(order))
    if missing:
        problems.append(f"未覆盖任务：{'、'.join(missing)}")
    extra = sorted(set(order) - numbers)
    if extra:
        problems.append(f"包含不存在的任务：{'、'.join(extra)}")
    duplicated = sorted({number for number in order if order.count(number) > 1})
    if duplicated:
        problems.append(f"任务重复出现：{'、'.join(duplicated)}")

    position = {number: index for index, number in enumerate(order) if number in numbers}
    for number, deps in deps_map.items():
        if number not in position:
            continue
        for dep in deps:
            if dep in position and position[dep] >= position[number]:
                problems.append(f"任务 {number} 排在其依赖 {dep} 之前")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("用法：python evals/verify_artifacts.py <开发序号目录>", file=sys.stderr)
        return 2

    root = Path(argv[1])
    if not root.is_dir():
        print(f"开发序号目录不存在：{root}", file=sys.stderr)
        return 2

    print(f"[产物校验] task-planner —— {root}")
    failures = 0

    task_dir = root / "task-list"
    if not task_dir.is_dir():
        print(f"  ✗ 缺少任务目录：{task_dir}")
        print()
        print("结果：失败（1 项）")
        return 1
    print(f"  ✓ 任务目录：{task_dir}")

    task_files = sorted(
        path
        for path in task_dir.iterdir()
        if path.is_file() and path.suffix == ".md" and path.name != _ORDER_NAME
    )
    if not task_files:
        print("  ✗ 任务目录下没有任务文件")
        failures += 1

    deps_map: dict[str, list[str]] = {}
    for path in task_files:
        problems = _validate_filename(path.name)
        number, deps, header_problems = _validate_task(path)
        problems.extend(header_problems)

        if problems:
            print(f"  ✗ 任务文件 {path.name}")
            for problem in problems:
                print(f"      - {problem}")
            failures += 1
        else:
            print(f"  ✓ 任务文件 {path.name}：JSON 头合法")
            if number is not None:
                deps_map[number] = deps

    for number, deps in deps_map.items():
        for dep in deps:
            if dep == number:
                print(f"  ✗ 任务 {number} 依赖了自身")
                failures += 1
            elif dep not in deps_map:
                print(f"  ✗ 任务 {number} 依赖了不存在的任务：{dep}")
                failures += 1

    cycle = _find_cycle(deps_map)
    if cycle:
        print(f"  ✗ 存在循环依赖：{' → '.join(cycle)}")
        failures += 1

    order_path = task_dir / _ORDER_NAME
    if not order_path.is_file():
        print(f"  ✗ 缺少执行顺序文件：{order_path}")
        failures += 1
    elif not order_path.read_text(encoding="utf-8", errors="replace").strip():
        print(f"  ✗ 执行顺序文件内容为空：{order_path}")
        failures += 1
    else:
        order_problems = _validate_order(order_path, set(deps_map), deps_map)
        if order_problems:
            print(f"  ✗ 执行顺序文件 {order_path.name}")
            for problem in order_problems:
                print(f"      - {problem}")
            failures += 1
        else:
            print(f"  ✓ 执行顺序文件 {order_path.name}：覆盖全部任务且顺序满足依赖")

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
