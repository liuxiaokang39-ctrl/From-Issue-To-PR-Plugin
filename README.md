# From Issue To PR Skill

> 一套从「模糊需求」到「可合并 PR」的 Skill 工作流：确认需求 → 产出开发文档 → 拆分任务并实现 → 测试 → 提交 PR。

## 项目简介

本仓库是一个 **Skill 组仓库**，把软件开发中从需求到提交 PR 的完整链路拆成 7 个可独立调用、也可顺序串联的 Skill。每个 Skill 负责一个阶段，并明确各自的输入与产出物，因此既可以走完整流程，也可以只取用其中一环。

它解决的问题：

- 需求在口头传递中失真，边界不清、验收标准缺失；
- 开发文档滞后于代码，方案与实现脱节；
- 任务拆分粒度不可执行，无法逐项验收；
- 测试与验收标准不对齐，回归范围不明；
- PR 描述缺少上下文，评审需要回溯大量背景。

各阶段的产物默认统一落在使用者项目的 `docs/` 目录下，除非显式指定其他位置。

## 工作流总览

```
issue-writer → dev-doc-writer → task-planner → implementer → test-planner → test-runner → pr-creator
   需求确认       开发文档          任务拆分        编码实现     测试流程与资源准备   按流程执行测试    提交 PR
```

| 阶段 | Skill | 输入 | 产出物 |
| --- | --- | --- | --- |
| 需求确认 | `issue-writer` | 用户口述需求、项目背景 | 远端仓库中的 Issue + 本地留档：背景与目标、需求列表、每项需求的期望行为与期望结果、范围边界、待确认问题 |
| 开发文档 | `dev-doc-writer` | Issue 内容、代码库上下文 | `docs/dev-docs/` 下的目录结构文档（docs 迁移信息 / 本项目工作区职责两份）、开发文档（数据结构、函数定义）、配套流程图，以及 `docs/migration-info/` 下的设计迁移记录 |
| 任务拆分 | `task-planner` | 开发文档 | `docs/dev-docs/<序号>/` 下的任务文件（`<编号>-<任务>.md`）与执行顺序文件（`执行顺序.md`） |
| 编码实现 | `implementer` | 开发文档与流程图、任务清单、代码库 | 逐项实现的代码改动 |
| 测试流程与资源准备 | `test-planner` | 开发文档、需求、任务报告、工作区代码 | `docs/test-process/<序号>/` 下三份测试流程文档（单元白盒、集成白盒、真实部署黑盒），以及执行所需的测试框架、运行时、依赖、测试数据与外部服务等资源 |
| 按流程执行测试 | `test-runner` | 三份测试流程文档、工作区代码 | 各场景的执行命令与结果记录；设计层面无法通过时产出 `docs/test-report/<序号>/测试报告.md` |
| 提交 PR | `pr-creator` | 代码改动、Issue、开发文档、测试报告 | PR 标题与描述（背景、改动摘要、验证方式、影响面、回滚方案） |

产物建议命名：`docs/requirement-issue/<仓库名>-<issue编号>-issue.md`、`docs/dev-docs/目录结构.md`、`docs/dev-docs/<序号>-<标题>开发文档.md` 与 `docs/dev-docs/<序号>-<标题>流程图.md`、`docs/dev-docs/<序号>/<编号>-<任务>.md` 与 `docs/dev-docs/<序号>/执行顺序.md`、`docs/migration-info/<序号>/<序号>-<迁移内容概况>.md`、`docs/test-process/<开发文档序号>/1-单元白盒测试流程.md`、`2-集成白盒测试流程.md`、`3-真实部署黑盒测试流程.md`、`docs/test-report/<测试流程序号>/测试报告.md`；PR 描述随 PR 一并提交。

## Skill 清单

### `issue-writer` —— 需求确认

