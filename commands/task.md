---
description: 任务拆分：把开发文档拆成可执行、可排序、可验收的原子任务与执行顺序
argument-hint: "[开发序号]"
---

调用 `task-planner` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号）
- 输入：开发文档与同目录流程图
- 产物：`docs/dev-docs/<开发序号>/task-list/` 下任务文件与 `执行顺序.md`
- 执行顺序由 `scripts/topo_sort.py` 扫描任务文件生成，不手工排序；依赖不得成环
- 收尾校验：`python skills/task-planner/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:implement`
