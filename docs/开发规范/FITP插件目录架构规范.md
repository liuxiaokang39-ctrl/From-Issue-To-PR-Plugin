# FITP插件目录架构规范

本规范规定 From Issue To PR（FITP）插件的目录架构：先给出标准 Codex 插件的目录基线，再说明本插件实际采用的目录结构与约定。单个 Skill 目录的组织方式见 [skill目录架构规范.md](skill目录架构规范.md)，`SKILL.md` 的内容格式见 [SKILL内容开发规范.md](SKILL内容开发规范.md)。

## 标准 Codex 插件目录架构

插件使用独立仓库，以插件名称命名，插件级目录形式如下：

```
my-plugin/
├── .codex-plugin/
│   └── plugin.json          # [必需] 插件清单（Manifest）
├── skills/                  # [可选] 技能目录，包含工作流说明
│   └── <skill-name>/
│       └── SKILL.md
├── .mcp.json                # [可选] MCP 服务器配置
├── .app.json                # [可选] 应用连接器配置
├── agents/                  # [可选] 插件级 Agent 配置
├── commands/                # [可选] 用户显式触发的命令
├── hooks/                   # [可选] 生命周期钩子
│   ├── hooks.json           # 钩子事件与脚本映射
│   └── *.py                 # 钩子脚本与公共库
├── scripts/                 # [可选] 插件级辅助脚本（非钩子）
└── assets/                  # [可选] 静态资源（图标、模板等）
```

| 组成部分 | 必需性 | 职责 |
| --- | --- | --- |
| `.codex-plugin/plugin.json` | 必需 | 插件清单，声明插件名、版本与组件入口 |
| `skills/` | 可选 | 每个 Skill 一个子目录，子目录内至少含 `SKILL.md` |
| `.mcp.json` | 可选 | 需要 MCP 服务器时在此声明 |
| `.app.json` | 可选 | 需要应用连接器时在此声明 |
| `agents/` | 可选 | 插件级 Agent，供宿主支持内置 Agent 时加载 |
| `commands/` | 可选 | 用户显式触发的命令，每个命令一个 Markdown 文件 |
| `hooks/` | 可选 | 生命周期钩子目录，聚合 `hooks.json` 与钩子脚本 |
| `hooks/hooks.json` | 可选 | 生命周期钩子配置，声明事件与脚本映射 |
| `hooks/*.py` | 可选 | 钩子入口脚本与公共库，与 `hooks.json` 同目录 |
| `scripts/` | 可选 | 插件级辅助脚本，例如 Codex 安装脚本；不存放钩子脚本 |
| `assets/` | 可选 | 插件级静态资源，例如图标与通用模板 |

关键约束：

- `plugin.json` 是唯一必需项，其余目录按实际需要创建；不需要的目录不要建空目录占位。
- 生命周期钩子统一放进 `hooks/`：`hooks.json` 与钩子脚本同级存放，不再把 `hooks.json` 放到插件根目录，也不再单独建 `hooks/scripts/`。
- 与钩子无关的插件级辅助脚本放在根级 `scripts/`，不要放进 `hooks/`。
- Skill 自身的 `references/`、`scripts/`、`assets/`、`evals/` 留在该 Skill 目录内，不提升到插件根目录。
- `docs/`、`README.md`、`LICENSE` 属于仓库文档与许可证，不是插件运行时组件，按仓库惯例放在根目录。

## 本项目目录架构

本项目是 Codex 插件 `from-issue-to-pr`。实际使用的插件级组成部分为 `.codex-plugin/`、`skills/`、`agents/`、`commands/`、`hooks/`、`scripts/`；未使用 `.mcp.json`、`.app.json` 与根级 `assets/`（静态资源按 Skill 就近存放）。

