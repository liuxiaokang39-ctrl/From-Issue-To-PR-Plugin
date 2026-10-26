---
description: 全流程：从需求确认一路推进到提交 PR，按阶段自动调度 8 个 Skill
argument-hint: "[需求描述] [开发序号]"
---

调用 `workflow-orchestrator` Agent 执行完整流程。

- 用户输入：`$ARGUMENTS`（需求描述与开发序号；开发序号缺失时先问用户）
- 阶段顺序：issue → dev-doc → task → implement → test-plan → test-run → doc-sync → pr
- 遇到各 Skill 内定义的人工门禁（设计终稿确认、真实部署黑盒测试审核）时停下来问用户
- 测试失败时按设计错误 / 非设计错误分别回流到 dev-doc 或 implement
- 每个阶段收尾跑对应 `evals/` 校验，产物缺失先补齐再进入下一阶段
