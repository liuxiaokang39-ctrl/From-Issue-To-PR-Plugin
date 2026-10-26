# From Issue To PR：Claude Code 安装指南（面向 Agent）

本文件写给协助用户安装本插件的 Agent。安装范围保持最小：不要克隆仓库、不要改用户的
全局 Claude Code 配置、不要复制认证文件、不要跳过 Hook 审核。

插件清单位于 `beta/claude-code-plugin-0.1.0` 分支的 `.claude-plugin/plugin.json`，插件整体说明见
[README.md](../../README.md)。

## 前置依赖

| 依赖 | 用途 | 必需性 |
| --- | --- | --- |
| 支持插件的 Claude Code（`claude plugin` 可用） | 安装与加载插件 | 必需 |
| Python 3.9+ | hooks 与各 Skill 的 `evals/` 脚本 | 必需 |
| git | 分支、提交与 PR 流程 | 必需 |
| GitHub CLI（`gh`），已 `gh auth login` | `issue-writer` / `pr-creator` 阶段 | 后续阶段必需 |
| Rust 工具链（`rust-script`） | 生成 rustdoc JSON 与 AST 事实 | 仅 `project-doc-sync` 阶段 |

`hooks/hooks.json` 默认以 `python` 调用脚本。Windows 下通常可用；若系统只有 `python3`，
安装前把 [hooks/hooks.json](../../hooks/hooks.json) 中的命令改成 `python3`。

## 安装

### 从本地仓库安装

在仓库根目录执行：

```powershell
claude plugin validate ./
claude plugin marketplace add ./
claude plugin install from-issue-to-pr@from-issue-to-pr
```

### 从 GitHub 安装

Claude Code 版本位于 `beta/claude-code-plugin-0.1.0` 分支；`main` 分支只保留安装文档，不含
`.claude-plugin/` 清单。从 GitHub 安装时先获取该分支的仓库副本，再按上一节从本地目录安装。

## 重启与加载

1. 重启 Claude Code，或在会话中运行 `/reload-plugins`。
2. 运行 `/plugin`，在 Installed 列表确认 `from-issue-to-pr` 已启用。
3. 运行 `/agents`，确认 `workflow-orchestrator` 可用。
4. 运行 `/hooks`，确认本插件的 4 个 Hook 事件已注册。

## Claude Code 版能力范围

| 组件 | 数量 | 使用方式 |
| --- | --- | --- |
| `skills/` | 8 个阶段 Skill | 由命令或 Agent 自动调用，也可用 `Skill` 工具直接调用 |
| `agents/workflow-orchestrator.md` | 1 个编排 Agent | `/agents` 查看；用于串联 8 个阶段 |
| `commands/` | 9 个命令 | `/from-issue-to-pr:workflow`、`/from-issue-to-pr:issue` 等 |
| `hooks/hooks.json` | 4 个生命周期 Hook | 安装后自动生效，可在 `/hooks` 查看 |

## Hook 行为

| 事件 | 匹配工具 | 行为 | 是否阻断 |
| --- | --- | --- | --- |
| `SessionStart` | — | 注入 8 阶段工作流与已有开发序号 | 否 |
| `PreToolUse` | `Bash` | 拦截强制推送、`reset --hard`、`clean -f`、强删分支、`checkout -- .`、`gh pr merge --admin` 等不可逆命令 | 是（deny） |
| `PostToolUse` | `Write` / `Edit` / `MultiEdit` | 写入 `docs/dev-docs/<序号>/` 产物后，运行对应 Skill 的 `evals/` 校验并把结果回给模型 | 否（回传校验结果） |
| `Stop` | — | 最近一个开发序号目录缺产物时返回一次继续执行，让模型补齐或向用户说明 | 一次继续 |

`project-doc-sync` 的校验需要 rustdoc JSON 参数，无法从文件路径推断，故不自动触发；
到该阶段时按 Skill 说明手工运行。

## 冒烟测试

使用一次性测试仓库，不要在用户正在开发的项目里做写入测试。

1. 新建 Claude Code 会话，问「当前插件工作流包含哪些阶段？」。若 `SessionStart` 已生效，
   回答中会出现 8 个阶段与 `docs/dev-docs/` 产物约定。
2. 在 `/plugin` 确认插件已启用；在 `/agents` 确认编排 Agent 存在；在 `/` 的命令列表中
   确认 `/from-issue-to-pr:workflow` 与 8 个阶段命令。
3. 在一次性仓库中让 Claude Code 执行 `git reset --hard`。`PreToolUse` 生效时应被拒绝，
   并给出插件拦截原因。
4. 让 Claude Code 新建 `docs/dev-docs/999/smoke-issue.md`。`PostToolUse` 生效时会在结果里
   附加 `issue-writer` 的校验输出。验证完删除该目录。

汇报时只说明：插件是否加载、命令与 Agent 是否可见、Hook 是否注册、上述两项拦截/校验是否
按预期触发。不要用一次冒烟测试断言模型行为整体变好。

## 已知限制

- Hook 只覆盖 Claude Code 的 `Write` / `Edit` / `MultiEdit`；通过 Bash 或其他工具写文件
  时不会触发产物校验。
- 插件不改变 Claude Code 的权限设置，也不替代工具自身的确认流程。
- Claude Code 版本位于 `beta/claude-code-plugin-0.1.0` 分支；Codex 版本安装见
  [codex.md](codex.md)。
