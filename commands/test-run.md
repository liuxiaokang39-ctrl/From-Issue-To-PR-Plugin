---
description: 执行测试：按三份流程文档依次执行并如实记录结果
argument-hint: "[开发序号]"
---

调用 `test-runner` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号）
- 执行顺序：单元白盒 → 集成白盒 → 真实部署黑盒，禁止虚构结果与静默吞错
- 产物：通过时 `docs/dev-docs/<开发序号>/test-report/测试报告.md`；设计层面无法通过时 `test-report/failure-report/<序号>-测试未通过报告.md`
- 仅允许在入参校验缺失或返回值格式不符时改代码；设计逻辑导致失败只出失败报告
- 收尾校验：`python skills/test-runner/evals/verify_artifacts.py docs/dev-docs/<开发序号>`
- 下一阶段：`/from-issue-to-pr:doc-sync`；失败则回流 `/from-issue-to-pr:dev-doc` 或 `/from-issue-to-pr:implement`