- **职责**：把零散、模糊的想法收敛为一份可评审的 Issue。
- **输入**：用户口述的需求、项目背景、相关代码或资料（可选）。
- **产出**：在远端仓库创建 Issue（远端为主仓库时建于主仓库，远端为 fork 时建于 fork 仓库；无法判断或无远端时先询问用户），并在本地留档 `docs/requirement-issue/<仓库名>-<issue编号>-issue.md`；内容含背景与目标、需求列表、每项需求的期望行为与期望结果、范围边界（做什么 / 不做什么）、待确认问题清单。
- **关键行为**：先确认需求是否真实需要，再就尚不清楚的部分逐项提问确认；信息不足时不自行脑补需求；更新报告时只保留最新需求，不迁移过时内容。创建 Issue 与执行 git / gh 命令时，按需读取 `references/GitHub-CLI.md`、`references/GitHub-submit.md`。

### `dev-doc-writer` —— 开发文档

- **职责**：把已确认的 Issue 转成可落地的开发文档与配套流程图。
- **输入**：Issue 内容、代码库上下文。
- **产出**：`docs/dev-docs/` 下的目录结构文档 `目录结构.md`（分两份，分别记录 docs 的迁移信息与本项目各工作区的职责）、开发文档（数据结构、函数定义，含公开属性与多线程属性）、配套流程图（状态流转、函数内运行流程）；设计修订的迁移记录另置于 `docs/migration-info/<序号>/`。
- **关键行为**：先建立 / 确认两类目录结构文档，再与人类确认读写与只读工作区；默认私有公开属性；需求不涉及多线程时默认普通函数；设计终稿交由人类决定，人类设计能满足需求时优先采用；禁止在同一份文件中并存原设计与修改后设计，迁移记录只记新设计与原设计的差异。

### `task-planner` —— 任务拆分

- **职责**：把开发文档拆成可执行、可排序、可验收、可追踪的原子任务文件与执行顺序文件。
- **输入**：开发文档。
- **产出**：`docs/dev-docs/<序号>/` 下的任务文件 `<编号>-<任务>.md`（含编号、任务、工作区、依赖、产出、验收标准，及从开发文档摘录的函数/结构体/数据库表）与执行顺序文件 `执行顺序.md`。
- **关键行为**：依赖关系必须由拆分阶段显式产出、禁止循环依赖；执行顺序由 `scripts/topo_sort.py` 扫描任务文件后拓扑排序生成，不手工排序；任务粒度以「能独立验证」为准，每个任务须声明其工作区。

### `implementer` —— 编码实现

- **职责**：按任务清单逐项实现代码改动。
- **输入**：开发文档与流程图（`docs/dev-docs/`）、任务清单（`docs/dev-docs/<序号>/`）、代码库。
- **产出**：代码改动，并在达到验收标准后逐项标记任务完成。
- **关键行为**：先读开发文档与流程图了解任务全貌，再基于 `main` 创建任务分支、按 `执行顺序.md` 给出的顺序逐项推进（不自行改序）；执行子任务前先检查其工作区，为空则自行发挥，非空则按任务设计修正现有代码；只改任务声明的工作区；函数编写遵循函数设计规则，Rust 项目额外遵循 Rust 全局约束；每完成一项任务即提交一次 commit 并随即 push；严格按清单推进，不做清单之外的重构或「顺手改进」。执行 git / gh 命令时按需读取 `references/GitHub-CLI.md`、`references/GitHub-submit.md`。

### `test-planner` —— 测试流程与资源准备

- **职责**：依据开发文档、需求与真实实现设计三层测试并编写测试流程文档，同时准备执行测试所需的资源。
- **输入**：开发文档与流程图、需求文档、任务报告（若有）、工作区代码。
- **产出**：`docs/test-process/<序号>/` 下的三份测试流程文档（单元白盒、集成白盒、真实部署黑盒），以及已就绪的测试框架、运行时、依赖、测试数据与外部服务等资源清单。
- **关键行为**：白盒测试覆盖工作区全部代码，公有接口另做单元与集成黑盒测试；真实部署黑盒测试须先交人类审核；逐项准备三份文档「测试所需外部资源」中的依赖，准备失败时提示人类；本阶段只设计与准备，不执行测试、不写入执行结果。

