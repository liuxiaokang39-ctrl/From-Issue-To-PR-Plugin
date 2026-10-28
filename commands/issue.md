---
description: 需求确认：把模糊需求收敛为可评审 Issue，并在远端仓库创建 Issue、本地留档
argument-hint: "[需求描述] [开发序号]"
---

调用 `issue-writer` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（需求描述与开发序号；缺失时先问用户，不要假设）
- 必须遵守 `skills/issue-writer/SKILL.md` 的提问规则：先确认需求是否真实需要，再逐项确认期望行为与期望结果
- 产物：远端 Issue + `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`
- 收尾校验：`python skills/issue-writer/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:spec`
