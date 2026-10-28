#!/usr/bin/env python3
"""PreToolUse hook：拦截不可逆的 git / gh 命令，以及非 spec-manager 对管理产物的越权操作。

越权范围：
- 写入 `docs/开发规范/` 下的开发规范；
- 写入 `docs/dev-docs/<序号>/开发上下文.md`；
- 新建 `docs/dev-docs/<序号>/` 序号目录（目录尚不存在时）；
- 创建 / 重命名 / 删除分支或创建 / 移动 / 删除 worktree。

spec-manager 执行期间会在 `.git/from-issue-to-pr/spec-manager.lock` 写入授权标记，
存在该标记时上述管理操作放行；其他来源一律阻断。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

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

_WORKSPACE_RULES: tuple[tuple[str, str], ...] = (
    (r"git\s+branch\s+(?:-[a-zA-Z]*[dDmMcCf]|--delete|--move|--copy|--force)\b",
     "创建 / 重命名 / 删除分支只能由 spec-manager 执行"),
    (r"git\s+branch\s+(?![-\s])[^\s]",
     "创建分支只能由 spec-manager 执行"),
    (r"git\s+checkout\s+(?:-b|-B)\b",
     "创建分支只能由 spec-manager 执行"),
    (r"git\s+switch\s+(?:-c|-C)\b",
     "创建分支只能由 spec-manager 执行"),
    (r"git\s+worktree\s+(?:add|remove|move|prune|lock|unlock)\b",
     "创建 / 调整 worktree 只能由 spec-manager 执行"),
)

_CREATE_DIR_RE = re.compile(r"mkdir|new-item|md\s|robocopy|xcopy", re.IGNORECASE)
_SHELL_WRITE_RE = re.compile(
    r"(?:>>?|tee\b|set-content|add-content|out-file|copy-item|move-item|remove-item|"
    r"new-item|rm\b|del\b|cp\b|mv\b|sed\s+-i|open\([^)]*['\"][wa]b?['\"])",
    re.IGNORECASE,
)
_PATCH_FILE_PREFIXES = ("*** Add File: ", "*** Update File: ", "*** Delete File: ")
_PATCH_MOVE_PREFIX = "*** Move to: "
_DENY_SUFFIX = "该操作被 from-issue-to-pr 插件拦截；需要该操作时请调用 spec-manager，或在用户确认后由用户本人手工执行。"


def _target_paths(event: dict) -> list[str]:
    """取出本次写入的目标文件：Claude 用 file_path，Codex 用补丁信封。"""
    tool_input = event.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or "")
    if file_path:
        return [file_path]

    patch = str(tool_input.get("command") or "")
    if not patch:
        return []

    paths: list[str] = []
    moved: dict[str, str] = {}
    current: str | None = None
    for raw in patch.splitlines():
        line = raw.strip()
        for prefix in _PATCH_FILE_PREFIXES:
            if line.startswith(prefix):
                current = line[len(prefix) :].strip()
                if current:
                    paths.append(current)
                break
        else:
            if line.startswith(_PATCH_MOVE_PREFIX) and current:
                target = line[len(_PATCH_MOVE_PREFIX) :].strip()
                if target:
                    moved[current] = target

    return [moved.get(path, path) for path in paths]


def _bash_reason(command: str, project_dir: Path) -> str | None:
    for pattern, reason in _WORKSPACE_RULES:
        if re.search(pattern, command):
            return reason

    if _SHELL_WRITE_RE.search(command) and (
        re.search(r"docs[\\/]+开发规范", command) or "开发上下文.md" in command
    ):
        return "开发规范与开发上下文登记文件由 spec-manager 独占写入"

    if (
        _CREATE_DIR_RE.search(command)
        and re.search(r"docs[\\/]+dev-docs", command)
    ):
        return "开发序号目录只能由 spec-manager 创建"
    return None


def _deny(reason: str) -> None:
    lib.emit(
        "PreToolUse",
        {
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{reason}。{_DENY_SUFFIX}",
        },
    )


def main() -> int:
    event = lib.read_event()
    tool_name = str(event.get("tool_name") or "")
    project_dir = Path(event.get("cwd") or Path.cwd())
    tool_input = event.get("tool_input") or {}

    if tool_name == "Bash":
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
        if lib.manager_active(project_dir):
            return 0
        reason = _bash_reason(command, project_dir)
        if reason:
            _deny(reason)
        return 0

    if tool_name in ("Write", "Edit", "MultiEdit", "apply_patch"):
        if lib.manager_active(project_dir):
            return 0
        for file_path in _target_paths(event):
            reason = lib.protected_write_reason(project_dir, file_path)
            if reason:
                _deny(reason)
                return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
