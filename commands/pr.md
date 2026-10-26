---
description: 提交 PR：把验证通过的改动整理为信息完整的草稿 PR 并推进到可评审
argument-hint: "[开发序号]"
---

调用 `pr-creator` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号）
- 前置：测试报告已通过、项目文档已同步
- 流程：确认待合并分支 → fork 先同步上游 `main` → 合入 `main` → 草稿 PR 触发 CI → 按 CI 报错最小修复 → 转可评审
- 产物：远端 PR + `docs/dev-docs/<开发序号>/<仓库名>-<PR编号>-PR.md`（与远端同内容）
- PR 标题与正文只取自 `docs/` 对应序号文件与真实 diff、测试记录
- 收尾校验：`python skills/pr-creator/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
