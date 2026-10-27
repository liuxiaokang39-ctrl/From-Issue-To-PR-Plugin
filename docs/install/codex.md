# From Issue To PR：Codex 安装指南（面向 Agent）

本文件写给协助用户安装本插件的 Agent。安装范围保持最小：不要克隆仓库、不要改用户的
全局 Codex 配置、不要复制认证文件、不要绕过 Hook 信任审核。

插件清单见 [.codex-plugin/plugin.json](../../.codex-plugin/plugin.json)，插件整体说明见
[README.md](../../README.md)。

## 前置依赖

| 依赖 | 用途 | 必需性 |
| --- | --- | --- |
| 支持插件的 Codex CLI（`codex plugin` 可用） | 安装与加载插件 | 必需 |
| Python 3.9+ | `scripts/` 下的 Hook 脚本与各 Skill 的 `evals/` 脚本 | 必需 |
| git | 分支、提交与 PR 流程 | 必需 |
| GitHub CLI（`gh`），已 `gh auth login` | `issue-writer` / `pr-creator` 阶段 | 后续阶段必需 |
| Rust 工具链（`rust-script`） | 生成 rustdoc JSON 与 AST 事实 | 仅 `project-doc-sync` 阶段 |

根目录的 `hooks.json` 默认以 `python` 调用脚本。Windows 下通常可用；若系统只有 `python3`，
安装前把 [hooks.json](../../hooks.json) 中的命令改成 `python3`。

## 安装

### 从本地仓库安装

在仓库根目录执行，`<本地仓库绝对路径>` 换成实际路径：

```powershell
codex plugin marketplace add <本地仓库绝对路径>
codex plugin add from-issue-to-pr@from-issue-to-pr
codex plugin list --json
```

### 从 GitHub 安装

当前 Codex 版本位于 `beta/codex-plugin-0.1.1` 分支，需用 `--ref` 固定：

```powershell
codex plugin marketplace add liuxiaokang39-ctrl/From-Issue-To-PR-Skill --ref beta/codex-plugin-0.1.1
codex plugin add from-issue-to-pr@from-issue-to-pr
```

两条 `add` 命令可重复执行，重复执行不会产生第二份注册。

## 命令与 Agent 的接入

Codex 不直接加载插件的 `commands/` 与 `agents/`，安装时需把它们复制到 Codex 的约定目录。

### commands/ → `~/.codex/prompts/`

安装脚本 `scripts/install_codex.py` 会把 `commands/` 下的命令文件复制到 `~/.codex/prompts/`。Codex 会从这个目录读取提示词，并以 `/prompts:xxx` 的形式暴露为可调用的入口；`xxx` 为去掉 `.md` 的文件名，例如 `workflow.md` 对应 `/prompts:workflow`。

若当前 Codex 版本已移除 custom prompts，则直接用 `$issue-writer` 等 Skill 名调用对应阶段，功能等价。

### agents/ → `~/.codex/agents/` 或项目 `.codex/agents/`

脚本同时把 `agents/*.toml` 复制到用户级 `~/.codex/agents/`，或复制到项目的 `.codex/agents/` 目录下，并在 `config.toml` 中注册 `[agents.<role>]`（`description` 与 `config_file`），同时确保 `features.multi_agent = true`。Codex 的子代理系统会从这些配置目录加载角色定义。

执行安装脚本：

用户级（`~/.codex/prompts`、`~/.codex/agents`、`~/.codex/config.toml`）：

```powershell
python scripts/install_codex.py --scope user
```

项目级（Agent 与 config 落在项目 `.codex/`，prompts 仍在用户级）：

```powershell
python scripts/install_codex.py --scope project --project <项目根>
```

常用参数：`--dry-run` 只打印计划不写入；`--prompts-dir` / `--agents-dir` / `--config` 覆盖默认目录。脚本可重复执行：prompts 文件会覆盖更新，已注册的 `[agents.<role>]` 与 `features.multi_agent` 不会重复写入。

## 重启与加载