```
From-Issue-To-PR-Skill/
├── .codex-plugin/
│   └── plugin.json                   # [必需] 插件清单
├── .agents/
│   └── plugins/
│       └── marketplace.json          # 本仓库的市场登记，供分发与发现（非插件运行时组件）
├── hooks/                            # 生命周期钩子目录
│   ├── hooks.json                    # 生命周期事件与脚本映射
│   ├── _hooklib.py                   # 钩子公共工具库
│   ├── session_start.py              # SessionStart：注入阶段上下文与已有开发序号
│   ├── pre_tool_use.py               # PreToolUse：拦截高危 git/gh 命令
│   ├── post_tool_use.py              # PostToolUse：写入产物后触发对应 evals 校验
│   └── stop_check.py                 # Stop：收尾检查最近开发序号目录产物齐全
├── scripts/
│   └── install_codex.py              # Codex 安装脚本：commands/ → ~/.codex/prompts，agents/*.toml 并注册 config.toml
├── agents/
│   ├── workflow-orchestrator.md      # 插件级 Agent（Markdown 角色定义），按 9 阶段顺序调度并处理门禁与失败回流
│   └── workflow-orchestrator.toml    # 同一 Agent 的 Codex TOML 角色配置，供安装脚本复制到 Codex agents 目录
├── commands/
│   ├── workflow.md                   # 全流程命令
│   ├── issue.md                      # A 需求确认
│   ├── spec.md                       # A2 规范与工作区准备
│   ├── dev-doc.md                    # B、C 状态流转流程图与开发文档
│   ├── task.md                       # D 任务拆分
│   ├── implement.md                  # E 编码实现
│   ├── test-plan.md                  # F 测试流程与资源准备
│   ├── test-run.md                   # G、H、J、K 按流程执行测试与判定
│   ├── doc-sync.md                   # I 项目文档同步
│   └── pr.md                         # L、M、N CI 测试与提交 PR
├── skills/
│   ├── issue-writer/
│   │   ├── SKILL.md
│   │   ├── assets/issue-template.md
│   │   ├── evals/verify_artifacts.py
│   │   └── references/{GitHub-CLI.md, GitHub-submit.md}
│   ├── spec-manager/
│   │   ├── SKILL.md
│   │   ├── assets/{rust-coding-standards-template.md, project-architecture-template.md,
│   │   │           migration-info-template.md}
│   │   ├── evals/verify_artifacts.py
│   │   └── references/rust/{coding-standards-checklist.md, project-architecture-scan.md}
│   ├── dev-doc-writer/
│   │   ├── SKILL.md
│   │   ├── assets/{dev-doc-template.md, flowchart-template.md, interface-contract-template.md}
│   │   ├── evals/verify_artifacts.py
│   │   └── references/{call-relationship-rules.md, function-design-rules.md,
│   │                   resource-lifecycle-rules.md, visibility-attributes.md}
│   ├── task-planner/
│   │   ├── SKILL.md
│   │   ├── assets/task-template.md
│   │   ├── evals/verify_artifacts.py
│   │   ├── references/resource-lifecycle-rules.md
│   │   └── scripts/topo_sort.py
│   ├── implementer/
│   │   ├── SKILL.md
│   │   ├── evals/verify_artifacts.py
│   │   └── references/{call-relationship-rules.md, function-design-rules.md,
│   │                   GitHub-CLI.md, GitHub-submit.md,
│   │                   resource-lifecycle-rules.md, rust-global-constraints.md}
│   ├── test-planner/
│   │   ├── SKILL.md
│   │   ├── assets/{unit-whitebox-test-process-template.md,
│   │   │           integration-whitebox-test-process-template.md,
│   │   │           deployment-blackbox-test-process-template.md}
│   │   ├── evals/verify_artifacts.py
│   │   └── references/{resource-lifecycle-rules.md, visibility-attributes.md}
│   ├── test-runner/
│   │   ├── SKILL.md
│   │   ├── assets/{test-pass-report-template.md, test-fail-report-template.md}
│   │   └── evals/verify_artifacts.py
│   ├── project-doc-sync/
│   │   ├── SKILL.md
│   │   ├── assets/{fn_doc.md, module_interface_doc.md}
│   │   ├── evals/verify_doc_coverage.sh
│   │   └── scripts/{ast_inspect.rs, extract_rustdoc_json.sh, generate_fn_docs.py}
│   └── pr-creator/
│       ├── SKILL.md
│       ├── evals/verify_artifacts.py
│       └── references/{GitHub-CLI.md, GitHub-submit.md}
├── docs/
│   ├── 开发规范/
│   │   ├── FITP插件目录架构规范.md   # 本文件：插件级目录架构与本项目当前结构
│   │   ├── skill目录架构规范.md      # 单个 Skill 目录的工作区组织
│   │   └── SKILL内容开发规范.md      # SKILL.md 的内容格式
│   ├── 项目架构.md                   # 核心目标、状态流转、两类文档、回流路径
│   └── install/codex.md              # Codex 安装、Hook 信任与冒烟测试
├── README.md                         # 插件简介、前置条件、安装与能力边界
├── LICENSE                           # Apache-2.0
└── .gitignore
```

