# From Issue To PR Skill

> 一套从「模糊需求」到「可合并 PR」的 Skill 工作流：确认需求 → 产出开发文档 → 拆分任务并实现 → 测试 → 同步项目文档 → 提交 PR。

## 项目简介

本仓库是一个 **Skill 组仓库**，把软件开发中从需求到提交 PR 的完整链路拆成 8 个可独立调用、也可顺序串联的 Skill。每个 Skill 负责一个阶段，并明确各自的输入与产出物，因此既可以走完整流程，也可以只取用其中一环。

它解决的问题：

- 需求在口头传递中失真，边界不清、验收标准缺失；
- 开发文档滞后于代码，方案与实现脱节；
- 任务拆分粒度不可执行，无法逐项验收；
- 测试与验收标准不对齐，回归范围不明；
- PR 描述缺少上下文，评审需要回溯大量背景。

各阶段的产物默认统一落在使用者项目的 `docs/` 目录下，除非显式指定其他位置；项目文档按其既有位置就地更新。

> 架构总览（含状态流转流程图、两类文档的区分、回流路径）见 [docs/项目架构.md](docs/项目架构.md)。

## 工作流总览

```
issue-writer → dev-doc-writer → task-planner → implementer → test-planner → test-runner → project-doc-sync → pr-creator
   需求确认       开发文档          任务拆分        编码实现     测试流程与资源准备   按流程执行测试      同步项目文档      提交 PR
```

| 阶段 | Skill | 输入 | 产出物 |
| --- | --- | --- | --- |
| 需求确认 | `issue-writer` | 用户口述需求、项目背景 | 远端仓库中的 Issue + 本地留档：背景与目标、需求列表、每项需求的期望行为与期望结果、范围边界、待确认问题 |
| 开发文档 | `dev-doc-writer` | Issue 内容、代码库上下文 | `docs/dev-docs/<开发序号>/` 下的开发文档（数据结构、函数定义）、配套流程图，以及 `migration-info/` 下的设计迁移记录 |
| 任务拆分 | `task-planner` | 开发文档与配套流程图 | `docs/dev-docs/<开发序号>/task-list/` 下的任务文件（`<编号>-<任务标题>.md`，含每个函数条目的内部流程图）与执行顺序文件（`执行顺序.md`） |
| 编码实现 | `implementer` | 开发文档与流程图、任务清单、代码库 | 逐项实现的代码改动 |
| 测试流程与资源准备 | `test-planner` | 开发文档、需求、任务报告、工作区代码 | `docs/dev-docs/<开发序号>/test-process/` 下三份测试流程文档（单元白盒、集成白盒、真实部署黑盒），以及执行所需的测试框架、运行时、依赖、测试数据与外部服务等资源 |
| 按流程执行测试 | `test-runner` | 三份测试流程文档、工作区代码 | 各场景的执行命令与结果记录；通过时产出 `docs/dev-docs/<开发序号>/test-report/测试报告.md`，设计层面无法通过时产出 `docs/dev-docs/<开发序号>/test-report/failure-report/<序号>-测试未通过报告.md` |
| 项目文档同步 | `project-doc-sync` | 测试通过的 Rust 代码、rustdoc JSON、AST 事实、现有项目文档 | 就地更新的公有接口源码 `///` 文档与相关项目说明；`docs/data-struct-and-interface/<模块名>/` 下按模块保存公有接口、公有/私有函数出入参与数据结构信息；`target/rust-fn-doc/` 下的中间产物 |
| 提交 PR | `pr-creator` | 代码改动、Issue、开发文档、测试报告 | PR 标题与描述（背景、改动摘要、验证方式、影响面、回滚方案） |

