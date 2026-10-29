#!/usr/bin/env python3
"""SessionStart hook：向会话注入本插件的工作流定位信息。"""

from __future__ import annotations

import sys
from pathlib import Path

import _hooklib as lib

_STAGES = (
    "A 需求确认（issue-writer）→ B 状态流转流程图 / C 开发文档（dev-doc-writer）"
    "→ D 任务拆分（task-planner）→ E 编码实现（implementer）"
    "→ F 测试流程与资源（test-planner）→ G/H/J/K 执行测试（test-runner）"
    "→ I 项目文档同步（project-doc-sync）→ L/M/N 提交 PR（pr-creator）"
)


def _recent_indexes(project_dir: Path, limit: int = 3) -> list[str]:
    root = project_dir / lib.DEV_DOCS_REL
    if not root.is_dir():
        return []
    dirs = sorted((path for path in root.iterdir() if path.is_dir()), key=lambda p: p.name)
    return [path.name for path in dirs[-limit:]]


def main() -> int:
    project_dir = Path.cwd()
    lines = [
        "【from-issue-to-pr 插件】业务链路含 8 个阶段 Skill：",
        _STAGES,
        "spec-manager 是管理角色、不占阶段序号：流程启动时调用一次检查并维护开发规范；issue-writer 创建 Issue 后调用一次，一次性分配开发序号、分支、worktree 与开发目录。",
        "开发规范与 docs/dev-docs/<开发序号>/开发上下文.md 只由 spec-manager 写入；其他 Skill 只读规范、只按登记值执行，禁止自行分配序号或创建分支 / worktree。",
        "产物统一落在 docs/dev-docs/<开发序号>/，项目文档按既有位置就地更新。",
        "固定入口命令共 2 条：/prompts:fitp-workflow（全流程 / 阶段续跑）与 /prompts:fitp-issueWriter（仅需求确认并创建 Issue）。",
        "无参数启动：先做启动检查，再输出「请描述本次开发计划的需求」，随后进入 A 阶段；携带 Issue 链接启动：跳过需求询问，直接复用该 Issue。",
        "阶段续跑：/prompts:fitp-workflow -devId=<n> -stage=<下一阶段>；测试失败回流用 -reStage=<dev-doc|implement|test-plan>；续跑不重跑启动检查、不再询问需求。",
        "单阶段也可直接调用对应 Skill（如 $issue-writer）；阶段结束按提示复制续跑命令到新对话继续。",
    ]
    recent = _recent_indexes(project_dir)
    if recent:
        lines.append(f"已有开发序号目录：{', '.join(recent)}（沿用同一序号继续推进）。")
    lib.emit_context("SessionStart", "\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
