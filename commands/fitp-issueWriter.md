---
description: 独立需求确认入口：只把模糊需求收敛为可评审的远端 Issue，不调用 spec-manager、不分配开发序号、不写本地留档；之后可用 /prompts:fitp-workflow <Issue链接> 续接全流程
argument-hint: "[需求描述]"
---

调用 `issue-writer` Skill，但只执行需求确认与创建远端 Issue。本命令是独立入口，与全流程入口隔离。

- 用户输入：`$ARGUMENTS`（需求描述；缺失时先用 `AskUserQuestion` 询问）
- 按 `skills/issue-writer/SKILL.md` 的提问规则执行需求确认：先确认本期做什么 / 不做什么，再逐项确认具体需求、期望行为与期望结果，最后请用户确认 Issue 正文
- 确认后用 `gh issue create` 创建远端 Issue，取得 Issue 链接与编号
- 创建成功后立即结束；本命令显式覆盖该 Skill 中「调用 spec-manager 分配开发信息」与「按开发序号本地留档」两步
- 禁止：调用 `spec-manager`；分配或确认开发序号；创建 / 切换分支；写入 `docs/dev-docs/`；生成 Issue 本地留档
- 产物：远端 Issue 链接 + 用户确认的需求清单
- 结束提示固定为：「可新开对话发送 `/prompts:fitp-workflow <Issue链接>` 续接全流程」
