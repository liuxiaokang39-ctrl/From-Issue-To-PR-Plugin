---
description: 全流程：从需求确认一路推进到提交 PR，按阶段自动调度 8 个阶段 Skill 与 spec-manager 管理角色
argument-hint: "[需求描述]"
---

调用 `workflow-orchestrator` Agent 执行完整流程。

- 用户输入：`$ARGUMENTS`（需求描述；开发信息由 `spec-manager` 分配，无需用户提供序号或分支）
- 管理角色：流程启动时调用 `spec-manager` 做规范检查；`issue` 阶段创建 Issue 后由 `issue-writer` 调用一次 `spec-manager` 分配开发序号、分支、worktree 与开发目录
- 阶段顺序：issue → dev-doc → task → implement → test-plan → test-run → doc-sync → pr
- 遇到各 Skill 内定义的人工门禁（设计终稿确认、真实部署黑盒测试审核）时停下来问用户
- 测试失败时按设计错误 / 非设计错误分别回流到 dev-doc 或 implement
- 每个阶段收尾跑对应 `evals/` 校验，产物缺失先补齐再进入下一阶段
