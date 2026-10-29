# From Issue To PR：Codex 安装指南（面向 Agent）

本文件是安装执行手册。请按步骤顺序执行，不要跳步。

步骤标记：

- **［Agent 执行］**：Agent 直接运行命令完成，无需征求用户同意。
- **［先询问用户］**：Agent 先向用户确认选项，再继续执行。
- **［用户操作］**：必须由用户在 Codex 或终端中交互完成，Agent 只负责给出指令并核对结果。

安装范围保持最小：不要克隆仓库、不要复制认证文件、不要绕过 Hook 信任审核；除
`scripts/install_codex.py` 对 `config.toml` 的注册外，不要手工改动用户其他 Codex 配置。

插件清单见 [.codex-plugin/plugin.json](../../.codex-plugin/plugin.json)，插件整体说明见
[README.md](../../README.md)。

## 步骤 1：检查前置依赖 ［Agent 执行］

逐条运行检查命令，并把结果记录到最终汇报中。

```powershell
codex --version
codex plugin --help
python --version
git --version
gh --version
gh auth status
rust-script --version
```

| 依赖 | 用途 | 必需性 | 检查通过标准 |
| --- | --- | --- | --- |
| 支持插件的 Codex CLI | 安装与加载插件 | 必需 | 两条 `codex` 命令均正常返回，`plugin` 子命令存在 |
| Python 3.9+ | `hooks/` 下 Hook 脚本与各 Skill 的 `evals/` 脚本 | 必需 | 版本号 ≥ 3.9 |
| git | 分支、提交与 PR 流程 | 必需 | 正常输出版本 |
| GitHub CLI（`gh`），已登录 | `issue-writer` / `pr-creator` 阶段 | 后续阶段必需 | `gh auth status` 显示已登录账号 |
| Rust 工具链（`rust-script`） | 生成 rustdoc JSON 与 AST | 仅 `project-doc-sync` 阶段 | 正常输出版本 |

判定规则：

- 任一必需依赖缺失或版本不满足：停止安装，向用户说明缺什么、如何安装，不要继续后续步骤。
- `gh` 未安装或未登录：继续安装，但明确告知用户在执行 `issue-writer` / `pr-creator` 阶段前必须完成 `gh auth login`。`gh auth login` 属 **［用户操作］**。
- `rust-script` 缺失：继续安装，仅提示 `project-doc-sync` 阶段需要。

## 步骤 2：确认安装来源 ［先询问用户］

询问用户从本地仓库还是 GitHub 安装，然后执行对应命令。

### 本地仓库 ［Agent 执行］

在仓库根目录执行，`<本地仓库绝对路径>` 换成实际路径：

```powershell
codex plugin marketplace add <本地仓库绝对路径>
codex plugin add from-issue-to-pr@from-issue-to-pr
```

### GitHub ［Agent 执行］

当前仓库默认分支为 `main`，直接安装即可，无需 `--ref`：

```powershell
codex plugin marketplace add liuxiaokang39-ctrl/From-Issue-To-PR-Skill
codex plugin add from-issue-to-pr@from-issue-to-pr
```

两条 `add` 命令可重复执行，重复执行不会产生第二份注册。

## 步骤 3：验证插件安装 ［Agent 执行］

```powershell
codex plugin list --json
```

检查输出中存在 `from-issue-to-pr`。不存在时停止，报告 `codex plugin list --json` 的实际输出。

## 步骤 4：接入命令与 Agent ［Agent 执行］

Codex 不直接加载插件的 `commands/` 与 `agents/`，需要由安装脚本复制到 Codex 的约定目录。

### 4.1 确认 Python 调用器名称 ［Agent 执行］

`hooks/hooks.json` 默认以 `python` 调用 Hook 脚本。

- `python --version` 通过：无需改动，继续 4.2。
- 只有 `python3` 可用：Agent 把 [hooks.json](../../hooks/hooks.json) 中 4 条 Hook 命令的 `python` 改为 `python3`。本地仓库安装时直接改仓库文件；从 marketplace 安装时改动会在插件升级后失效，需在最终汇报中注明。