产物建议命名：`docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`、`docs/dev-docs/<开发序号>/<标题>开发文档.md` 与 `docs/dev-docs/<开发序号>/<标题>流程图.md`、`docs/dev-docs/<开发序号>/migration-info/<序号>-<迁移内容概况>.md`、`docs/dev-docs/<开发序号>/task-list/<编号>-<任务标题>.md` 与 `docs/dev-docs/<开发序号>/task-list/执行顺序.md`、`docs/dev-docs/<开发序号>/test-process/1-单元白盒测试流程.md`、`2-集成白盒测试流程.md`、`3-真实部署黑盒测试流程.md`、`docs/dev-docs/<开发序号>/test-report/测试报告.md`、`docs/dev-docs/<开发序号>/test-report/failure-report/<序号>-测试未通过报告.md`、`docs/dev-docs/<开发序号>/task-report/<编号>-<任务标题>.md`、`docs/dev-docs/<开发序号>/<仓库名>-<PR编号>-PR.md`。

**设计错误判定**：如果根据已批准的状态流转图设计的代码并不能完成需求，视为设计错误，须回到开发文档阶段重新设计；非设计错误（如边界条件、参数校验、状态判断疏漏）则直接修改代码。详见 [docs/项目架构.md](docs/项目架构.md)。

## Skill 清单

### `issue-writer` —— 需求确认

- **职责**：把零散、模糊的想法收敛为一份可评审的 Issue。
- **输入**：用户口述的需求、项目背景、相关代码或资料（可选）。
- **产出**：在远端仓库创建 Issue（远端为主仓库时建于主仓库，远端为 fork 时建于 fork 仓库；无法判断或无远端时先询问用户），并在本地留档 `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`；内容含背景与目标、需求列表、每项需求的期望行为与期望结果、范围边界（做什么 / 不做什么）、待确认问题清单。
- **关键行为**：先确认需求是否真实需要，再就尚不清楚的部分逐项提问确认；信息不足时不自行脑补需求；更新报告时只保留最新需求，不迁移过时内容。创建 Issue 与执行 git / gh 命令时，按需读取 `references/GitHub-CLI.md`、`references/GitHub-submit.md`。

### `dev-doc-writer` —— 开发文档

- **职责**：把已确认的 Issue 转成可落地的开发文档与配套流程图。
- **输入**：Issue 内容、代码库上下文。
- **产出**：`docs/dev-docs/<开发序号>/` 下的开发文档（数据结构、函数定义，含公开属性与多线程属性）、配套流程图（状态流转、函数内运行流程）；设计修订的迁移记录另置于 `docs/dev-docs/<开发序号>/migration-info/`。
- **关键行为**：先与人类确认读写与只读工作区；默认私有公开属性；需求不涉及多线程时默认普通函数；设计终稿交由人类决定，人类设计能满足需求时优先采用；禁止在同一份文件中并存原设计与修改后设计，迁移记录只记新设计与原设计的差异。

### `task-planner` —— 任务拆分

- **职责**：把开发文档拆成可执行、可排序、可验收、可追踪的原子任务文件与执行顺序文件。
- **输入**：开发文档与同目录流程图。
- **产出**：`docs/dev-docs/<开发序号>/task-list/` 下的任务文件 `<编号>-<任务标题>.md`（含编号、任务、工作区、依赖、产出、验收标准，及从开发文档摘录的函数/结构体/数据库表；每个函数条目附依据开发文档功能与总流程图设计的内部流程图）与执行顺序文件 `执行顺序.md`。
- **关键行为**：依赖关系必须由拆分阶段显式产出、禁止循环依赖；执行顺序由 `scripts/topo_sort.py` 扫描任务文件后拓扑排序生成，不手工排序；任务粒度以「能独立验证」为准，每个任务须声明其工作区；每个函数条目须有独立的函数内部流程图，不得照搬整份流程图或与其他函数共用。

### `implementer` —— 编码实现

