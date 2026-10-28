---
description: 开发规范与开发信息管理（不占阶段序号）：维护 Rust 编码规范与目录架构规范，一次性分配开发序号、分支、worktree 与开发目录并写登记文件
argument-hint: "[开发序号]"
---

调用 `spec-manager` Skill。它是管理角色，不是阶段链路中的一站，由流程启动与 Issue 创建后两个时点调用。

- 用户输入：`$ARGUMENTS`（可选开发序号；启动检查模式不需要）
- 模式一「启动检查（bootstrap）」：流程启动时由编排器调用，检查项目现状并生成 / 更新 `docs/开发规范/Rust编码规范.md` 与 `docs/开发规范/项目目录架构规范.md`；规范有变更时写入 `docs/开发规范/迁移信息/000-<规范名>.md`
- 模式二「开发信息分配（allocate）」：`issue-writer` 创建 Issue 后调用一次，一次性分配开发序号、`feat/<Issue编号>-<简述>` 分支、与仓库同级的 `<仓库名>-dev-<开发序号>` worktree、本次开发目录，创建 `docs/dev-docs/<开发序号>/` 目录骨架，并写入 `docs/dev-docs/<开发序号>/开发上下文.md`
- 开发规范、序号目录骨架、登记文件、分支与 worktree 只由 `spec-manager` 写入；其他 Skill 只读规范、只按登记值执行
- 规范只保留最新约束，变更写入 `docs/开发规范/迁移信息/<开发序号>-<规范名>.md`
- 无 Issue 时不得进入开发信息分配模式，须先回到 `issue-writer`
- 收尾校验：启动检查用 `python skills/spec-manager/evals/verify_artifacts.py <项目根>`；开发信息分配用 `python skills/spec-manager/evals/verify_artifacts.py <项目根> <开发序号>`；worktree、分支与本次开发目录由 Agent 用 `git worktree list`、`git branch` 与登记文件复核
- 本命令不占阶段序号，也不作为阶段推进的一环；阶段之间的下一阶段由 `/from-issue-to-pr:workflow` 或各阶段命令说明给出