1. 让用户重启 Codex。
2. 打开新的 Codex CLI TUI，运行 `/plugins`，确认 `from-issue-to-pr` 已启用。
3. 运行 `/hooks`，让用户逐条查看并信任本插件声明的 Hook 命令。

插件安装不会自动信任 Hook。信任记录绑定 Hook 定义的内容哈希：插件升级后定义变化，
需要重新审核并信任。`/hooks` 里可能同时出现其他插件或用户自己的 Hook，只审核
`from-issue-to-pr` 的条目即可。

## Codex 版能力范围

| 组件 | Codex 是否加载 | 使用方式 |
| --- | --- | --- |
| `skills/`（8 个阶段 Skill） | 是 | `$issue-writer`、`$dev-doc-writer`、`$task-planner` 等 |
| `hooks.json`（4 个生命周期 Hook） | 是 | 经 `/hooks` 信任后自动触发 |
| `commands/`（9 个命令） | 安装时复制到 `~/.codex/prompts/` | 复制后以 `/prompts:xxx` 调用，例如 `/prompts:workflow` |
| `agents/workflow-orchestrator.md` | 安装时复制 TOML 到 `~/.codex/agents/` 或项目 `.codex/agents/` | 由 Codex 子代理系统加载角色定义 |

走完整流程时，可用 `/prompts:workflow 需求描述 开发序号`，也可让 Codex 依次调用
`$issue-writer` → `$dev-doc-writer` → `$task-planner` → `$implementer` → `$test-planner`
→ `$test-runner` → `$project-doc-sync` → `$pr-creator`，并在各 Skill 定义的人工门禁处
停下来询问用户。

## Hook 行为

| 事件 | Codex 工具名 | 行为 | 是否阻断 |
| --- | --- | --- | --- |
| `SessionStart` | — | 注入 8 阶段工作流与已有开发序号 | 否 |
| `PreToolUse` | `Bash` | 拦截强制推送、`reset --hard`、`clean -f`、强删分支、`gh pr merge --admin` 等不可逆命令 | 是（deny） |
| `PostToolUse` | `apply_patch` | 解析补丁中的 `*** Add File:` / `*** Update File:` / `*** Delete File:` 路径，对 `docs/dev-docs/<序号>/` 产物运行对应 Skill 的 `evals/` 校验 | 否（回传校验结果） |
| `Stop` | — | 最近一个开发序号目录缺产物时返回一次继续执行，让模型补齐或向用户说明 | 一次继续 |

`project-doc-sync` 的校验需要 rustdoc JSON 参数，无法从补丁路径推断，故不自动触发；
到该阶段时按 Skill 说明手工运行。

## 冒烟测试

使用一次性测试仓库，不要在用户正在开发的项目里做写入测试。

1. 新建 Codex 会话，问「当前插件工作流包含哪些阶段？」。若 `SessionStart` 已生效，
   回答中会出现 8 个阶段与 `docs/dev-docs/` 产物约定。
2. 在 `/plugins` 确认插件已启用；在 `/hooks` 确认 4 个事件的条目已信任。
3. 在一次性仓库中让 Codex 执行 `git reset --hard`。`PreToolUse` 生效时应被拒绝，
   并给出插件拦截原因。
4. 让 Codex 新建 `docs/dev-docs/999/smoke-issue.md`。`PostToolUse` 生效时会在结果里
   附加 `issue-writer` 的校验输出。验证完删除该目录。

汇报时只说明：插件是否加载、Skill 是否可用、Hook 是否已信任、上述两项拦截/校验是否
按预期触发。不要用一次冒烟测试断言模型行为整体变好。

## 已知限制

- Hook 只覆盖 Codex 的 `Bash`（`exec_command`）与 `apply_patch`；通过其他工具或脚本
  写文件时不会触发产物校验。
- 插件不改变 Codex 的沙箱与审批设置，也不替代 Codex 自身的权限确认。
- `main` 分支是 Codex 的最新开发分支，`beta/codex-plugin-0.1.1` 是插件的版本分支。
