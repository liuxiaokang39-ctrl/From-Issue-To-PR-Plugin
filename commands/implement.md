---
description: 编码实现：按 task-list/执行顺序.md 逐项实现并提交
argument-hint: "[开发序号]"
---

调用 `implementer` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号）
- 输入：开发文档与流程图、`docs/dev-docs/<开发序号>/task-list/`
- 产物：代码改动 + `docs/dev-docs/<开发序号>/task-report/<编号>-<任务标题>.md`
- 只改任务声明的工作区；每完成一项任务提交一次 commit 并 push；不做清单外重构
- 收尾校验：`python skills/implementer/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:test-plan`
