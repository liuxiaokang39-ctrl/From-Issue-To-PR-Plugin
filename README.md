# From Issue To PR

From Issue To PR 是一个 Codex 插件：它把开发者手上模糊的需求，按 8 个固定阶段推进到可合并的 PR，解决「需求到代码之间缺少可追溯产物与统一判定标准」的问题。`spec-manager` 是不占阶段序号的管理角色，负责维护开发规范并一次性分配开发序号、分支、worktree 与开发目录。

## 前置条件

| 依赖 | 用途 | 必需性 |
| --- | --- | --- |
| 支持插件的 Codex CLI（`codex plugin` 可用） | 安装与加载插件 | 必需 |
| Python 3.9+ | 运行 `hooks/` 下的 Hook 脚本与各 Skill 的 `evals/` 脚本 | 必需 |
| git | 分支、提交与 PR 流程 | 必需 |
| GitHub CLI（`gh`），已执行 `gh auth login` | 创建 Issue 与 PR | `issue-writer`、`pr-creator` 阶段必需 |
| Rust 工具链（`rust-script`） | 生成 rustdoc JSON 与 AST 事实 | 仅 `project-doc-sync` 阶段必需 |

本项目不使用数据库；需要连通的只有 GitHub（通过 `gh` 访问）。

`hooks/hooks.json` 默认以 `python` 调用脚本。若系统只有 `python3`，安装前需把该文件中的命令改为 `python3`。

## 安装

安装步骤由 Agent 按 [docs/install/codex.md](docs/install/codex.md) 执行。请先下载 [docs/install/codex.md](docs/install/codex.md)，然后将该文件与下面这句话一起发给 Agent：

```
请读取 docs/install/codex.md，按其中步骤为我安装 From Issue To PR 插件。
```

如果想安装指定版本，请前往发行版下载对应的 codex.md 文件。

安装完成后还需要两步：

1. **同意钩子**：插件安装不会自动信任 Hook。按 `docs/install/codex.md` 的指引运行 `/hooks`，逐条查看并信任 `from-issue-to-pr` 的 Hook 条目。
2. **重启应用**：重启安装本插件的应用，使插件与 Hook 重新加载后生效。

## 快速启动

安装完成后，在对话框输入下面这行启动全流程：

```text
/prompts:fitp-workflow
```

插件先做启动检查，再提示「请描述本次开发计划的需求」；描述后进入 A 阶段，由 `issue-writer` 创建 Issue 并分配开发信息。每个阶段结束时都会给出下一条可复制的续跑命令：

```text
/prompts:fitp-workflow -devId=<开发序号> -stage=<下一阶段>
```

测试失败时按失败报告使用 `-reStage=<dev-doc|implement|test-plan>` 回流。已有 Issue 时可直接续接：

```text
/prompts:fitp-workflow <Issue链接>
```

只想确认需求并创建 Issue，使用独立入口 `/prompts:fitp-issueWriter`；它不调用 `spec-manager`、不分配开发序号，也不生成本地留档。

- 开发序号、分支、worktree 与开发目录由 `spec-manager` 自动分配与登记，无需手动提供。
- 阶段续跑命令可直接粘贴到新对话，从下一阶段继续，避免长链路依赖同一上下文。

## 许可证

本项目采用 [Apache-2.0 许可证](LICENSE)。

## 它不做什么

- **不替代 Codex 的权限与沙箱**：插件不改变 Codex 的沙箱与审批设置，也不替代 Codex 自身的权限确认。
- **不自动信任 Hook**：Hook 必须由人工在 `/hooks` 中逐条审核并信任；插件升级导致 Hook 定义变化后需重新审核。
- **命令与 Agent 不在插件内直接生效**：Codex 不加载 `commands/` 与 `agents/`，安装时需把命令文件复制到 `~/.codex/prompts/`（以 `/prompts:xxx` 调用）、把代理的 TOML 配置复制到 `~/.codex/agents/` 或项目 `.codex/agents/`（见 [docs/install/codex.md](docs/install/codex.md)）。
- **不覆盖全部文件写入**：Hook 监听 Codex 的 `Bash` 与 `apply_patch`；通过其他工具或脚本写文件时不会触发产物校验，但非 `spec-manager` 写入开发规范、新建序号目录或创建 / 切换分支与 worktree 仍会被拦截。
- **管理产物只由 spec-manager 写入**：开发规范、`docs/dev-docs/<开发序号>/` 骨架、`开发上下文.md`、开发分支与 worktree 具有独占写入约束，其他 Skill 只读规范、只按登记值执行。
- **不支持 Rust 以外的项目文档同步与开发规范生成**：`project-doc-sync` 与 `spec-manager` 本版本仅处理 Rust 项目，其他语言的对应能力不在范围内。
- **不合并 PR、不绕过 CI**：`pr-creator` 只创建草稿 PR 并修复 CI 报错，CI 未全部通过时不转为可评审；插件还会拦截 `gh pr merge --admin`、强制推送、`reset --hard` 等不可逆操作。
