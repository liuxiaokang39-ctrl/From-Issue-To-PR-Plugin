---
description: 测试流程与资源准备：编写三层测试流程文档并准备执行所需资源
argument-hint: "[开发序号]"
---

调用 `test-planner` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号）
- 产物：`docs/dev-docs/<开发序号>/test-process/` 下单元白盒、集成白盒、真实部署黑盒三份流程文档 + 已就绪资源
- 本阶段只设计与准备，不执行测试、不写入执行结果
- 门禁：真实部署黑盒测试流程须先交用户审核
- 收尾校验：`python skills/test-planner/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:test-run`
