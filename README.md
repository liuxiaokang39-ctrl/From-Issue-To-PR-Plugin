# From Issue To PR

> 一个把「模糊需求」推进到「可合并 PR」的插件：确认需求 → 产出开发文档 → 拆分任务并实现 → 测试 → 同步项目文档 → 提交 PR。

## 插件简介

本仓库本身就是一个可安装的插件，插件清单位于 [plugin.json](plugin.json)。

插件包含：

- **8 个阶段 Skill**：每个 Skill 负责开发链路中的一个阶段，可独立调用，也可顺序串联；
- **1 个编排 Agent**：`workflow-orchestrator`，按固定顺序调度 8 个 Skill，并处理门禁与失败回流；
- **9 个命令**：8 个阶段命令 + 1 个全流程命令；
- **4 个生命周期钩子**：会话注入上下文、拦截高危 git/gh 命令、写入产物后自动校验、收尾检查产物齐全。

各阶段的产物统一落在使用者项目的 `docs/dev-docs/<开发序号>/` 下，项目文档按其既有位置就地更新。整体架构（状态流转、两类文档的区分、回流路径）见 [docs/项目架构.md](docs/项目架构.md)。

## 安装

### 前置依赖

| 依赖 | 用途 | 必需性 |
| --- | --- | --- |
| Python 3.9+ | 运行 `scripts/`、`evals/` 与 hooks 脚本 | 必需 |
| git | 分支、提交与 PR 流程 | 必需 |
| GitHub CLI（`gh`），已 `gh auth login` | 创建 Issue 与 PR | `issue-writer` / `pr-creator` 阶段必需 |
| Rust 工具链（`rust-script`） | 生成 rustdoc JSON 与 AST 事实 | 仅 `project-doc-sync` 阶段必需 |

Windows 下 hooks 以 `python` 调用脚本；若环境只有 `python3`，需同步修改 [hooks/hooks.json](hooks/hooks.json) 中的命令。

### 安装方式

本插件当前仅支持 Codex。`main` 分支是 Codex 的最新开发分支，`beta/codex-plugin-0.1.0` 是插件的版本分支。

安装与加载步骤、Hook 信任与冒烟测试见 [docs/install/codex.md](docs/install/codex.md)。

## 使用

### 走完整流程

```
/from-issue-to-pr:workflow 需求描述 开发序号
```

或直接描述「从需求到 PR」的诉求，由 `workflow-orchestrator` Agent 接管。编排时严格按阶段推进，遇到各 Skill 内定义的人工门禁（设计终稿确认、真实部署黑盒测试审核）会停下来问你。

### 只走某个阶段

| 命令 | 阶段 | 对应 Skill |
| --- | --- | --- |
| `/from-issue-to-pr:issue` | 需求确认 | `issue-writer` |
| `/from-issue-to-pr:dev-doc` | 开发文档 | `dev-doc-writer` |
| `/from-issue-to-pr:task` | 任务拆分 | `task-planner` |
| `/from-issue-to-pr:implement` | 编码实现 | `implementer` |
| `/from-issue-to-pr:test-plan` | 测试流程与资源准备 | `test-planner` |
| `/from-issue-to-pr:test-run` | 按流程执行测试 | `test-runner` |
| `/from-issue-to-pr:doc-sync` | 项目文档同步 | `project-doc-sync` |
| `/from-issue-to-pr:pr` | 提交 PR | `pr-creator` |

命令名以插件名前缀命名空间化；实际前缀以所用工具的加载方式为准。不命中命令时，用自然语言点名对应 Skill 也能触发。

## 阶段与产物

