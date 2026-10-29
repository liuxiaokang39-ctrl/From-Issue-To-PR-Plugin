---
description: 需求确认：把模糊需求收敛为可评审 Issue，在远端仓库创建 Issue，调用 spec-manager 分配开发信息后本地留档
argument-hint: "[需求描述]"
---

调用 `issue-writer` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（需求描述；不提供开发序号或分支，缺失时先问用户，不要假设）
- 必须遵守 `skills/issue-writer/SKILL.md` 的提问规则：先确认本期做什么 / 不做什么，再逐项确认具体需求、期望行为与期望结果
- 创建远端 Issue 后，必须调用一次 `spec-manager` 取得开发序号、分支、worktree 与开发目录，再按返回的开发序号本地留档；禁止自行分配序号或创建工作区
- 产物：远端 Issue + `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`
- 收尾校验：`python skills/issue-writer/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:dev-doc`