- **职责**：按任务清单逐项实现代码改动。
- **输入**：开发文档与流程图、任务清单（`docs/dev-docs/<开发序号>/task-list/`）、代码库。
- **产出**：代码改动，以及逐项任务报告 `docs/dev-docs/<开发序号>/task-report/<编号>-<任务标题>.md`。
- **关键行为**：先读开发文档与流程图了解任务全貌，再基于 `main` 创建任务分支、按 `task-list/执行顺序.md` 给出的顺序逐项推进（不自行改序）；执行子任务前先检查其工作区，为空则自行发挥，非空则按任务设计修正现有代码；只改任务声明的工作区；函数编写遵循函数设计规则，Rust 项目额外遵循 Rust 全局约束；每完成一项任务即提交一次 commit 并随即 push；严格按清单推进，不做清单之外的重构或「顺手改进」。执行 git / gh 命令时按需读取 `references/GitHub-CLI.md`、`references/GitHub-submit.md`。

### `test-planner` —— 测试流程与资源准备

- **职责**：依据开发文档、需求与真实实现设计三层测试并编写测试流程文档，同时准备执行测试所需的资源。
- **输入**：开发文档与流程图、需求文档、任务报告（若有）、工作区代码。
- **产出**：`docs/dev-docs/<开发序号>/test-process/` 下的三份测试流程文档（单元白盒、集成白盒、真实部署黑盒），以及已就绪的测试框架、运行时、依赖、测试数据与外部服务等资源清单。
- **关键行为**：白盒测试覆盖工作区全部代码，公有接口另做单元与集成黑盒测试；真实部署黑盒测试须先交人类审核；逐项准备三份文档「测试所需外部资源」中的依赖，准备失败时提示人类；本阶段只设计与准备，不执行测试、不写入执行结果。

### `test-runner` —— 按流程执行测试

- **职责**：按既有测试流程文档执行三层测试，如实记录结果并处理失败。
- **输入**：`docs/dev-docs/<开发序号>/test-process/` 下的三份测试流程文档、工作区代码。
- **产出**：各场景的执行命令与结果记录；通过时产出 `docs/dev-docs/<开发序号>/test-report/测试报告.md`，设计层面无法通过时产出 `docs/dev-docs/<开发序号>/test-report/failure-report/<序号>-测试未通过报告.md`。
- **关键行为**：通过 shell 按「单元白盒 → 集成白盒 → 真实部署黑盒」的顺序执行全部场景，禁止虚构结果与静默吞错；仅允许在入参校验缺失或返回值格式不符时修改代码，设计逻辑导致无法通过时只产出失败报告；测试与源码隔离且不修改函数公开属性；流程文档与实现不一致时回退到 `test-planner`，不擅自改期望结果。

### `project-doc-sync` —— 项目文档同步

- **职责**：在测试通过后，以 rustdoc JSON 为可信底座、syn AST 补全缺失信息，更新 Rust 公有接口的 `///` 文档，并按模块生成接口与数据结构文档。
- **输入**：测试通过的 Rust 代码、rustdoc JSON、AST 事实 JSON、现有项目文档。
- **产出**：就地更新的公有接口源码 `///`（`# Arguments`、`# Returns`、`# Errors`、`# Examples`）、`docs/data-struct-and-interface/<模块名>/` 下按类别拆分的 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md`（含定义位置）、相关项目说明与未确认字段清单；中间产物写入 `target/rust-fn-doc/`。
- **关键行为**：签名与 doc 事实只取自 rustdoc JSON，AST 只补函数体结构、错误分支、调用关系、私有函数与数据结构；LLM 只做合成，不臆造参数含义、错误码、返回值语义；源码 `///` 只更新公有接口，私有函数与数据结构只进模块文档；先用 `scripts/extract_rustdoc_json.sh` 生成 JSON，再用 `scripts/ast_inspect.rs` 补全，由 `scripts/generate_fn_docs.py` 产出事实包、骨架、未确认清单与模块文档，最后用 `evals/verify_doc_coverage.sh` 校验；只同步经测试验证的代码，不修改开发文档与流程图。
- **适用范围**：本版本仅支持 Rust，其他语言暂不支持。