### 顶层目录职责

| 目录 / 文件 | 职责 | 变动时机 |
| --- | --- | --- |
| `.codex-plugin/` | 插件清单，声明 Skill、命令、Agent、Hooks 的加载入口 | 新增插件级能力或调整入口时 |
| `hooks/` | 生命周期钩子目录：`hooks.json` 声明事件映射，同目录脚本存放钩子入口与公共库，不放业务逻辑 | 新增或调整 Hook 事件、钩子脚本时 |
| `scripts/` | 插件级辅助脚本，存放与钩子无关的脚本（如 Codex 安装脚本），不承载业务逻辑 | 新增插件级辅助脚本时 |
| `agents/` | 编排层，负责任务顺序、门禁与回流，不承载具体阶段规则 | 阶段顺序或门禁变化时 |
| `commands/` | 用户的阶段入口，正文只声明调用哪个 Skill，不重复 Skill 内规则 | 新增阶段或调整命令参数时 |
| `skills/` | 9 个阶段 Skill 的实际实现，每个目录内部按 skill目录架构规范组织 | 阶段职责变化时 |
| `.agents/plugins/` | 市场登记信息，供分发与发现，不参与运行时加载 | 发布或版本变更时 |
| `docs/` | 插件自身的规范、架构与安装文档，不放使用者项目的产物 | 规范或架构变化时 |
| `README.md` | 面向使用者的定位、前置条件、安装与能力边界 | 对外可见行为变化时 |

### 目录约定

- 使用者项目的产物一律落在其 `docs/dev-docs/<开发序号>/` 或 `docs/data-struct-and-interface/` 下，不写入本仓库。
- 本仓库 `docs/` 只维护插件自身的规范、架构与安装说明；开发规范统一放在 `docs/开发规范/` 下。
- `hooks/__pycache__/`、`scripts/__pycache__/` 为 Python 运行缓存，不属于源码，已由 `.gitignore` 的 `__pycache__/`、`*.pyc` 规则排除。
- 新增 Skill 时在 `skills/` 下建同名目录并至少包含 `SKILL.md`；是否补 `references/`、`assets/`、`scripts/`、`evals/` 由该阶段是否需要决定。
- 新增命令时在 `commands/` 下建 Markdown 文件，frontmatter 写 `description` 与 `argument-hint`，正文只声明调用哪个 Skill。
- 新增 Hook 时在 `hooks/hooks.json` 增加事件映射，脚本直接放入 `hooks/` 并复用 `_hooklib.py`；不要把 `hooks.json` 放到插件根目录，也不要另建 `hooks/scripts/`。
- 新增插件级 Agent 时同时提供 Markdown 角色定义与 Codex 用的 TOML 配置，由 `scripts/install_codex.py` 复制并注册到 `config.toml`。