### 4.2 确认安装范围 ［先询问用户］

询问用户选择用户级还是项目级，未指定时按用户级执行。

| 范围 | 命令 | 落地位置 |
| --- | --- | --- |
| 用户级（默认） | `python scripts/install_codex.py --scope user` | `~/.codex/prompts/`、`~/.codex/agents/`、`~/.codex/config.toml` |
| 项目级 | `python scripts/install_codex.py --scope project --project <项目根>` | prompts 仍在 `~/.codex/prompts/`；Agent 与 config 落在 `<项目根>/.codex/` |

### 4.3 执行安装脚本 ［Agent 执行］

先 dry-run 核对计划，再实际写入：

```powershell
python scripts/install_codex.py --dry-run
python scripts/install_codex.py --scope user
```

脚本行为：

- `commands/` → `~/.codex/prompts/`，Codex 以 `/prompts:xxx` 暴露入口；`xxx` 为去掉 `.md` 的文件名，插件只提供 `fitp-workflow.md` 与 `fitp-issueWriter.md` 两条命令，分别对应 `/prompts:fitp-workflow` 与 `/prompts:fitp-issueWriter`。
- `agents/*.toml` → `~/.codex/agents/`（或项目 `.codex/agents/`），并在 `config.toml` 注册 `[agents.<role>]` 的 `description` 与 `config_file`，同时确保 `features.multi_agent = true`。
- 常用参数：`--dry-run` 只打印计划；`--prompts-dir` / `--agents-dir` / `--config` 覆盖默认目录。
- 脚本可重复执行：prompts 文件会覆盖更新，已注册的 `[agents.<role>]` 与 `features.multi_agent` 不会重复写入。

若当前 Codex 版本已移除 custom prompts，则直接使用 `$issue-writer` 等 Skill 名调用对应阶段，功能等价。

### 4.4 验证接入结果 ［Agent 执行］

```powershell
(Get-ChildItem "$HOME\.codex\prompts\fitp-*.md").Count
Test-Path "$HOME\.codex\agents\workflow-orchestrator.toml"
Select-String -Path "$HOME\.codex\config.toml" -Pattern 'multi_agent|\[agents\.workflow-orchestrator\]'
```

期望：本插件的命令数为 `2`，且仅有 `fitp-workflow.md` 与 `fitp-issueWriter.md`（安装脚本也会校验该数量）；Agent 文件存在；`config.toml` 同时命中 `multi_agent` 与 `[agents.workflow-orchestrator]`。不符时报告脚本输出与实际文件状态，不要静默重试。

## 步骤 5：重启并加载插件 ［用户操作］

1. 让用户重启 Codex。
2. 用户打开新的 Codex CLI TUI，运行 `/plugins`，确认 `from-issue-to-pr` 已启用。
3. 用户运行 `/hooks`，逐条查看并信任 `from-issue-to-pr` 的 Hook 命令。

插件安装不会自动信任 Hook。信任记录绑定 Hook 定义的内容哈希，插件升级后定义变化需重新审核并信任。`/hooks` 中可能同时出现其他插件或用户自己的 Hook，只审核本插件的条目。

## 步骤 6：冒烟测试 ［用户操作，Agent 提供话术并核对］

使用一次性测试仓库，不要写入用户正在开发的项目。Agent 向用户提供以下测试项并收集结果。

1. 新建 Codex 会话，问「当前插件工作流包含哪些阶段？」。`SessionStart` 生效时，回答应包含 8 个阶段、`spec-manager` 管理角色、两条固定入口命令（`/prompts:fitp-workflow`、`/prompts:fitp-issueWriter`）与阶段续跑约定。
2. 在 `/plugins` 确认插件已启用；在 `/hooks` 确认 4 个事件的条目已信任。
3. 在一次性仓库中让 Codex 执行 `git reset --hard`。`PreToolUse` 生效时应被拒绝，并给出插件拦截原因。
4. 让 Codex 新建 `docs/dev-docs/999/smoke-issue.md`。`PreToolUse` 生效时应被拒绝，并说明序号目录只能由 `spec-manager` 创建。

