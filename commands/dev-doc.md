---
description: 开发文档：把已确认的 Issue 转成开发文档与配套流程图
argument-hint: "[开发序号]"
---

调用 `dev-doc-writer` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号）
- 输入：`docs/dev-docs/<开发序号>/` 下的 Issue 留档
- 产物：开发文档、状态流转与函数内运行流程图；设计修订另记 `migration-info/`
- 门禁：设计终稿交由用户决定，用户方案能满足需求时优先采用
- 收尾校验：`python skills/dev-doc-writer/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:task`