### `test-runner` —— 按流程执行测试

- **职责**：按既有测试流程文档执行三层测试，如实记录结果并处理失败。
- **输入**：`docs/test-process/<序号>/` 下的三份测试流程文档、工作区代码。
- **产出**：各场景的执行命令与结果记录；设计层面无法通过时产出 `docs/test-report/<序号>/测试报告.md`。
- **关键行为**：通过 shell 按「单元白盒 → 集成白盒 → 真实部署黑盒」的顺序执行全部场景，禁止虚构结果与静默吞错；仅允许在入参校验缺失或返回值格式不符时修改代码，设计逻辑导致无法通过时只产出测试报告；测试与源码隔离且不修改函数公开属性；流程文档与实现不一致时回退到 `test-planner`，不擅自改期望结果。

### `pr-creator` —— 提交 PR

- **职责**：把验证通过的改动整理为一份信息完整的 PR。
- **输入**：代码改动、Issue、开发文档、测试报告。
- **产出**：PR 标题与描述（背景、改动摘要、验证方式、影响面、回滚方案）。
- **关键行为**：PR 描述自包含——评审者无需回溯上下文即可理解改动理由。

## 目录结构

```
.
├── LICENSE
├── README.md
└── skills/
    ├── issue-writer/
    │   ├── SKILL.md
    │   └── references/
    │       ├── GitHub-CLI.md
    │       ├── GitHub-submit.md
    │       └── issue-template.md
    ├── dev-doc-writer/
    │   ├── SKILL.md
    │   └── references/
    │       ├── visibility-attributes.md
    │       ├── function-design-rules.md
    │       ├── dev-doc-template.md
    │       └── flowchart-template.md
    ├── task-planner/
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── task-template.md
    │   └── scripts/
    │       └── topo_sort.py
    ├── implementer/
    │   ├── SKILL.md
    │   └── references/
    │       ├── function-design-rules.md
    │       ├── GitHub-CLI.md
    │       ├── GitHub-submit.md
    │       └── rust-global-constraints.md
    ├── test-planner/
    │   ├── SKILL.md
    │   └── references/
    │       ├── visibility-attributes.md
    │       ├── unit-whitebox-test-process-template.md
    │       ├── integration-whitebox-test-process-template.md
    │       └── deployment-blackbox-test-process-template.md
    ├── test-runner/
    │   └── SKILL.md
    └── pr-creator/
        └── SKILL.md
```

`issue-writer`、`dev-doc-writer`、`task-planner`、`implementer`、`test-planner`、`test-runner` 的正文已补充；`pr-creator` 的 `SKILL.md` 当前仅包含元信息，正文待补充。`GitHub-CLI.md`（gh 命令参考）与 `GitHub-submit.md`（Conventional Commits 提交规范与 Git 安全约束）为 `issue-writer` 与 `implementer` 共用的参考文件。

## 快速开始

1. 确认所使用的 AI 编程工具支持 Skill，即能够加载 `SKILL.md` 形式的指令文件。
2. 将 `skills/` 下所需的 Skill 目录放入该工具的 Skill 目录：
   - **Codex**：Skill 目录路径 `TBD`
   - **TRAE**：Skill 目录路径 `TBD`
   - 若工具不支持全局 Skill 目录，也可把 `SKILL.md` 放在项目内，并通过工具的规则文件（如 `AGENTS.md`）引用。
3. 在对话中依次触发各 Skill：先由 `issue-writer` 收敛需求，再按流程推进；也可以只调用其中某一个 Skill。

> 以上路径待实测确认后补充。

## 许可证

本项目采用 Apache-2.0 许可证，详见 [LICENSE](LICENSE)。
