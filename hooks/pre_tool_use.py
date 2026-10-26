#!/usr/bin/env python3
"""PreToolUse hook：拦截会不可逆破坏工作区或远端的 git / gh 命令。"""

from __future__ import annotations

import re
import sys

import _hooklib as lib

_RULES: tuple[tuple[str, str], ...] = (
    (r"git\s+push\b[^\n|;&]*(?:--force\b|--force-with-lease\b|\s-f\b)",
     "检测到强制推送，可能覆盖远端他人提交"),
    (r"git\s+reset\s+--hard\b", "git reset --hard 会丢弃未提交改动"),
    (r"git\s+clean\b[^\n|;&]*-[a-zA-Z]*f", "git clean -f 会删除未跟踪文件"),
    (r"git\s+branch\s+(?:-D\b|--delete\s+--force\b)", "强制删除分支不可恢复"),
    (r"git\s+checkout\s+--\s+\.", "git checkout -- . 会丢弃全部未提交改动"),
    (r"git\s+restore\s+--\s+", "git restore -- 会丢弃未提交改动"),
    (r"gh\s+pr\s+merge\b[^\n|;&]*--admin\b", "绕过分支保护强制合并 PR"),
    (r"gh\s+repo\s+delete\b", "删除远端仓库不可恢复"),
)


def main() -> int:
    event = lib.read_event()
    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    for pattern, reason in _RULES:
        if re.search(pattern, command):
            lib.emit(
                "PreToolUse",
                {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"{reason}。该命令被 from-issue-to-pr 插件拦截，"
                        "如确需执行，请用户本人手工运行。"
                    ),
                },
            )
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
