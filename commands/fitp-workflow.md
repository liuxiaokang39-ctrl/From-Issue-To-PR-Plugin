---
description: 全流程唯一入口：启动检查 → 需求询问 → 逐阶段推进；支持用 Issue 链接复用已建 Issue，并可用 -devId 配合 -stage / -reStage 在新对话中从阶段断点续跑
argument-hint: "[Issue链接] | -devId=<开发序号> -stage=<阶段名> | -devId=<开发序号> -reStage=<回流阶段名>"
---

调用 `workflow-orchestrator` Agent 执行；各阶段的具体做法以对应 Skill 的 `SKILL.md` 为准。本命令是本插件唯一的全流程入口，不保留旧命令别名。

## 入口判定

按 `$ARGUMENTS` 判定，只允许以下三种形态：

| 形态 | 参数 | 行为 |
| --- | --- | --- |
| 全流程启动 | 空 | 启动检查 → 需求询问 → A 阶段 |
| 复用 Issue 启动 | 仅一个 Issue 链接 | 启动检查 → 跳过需求询问 → A 阶段复用该 Issue |
| 阶段续跑 | `-devId=<开发序号>`，且只带 `-stage=<阶段名>` 或 `-reStage=<回流阶段名>` 之一 | 校验参数后直接从指定阶段继续 |

三种形态以外的参数一律拒绝执行并提示正确用法，不猜测用户意图。拒绝情形包括：同时出现 `-stage` 与 `-reStage`、缺少 `-devId`、阶段名不在允许范围、`-devId` 不是正整数、参数中混入多余内容。

## 入口一：全流程启动（无参数）

1. 先调用 `spec-manager`（bootstrap）做启动检查；启动检查失败时中断，不进入 A 阶段。
2. 启动检查通过后，用纯文本输出「请描述本次开发计划的需求」，不要改用选项式提问。
3. 用户描述需求后，以该需求为基础，进入A阶段，调用 `issue-writer`，帮助用户在基础需求上进一步明确需求。创建 Issue 后调用 `spec-manager`（allocate）取得开发序号、分支、worktree 与开发目录，并按返回的开发序号本地留档。

## 入口二：复用已建 Issue（参数为 Issue 链接）

1. 同样先调用 `spec-manager`（bootstrap）做启动检查；失败时中断。
2. 跳过需求询问，不重复确认需求；把该 Issue 链接交给 A 阶段，读取 Issue 内容作为已确认需求。
3. A 阶段由 `issue-writer` 执行开发信息分配与本地留档：用该 Issue 链接调用 `spec-manager`（allocate），按返回的开发序号写入 Issue 本地留档，不重复创建 Issue。
4. 该 Issue 已归档在同一开发序号目录下时直接复用；尚未归档时按返回的开发序号新建本地留档，目录由 `spec-manager` 创建。

## 入口三：阶段续跑（-devId / -stage / -reStage）

### 参数约束

- `-devId` 必填且为正整数；`docs/dev-docs/<devId>/` 与 `docs/dev-docs/<devId>/开发上下文.md` 必须存在，且登记内容（开发序号、分支名、worktree 路径、工作区表格）齐全、工作区至少一条「读写」。任一项缺失或不存在时中断，禁止自行创建目录、补编号或猜测登记值。
- `-stage` 与 `-reStage` 互斥，必须且只能出现一个。
- `-stage` 允许取值：`dev-doc` / `task` / `implement` / `test-plan` / `test-run` / `doc-sync` / `pr`；A 阶段只通过无参数启动或携带 Issue 链接进入。
- `-reStage` 允许取值：`dev-doc` / `implement` / `test-plan`。
- 使用 `-reStage` 时，执行目标阶段前必须读取失败报告目录 `docs/dev-docs/<devId>/failure-report/`（`test-runner` 实际写入的 `docs/dev-docs/<devId>/test-report/failure-report/` 同样有效），确认报告存在且内容非空；报告缺失时中断，不进入目标阶段。
- 续跑入口不重跑启动检查、不再询问需求、不复用旧对话中的临时结论；开发序号、分支、worktree 与工作区只取自开发上下文登记文件，其余输入只取自 `docs/dev-docs/<devId>/` 下的产物。

### 阶段与 Skill 映射

| 阶段名 | Skill | 阶段结束后正常续跑 |
| --- | --- | --- |
| `issue`（A 阶段，由启动入口进入） | `issue-writer` | `-stage=dev-doc` |
| `dev-doc` | `dev-doc-writer` | `-stage=task` |
| `task` | `task-planner` | `-stage=implement` |
| `implement` | `implementer` | `-stage=test-plan` |
| `test-plan` | `test-planner` | `-stage=test-run` |
| `test-run` | `test-runner` | 通过：`-stage=doc-sync`；失败：按回流目标使用 `-reStage` |
| `doc-sync` | `project-doc-sync` | `-stage=pr` |
| `pr` | `pr-creator` | 无（全部完成，只汇报） |

每次调用只推进一个阶段（A 阶段通过启动入口执行，其余阶段通过 `-stage` 续跑）；该阶段完成或失败即停止，不自动跨阶段继续。

## 阶段结束输出

每个阶段结束后按固定模板汇报，并给出可直接复制的续跑命令；`pr` 阶段完成后只汇报，不输出命令。正常完成与需回流的输出分别使用下列模板，首行固定，命令前的提示语固定。

正常推进：

```text
本阶段已完成：<阶段名>
- 产物：<产物路径>
- 校验：<通过 / 未通过>
- 下一阶段：<下一阶段名>（<Skill>）
- 人工门禁：<无 / 待用户确认的事项>

请复制下方命令，在新窗口粘贴发送：
/prompts:fitp-workflow -devId=<实际开发序号> -stage=<下一阶段>
```

测试失败回流：

```text
本阶段未完成，需回流：<阶段名>
- 失败报告：<失败报告路径>
- 回流目标：<dev-doc / implement / test-plan>
- 回流原因：<设计错误 / 非设计错误 / 测试流程与实现不一致>

请复制下方命令，在新窗口粘贴发送：
/prompts:fitp-workflow -devId=<实际开发序号> -reStage=<回流目标>
```

回流目标判定：设计错误回到 `dev-doc`；非设计错误（边界条件、参数校验、状态判断疏漏）回到 `implement`；测试流程文档与实现不一致回到 `test-plan`。判定依据不足时用 `AskUserQuestion` 向用户确认，不自行猜测。

## 执行约束

- 启动检查只在全流程启动与复用 Issue 启动两个入口执行；阶段续跑入口禁止重跑启动检查。
- 开发序号、分支、worktree 与工作区只由 `spec-manager` 分配与登记，编排过程禁止自行编号、创建或删除分支与 worktree；分支状态由各阶段执行前自检，不符时切换到登记分支，切换失败中断。
- 禁止跳过阶段、并行推进两个阶段，或在阶段产物校验未通过时输出续跑命令。
- 人工门禁（设计终稿确认、真实部署黑盒测试审核等）未通过时中止当前阶段，不输出越过门禁的续跑命令。
- 阶段结束输出必须使用上述固定模板：正常块首行为「本阶段已完成」，回流块首行为「本阶段未完成，需回流」，命令前固定输出「请复制下方命令，在新窗口粘贴发送」；正常块只给 `-stage`，回流块只给 `-reStage`。
