#!/usr/bin/env python3
"""校验 test-runner 执行后是否在约定位置生成测试报告。

用法：
    python evals/verify_artifacts.py <开发序号目录>

示例：
    python evals/verify_artifacts.py docs/dev-docs/001

开发序号目录即 docs/dev-docs/<开发序号>。约定产物为：

- 通过报告：`test-report/测试报告.md`；
- 失败报告：`test-report/failure-report/<序号>-测试未通过报告.md`。

至少须存在其一，且内容非空；存在失败报告时，文件名须符合约定。

退出码：全部通过为 0；有缺失或不符合约定为 1；参数错误为 2。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PASS_REPORT = "测试报告.md"
_FAIL_REPORT_RE = re.compile(r"^\d+-测试未通过报告\.md$")


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

    print(f"[产物校验] test-runner —— {root}")
    failures = 0
    report_dir = root / "test-report"

    if _is_non_empty(report_dir / _PASS_REPORT):
        print(f"  ✓ 测试报告：{report_dir / _PASS_REPORT}")
        pass_report_ok = True
    else:
        pass_report_ok = False

    fail_dir = report_dir / "failure-report"
    fail_reports = sorted(
        path for path in fail_dir.iterdir() if path.is_file()
    ) if fail_dir.is_dir() else []

    valid_fail = 0
    for path in fail_reports:
        if not _FAIL_REPORT_RE.match(path.name):
            print(f"  ✗ 失败报告命名不符合 `<序号>-测试未通过报告.md`：{path}")
            failures += 1
        elif not _is_non_empty(path):
            print(f"  ✗ 失败报告内容为空：{path}")
            failures += 1
        else:
            print(f"  ✓ 失败报告：{path}")
            valid_fail += 1

    if not pass_report_ok and valid_fail == 0:
        print(f"  ✗ 缺少测试报告：{report_dir / _PASS_REPORT} 或 {fail_dir}/<序号>-测试未通过报告.md")
        failures += 1

    print()
    if failures:
        print(f"结果：失败（{failures} 项）")
        return 1
    print("结果：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
