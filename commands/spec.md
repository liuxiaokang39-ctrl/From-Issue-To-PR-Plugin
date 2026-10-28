---
description: 规范与工作区准备：生成/维护 Rust 编码规范与目录架构规范，分配开发序号并创建 worktree 与分支
argument-hint: "[开发序号]"
---

调用 `spec-manager` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号；缺失时由 Skill 扫描 `docs/dev-docs/` 给出候选并询问用户）
- 前置：需求已通过 `issue-writer` 确认
- 产物：`docs/开发规范/Rust编码规范.md`、`docs/开发规范/项目目录架构规范.md`、`docs/dev-docs/<开发序号>/` 目录骨架、与仓库同级的 `<仓库名>-dev-<开发序号>` worktree、`feat/<Issue编号>-<简述>` 分支，以及 worktree 内的本次开发目录（经用户确认后登记到目录架构规范）
- 规范只保留最新约束，变更写入 `docs/开发规范/迁移信息/<开发序号>-<规范名>.md`
- 无 Issue 时由用户选择「先补 Issue」或「仅做规范与骨架」
- 收尾校验：`python skills/spec-manager/evals/verify_artifacts.py <项目根> <开发序号>`；worktree、分支与本次开发目录由 Agent 用 `git worktree list`、`git branch` 与目录架构规范复核
- 下一阶段：`/from-issue-to-pr:dev-doc`