> 项目文档描述项目当前状态，长期维护；开发文档（`docs/dev-docs/`）指导某一次开发，具有时效性，是本次开发的迁移文档。两者不可混用。

### `pr-creator` —— 提交 PR

- **职责**：把验证通过的改动整理为一份信息完整的 PR。
- **输入**：代码改动、Issue、开发文档、测试报告。
- **产出**：PR 标题与描述（背景、改动摘要、验证方式、影响面、回滚方案），以及 `docs/dev-docs/<开发序号>/` 下与远端 PR 同内容的本地副本 `<仓库名>-<PR编号>-PR.md`。
- **关键行为**：先确认待合并分支并判断远端类型，fork 仓库先同步上游 `main`；把待合并分支合入 `main` 后以草稿 PR 触发 CI，按 CI 报错最小修复至全部通过才转为可评审；修复若改变执行逻辑并与对应流程图冲突则暂停并告知人类；PR 标题与正文只取自 `docs/` 对应序号文件与真实 diff、测试记录，缺失信息先问人类；PR 创建后在本地保存同内容副本；PR 描述自包含——评审者无需回溯上下文即可理解改动理由。执行 git / gh 命令时按需读取 `references/GitHub-CLI.md`、`references/GitHub-submit.md`。

## 目录结构

```
.
├── LICENSE
├── README.md
├── docs/
│   ├── 开发规范.md
│   └── 项目架构.md
└── skills/
    ├── issue-writer/
    │   ├── SKILL.md
    │   ├── assets/
    │   │   └── issue-template.md
    │   └── references/
    │       ├── GitHub-CLI.md
    │       └── GitHub-submit.md
    ├── dev-doc-writer/
    │   ├── SKILL.md
    │   ├── assets/
    │   │   ├── dev-doc-template.md
    │   │   └── flowchart-template.md
    │   └── references/
    │       ├── visibility-attributes.md
    │       ├── function-design-rules.md
    │       └── call-relationship-rules.md
    ├── task-planner/
    │   ├── SKILL.md
    │   ├── assets/
    │   │   └── task-template.md
    │   └── scripts/
    │       └── topo_sort.py
    ├── implementer/
    │   ├── SKILL.md
    │   └── references/
    │       ├── function-design-rules.md
    │       ├── call-relationship-rules.md
    │       ├── GitHub-CLI.md
    │       ├── GitHub-submit.md
    │       └── rust-global-constraints.md
    ├── test-planner/
    │   ├── SKILL.md
    │   ├── assets/
    │   │   ├── unit-whitebox-test-process-template.md
    │   │   ├── integration-whitebox-test-process-template.md
    │   │   └── deployment-blackbox-test-process-template.md
    │   └── references/
    │       └── visibility-attributes.md
    ├── test-runner/
    │   ├── SKILL.md
    │   └── assets/
    │       ├── test-pass-report-template.md
    │       └── test-fail-report-template.md
    ├── project-doc-sync/
    │   ├── SKILL.md
    │   ├── assets/
    │   │   └── fn_doc.md
    │   ├── evals/
    │   │   └── verify_doc_coverage.sh
    │   └── scripts/
    │       ├── ast_inspect.rs
    │       ├── extract_rustdoc_json.sh
    │       └── generate_fn_docs.py
    └── pr-creator/
        ├── SKILL.md
        └── references/
            ├── GitHub-CLI.md
            └── GitHub-submit.md
```

8 个 Skill 的 `SKILL.md` 正文均已补充。各 Skill 按 [docs/开发规范.md](docs/开发规范.md) 组织工作区：`references/` 存放规范、命令参考与决策表，`assets/` 存放模板与样例，`scripts/` 存放确定性脚本。`GitHub-CLI.md`（gh 命令参考）与 `GitHub-submit.md`（Conventional Commits 提交规范与 Git 安全约束）为 `issue-writer`、`implementer`、`pr-creator` 各自附带的参考文件。

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