| 阶段 | Skill | 产物 |
| --- | --- | --- |
| 需求确认 | `issue-writer` | 远端 Issue + `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md` |
| 开发文档 | `dev-doc-writer` | 开发文档、流程图、公有接口契约；设计修订另记 `migration-info/` |
| 任务拆分 | `task-planner` | `task-list/<编号>-<任务标题>.md` + `task-list/执行顺序.md` |
| 编码实现 | `implementer` | 代码改动 + `task-report/<编号>-<任务标题>.md` |
| 测试流程与资源准备 | `test-planner` | `test-process/` 下单元白盒、集成白盒、真实部署黑盒三份流程文档 + 已就绪资源 |
| 按流程执行测试 | `test-runner` | `test-report/测试报告.md`；设计层面失败时 `test-report/failure-report/<序号>-测试未通过报告.md` |
| 项目文档同步 | `project-doc-sync` | 源码公有接口 `///` + `docs/data-struct-and-interface/<模块名>/` 四类模块文档 |
| 提交 PR | `pr-creator` | 远端 PR + `docs/dev-docs/<开发序号>/<仓库名>-<PR编号>-PR.md` |

**设计错误判定**：若按已批准的状态流转图设计的代码无法完成需求，视为设计错误，回到开发文档阶段重新设计；非设计错误（边界条件、参数校验、状态判断疏漏）直接改代码。详见 [docs/项目架构.md](docs/项目架构.md)。

## Hooks

| 事件 | 行为 | 是否阻断 |
| --- | --- | --- |
| `SessionStart` | 注入 8 阶段工作流与已有开发序号，避免每次手工说明当前进度 | 否 |
| `PreToolUse`（Bash） | 拦截强制推送、`reset --hard`、`clean -f`、强删分支、`checkout -- .`、`gh pr merge --admin` 等不可逆命令 | 是（deny） |
| `PostToolUse`（Write/Edit） | 写入 `docs/dev-docs/<开发序号>/` 产物后，自动运行对应 Skill 的 `evals/` 校验并把结果回给模型 | 否 |
| `Stop` | 检查最近一个开发序号目录的产物是否齐全，缺产物时提醒而非静默结束 | 否 |

`project-doc-sync` 的校验依赖 rustdoc JSON 参数，无法从文件路径推断，故不自动触发，需在该阶段按命令说明手工运行。

## 产物校验

各 Skill 自带 `evals/` 校验脚本，可直接运行：

```bash
python skills/issue-writer/evals/verify_artifacts.py docs/dev-docs/001
python skills/project-doc-sync/evals/verify_doc_coverage.sh \
  --rustdoc target/rust-fn-doc/<crate名>.json \
  --ast target/rust-fn-doc/ast.json \
  --docs-root docs/data-struct-and-interface
```

## 目录结构

```
.
├── plugin.json                  # 插件清单
├── README.md                    # 安装与使用说明
├── agents/
│   └── workflow-orchestrator.md # 主编排 Agent
├── commands/                    # 8 个阶段命令 + 1 个全流程命令
├── hooks/                       # 生命周期钩子配置与脚本
│   ├── hooks.json
│   ├── _hooklib.py
│   ├── session_start.py
│   ├── pre_tool_use.py
│   ├── post_tool_use.py
│   └── stop_check.py
├── skills/                      # 8 个 Skill
│   ├── issue-writer/
│   ├── dev-doc-writer/
│   ├── task-planner/
│   ├── implementer/
│   ├── test-planner/
│   ├── test-runner/
│   ├── project-doc-sync/
│   └── pr-creator/
└── docs/                        # 插件自身的开发规范、架构说明与安装文档
    ├── 开发规范.md
    ├── 项目架构.md
    └── install/
        └── codex.md
```

每个 Skill 目录按 [docs/开发规范.md](docs/开发规范.md) 组织：`SKILL.md` 为唯一必需文件；`references/` 存规范与命令参考，`assets/` 存模板样例，`scripts/` 存确定性脚本，`evals/` 存产物校验脚本。

## 开发这个插件

- 新增 Skill：在 `skills/` 下建同名目录并写 `SKILL.md`，[plugin.json](plugin.json) 的 `skills` 已指向 `./skills/`，无需改动清单。
- 新增命令：在 `commands/` 下加一个 Markdown 文件，frontmatter 写 `description` 与 `argument-hint`，正文声明调用哪个 Skill。
- 调整钩子：改 `hooks/hooks.json` 的事件映射，脚本放在 `hooks/` 下并复用 `_hooklib.py`。
- 交付前跑一遍相关 `evals/` 脚本，确认产物仍落在约定位置。

## 许可证

本项目采用 Apache-2.0 许可证，详见 [LICENSE](LICENSE)。
