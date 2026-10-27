# From Issue To PR

From Issue To PR 是一个 Codex 插件：它把开发者手上模糊的需求，按 8 个固定阶段推进到可合并的 PR，解决「需求到代码之间缺少可追溯产物与统一判定标准」的问题。

## 前置条件

| 依赖 | 用途 | 必需性 |
| --- | --- | --- |
| 支持插件的 Codex CLI（`codex plugin` 可用） | 安装与加载插件 | 必需 |
| Python 3.9+ | 运行 `scripts/` 下的 Hook 脚本与各 Skill 的 `evals/` 脚本 | 必需 |
| git | 分支、提交与 PR 流程 | 必需 |
| GitHub CLI（`gh`），已执行 `gh auth login` | 创建 Issue 与 PR | `issue-writer`、`pr-creator` 阶段必需 |
| Rust 工具链（`rust-script`） | 生成 rustdoc JSON 与 AST 事实 | 仅 `project-doc-sync` 阶段必需 |

本项目不使用数据库；需要连通的只有 GitHub（通过 `gh` 访问）。

根目录的 `hooks.json` 默认以 `python` 调用脚本。若系统只有 `python3`，安装前需把该文件中的命令改为 `python3`。

## 安装

安装步骤由 Agent 按 [docs/install/codex.md](docs/install/codex.md) 执行。请先下载 [docs/install/codex.md](docs/install/codex.md)，然后将该文件与下面这句话一起发给 Agent：

```
请读取 docs/install/codex.md，按其中步骤为我安装 From Issue To PR 插件。
```

安装完成后还需要两步：

1. **同意钩子**：插件安装不会自动信任 Hook。按 `docs/install/codex.md` 的指引运行 `/hooks`，逐条查看并信任 `from-issue-to-pr` 的 Hook 条目。
2. **重启应用**：重启安装本插件的应用，使插件与 Hook 重新加载后生效。

## 最小可运行示例

安装完成后，直接在对话框输入下面这行即可使用本插件：

```
/prompts:workflow 需求描述 开发序号
```

- `需求描述`：你想干什么，用一句话写清楚。
- `开发序号`：一个阿拉伯数字（如 `1`、`2`、`3`）。

## 许可证

本项目采用 [Apache-2.0 许可证](LICENSE)。

## 它不做什么

- **不替代 Codex 的权限与沙箱**：插件不改变 Codex 的沙箱与审批设置，也不替代 Codex 自身的权限确认。
- **不自动信任 Hook**：Hook 必须由人工在 `/hooks` 中逐条审核并信任；插件升级导致 Hook 定义变化后需重新审核。
- **命令与 Agent 不在插件内直接生效**：Codex 不加载 `commands/` 与 `agents/`，安装时需把命令文件复制到 `~/.codex/prompts/`（以 `/prompts:xxx` 调用）、把代理的 TOML 配置复制到 `~/.codex/agents/` 或项目 `.codex/agents/`（见 [docs/install/codex.md](docs/install/codex.md)）。
- **不覆盖全部文件写入**：Hook 只监听 Codex 的 `Bash` 与 `apply_patch`；通过其他工具或脚本写文件时不会触发产物校验。
- **不支持 Rust 以外的项目文档同步**：`project-doc-sync` 本版本仅处理 Rust 项目，其他语言的项目文档同步不在能力范围内。
- **不合并 PR、不绕过 CI**：`pr-creator` 只创建草稿 PR 并修复 CI 报错，CI 未全部通过时不转为可评审；插件还会拦截 `gh pr merge --admin`、强制推送、`reset --hard` 等不可逆操作。