测试结束后无需清理：新建序号目录的写入已被拦截。

## 步骤 7：汇报安装结果 ［Agent 执行］

只汇报以下内容，不要用一次冒烟测试断言模型行为整体变好：

- 插件是否加载、Skill 是否可用；
- Hook 是否已信任；
- 步骤 6 中拦截与校验两项是否按预期触发；
- Python 调用器是否做过 `python` → `python3` 改动及其失效条件（如有）。

## Codex 版能力范围

| 组件 | Codex 是否加载 | 使用方式 |
| --- | --- | --- |
| `skills/`（8 个阶段 Skill + 1 个管理角色） | 是 | `$issue-writer`、`$dev-doc-writer`、`$task-planner` 等阶段 Skill；`$spec-manager` 为管理角色 |
| `hooks/hooks.json`（4 个生命周期 Hook） | 是 | 经 `/hooks` 信任后自动触发 |
| `commands/`（2 个命令） | 安装时复制到 `~/.codex/prompts/` | 复制后以 `/prompts:xxx` 调用：`/prompts:fitp-workflow`（全流程 / 阶段续跑）、`/prompts:fitp-issueWriter`（仅需求确认并创建 Issue） |
| `agents/workflow-orchestrator.md` | 安装时复制 TOML 到 `~/.codex/agents/` 或项目 `.codex/agents/` | 由 Codex 子代理系统加载角色定义 |

走完整流程时，输入 `/prompts:fitp-workflow` 启动，按提示描述需求；已有 Issue 时用 `/prompts:fitp-workflow <Issue链接>` 跳过需求询问。每个阶段结束后复制提示中的续跑命令到新对话继续：

```text
/prompts:fitp-workflow -devId=<开发序号> -stage=<下一阶段>
```

测试失败时按失败报告使用 `-reStage=<dev-doc|implement|test-plan>` 回流。也可让 Codex 依次调用
`$issue-writer` → `$dev-doc-writer` → `$task-planner` → `$implementer`
→ `$test-planner` → `$test-runner` → `$project-doc-sync` → `$pr-creator`，并在各 Skill 定义的人工门禁处
停下来询问用户。开发规范检查与开发信息分配由 `spec-manager` 管理角色承担，不占阶段序号。

## Hook 行为

| 事件 | Codex 工具名 | 行为 | 是否阻断 |
| --- | --- | --- | --- |
| `SessionStart` | — | 注入 8 阶段工作流、`spec-manager` 管理角色、两条固定入口命令与阶段续跑规则，并列出已有开发序号 | 否 |
| `PreToolUse` | `Bash`、`apply_patch` | 拦截强制推送、`reset --hard`、`clean -f`、强删分支、`gh pr merge --admin` 等不可逆命令；非 `spec-manager` 写入开发规范、新建序号目录或操作分支时拒绝 | 是（deny） |
| `PostToolUse` | `apply_patch` | 解析补丁中的 `*** Add File:` / `*** Update File:` / `*** Delete File:` 路径，对 `docs/dev-docs/<序号>/` 产物运行对应 Skill 的 `evals/` 校验 | 否（回传校验结果） |
| `Stop` | — | 最近一个开发序号目录缺产物时返回一次继续执行，让模型补齐或向用户说明 | 一次继续 |

`project-doc-sync` 的校验需要 rustdoc JSON 参数，无法从补丁路径推断，故不自动触发；
到该阶段时按 Skill 说明手工运行。

## 已知限制

- Hook 只覆盖 Codex 的 `Bash`（`exec_command`）与 `apply_patch`；通过其他工具或脚本
  写文件时不会触发产物校验。
- 插件不改变 Codex 的沙箱与审批设置，也不替代 Codex 自身的权限确认。
- GitHub 安装默认使用 `main` 分支；如需固定版本，可自行加 `--ref <分支或标签>`。
