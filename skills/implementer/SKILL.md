---
name: implementer
description: 编码实现阶段：读取开发文档、流程图与任务清单，按执行顺序逐项实现代码改动，逐任务生成任务报告并提交、推送 commit；函数编写遵循函数设计规则，Rust 项目额外遵循 Rust 全局约束；严格遵循清单范围，不做清单之外的重构。当用户要求按任务清单写代码、实现任务、落实开发文档、执行 task-list 或提到「编码实现」「实现任务」「按清单开发」「代码落地」等关键词时使用；典型输入为 docs/dev-docs/<开发序号>/ 下的 `<title>-dev-doc.md`、`<title>-flowchart.md` 与 task-list/。
compatibility: python3.12+
metadata:
  author: XK_XK
  version: 1.2
---

# implementer

把已拆分好的任务清单，逐项落成代码改动，并逐任务产出任务报告、提交并推送 commit。本 Skill 位于任务拆分之后、测试与 PR 提交之前，只负责编码实现，不改动开发文档与任务清单。

## 适用场景

- 适用：任务清单已定稿，需要按 `execution-order.md` 逐项修改代码、生成任务报告并按任务提交 commit；用户提到「编码实现」「实现任务」「按任务清单开发」「代码落地」等说法。
- 不适用：开发文档或流程图缺失（回到 `dev-doc-writer` 补齐）；任务清单与执行顺序缺失（回到 `task-planner` 补齐）；测试计划与测试执行（由 `test-planner`、`test-runner` 处理）；PR 提交（由 `pr-creator` 处理）。

## 必要前提

1. **开发文档与流程图存在**：`docs/dev-docs/<开发序号>/` 下存在 `<title>-dev-doc.md` 与同目录的 `<title>-flowchart.md`，且内容非空。不满足时中断，回到 `dev-doc-writer` 阶段补齐，不自行脑补设计。
2. **任务清单与执行顺序存在**：`docs/dev-docs/<开发序号>/task-list/` 下存在 `execution-order.md` 与其中引用的任务文件 `<seq>-<task-title>.md`。不满足时中断，回到 `task-planner` 阶段补齐。
3. **开发序号已登记**：`<开发序号>` 取自 `docs/dev-docs/<开发序号>/dev-context.md` 的登记值，且与 `task-list/` 目录一致。登记文件缺失或与任务目录不一致时中断，回到 `spec-manager` 补齐，不得自行编号。
4. **git 与 gh 可用，分支为登记分支**：`git status` 与 `gh auth status` 均可成功执行，登记文件指定的项目根目录与分支可用；执行前在项目根目录内用 `git branch --show-current` 检查当前分支是否为登记「分支名」，不是时切换到该分支，切换失败则中断。不满足时中断并提示人类配置后重试，不得跳过提交或 push。

## 执行约束

- 必须：奥卡姆剃刀——如无必要，勿增实体。
- 必须：执行顺序取自 `execution-order.md`，按其给出的顺序逐步推进，不自行改序。
- 必须：只改任务声明的工作区——工作区以其在登记文件中的类型为准，类型为「读写」的可新增或修改，类型为「只读」的只读不改。
- 必须：任务达到其「验收标准」后才标记完成；每完成一项任务即生成任务报告、提交 commit 并 push。
- 必须：任务报告固定写入 `docs/dev-docs/<开发序号>/task-report/`，除代码产物与任务报告外不新增其他文件或目录。
- 禁止：在 `main` 分支上 commit 或 push；本阶段全部改动提交在登记文件指定的分支上。
- 必须：开发规范（`docs/dev-standards/`）只读；开发序号、分支名、项目根目录与工作区一律取自 `docs/dev-docs/<开发序号>/dev-context.md`，只按登记值执行，执行前在项目根目录内按登记分支名自检并切换。
- 禁止：创建 / 重命名 / 删除开发分支，禁止写入开发规范与开发上下文登记文件；当前分支不是登记分支时，只允许切换到登记分支，切换失败中断；登记值不可用时回到 `spec-manager` 处理。
- 必须：凡需要向人类提问或确认的环节（信息缺失、失败处理去向等），一律使用 `AskUserQuestion`（或同类选项式接口）给出可选方案，禁止只以纯文本开放式提问；人类可通过「Other」补充选项之外的内容。唯一例外为流程启动时由入口输出的「请描述本次开发计划的需求」。
- 禁止：开发文档、流程图或任务清单缺失时自行脑补，必须回到对应上游阶段补齐。
- 禁止：未达到「验收标准」的任务标记完成；任务报告缺失或未覆盖「修改的信息」「修改的文件与文件内位置」「检查结果」三项的，同样不得标记完成。
- 禁止：跳过 commit 或 push；commit 失败时禁止使用 `--amend`、`--no-verify` 绕过，必须修复后新建 commit。
- 禁止：修改项目的 Git 系文件——包括 `.git/` 目录及其内部文件，以及 `.gitignore`、`.gitattributes`、`.gitmodules` 等 Git 配置文件与钩子；确需改动时停止该任务并交人类处理。
- 只能修改：任务声明的读写工作区，以及 `docs/dev-docs/<开发序号>/task-report/`；两者均不包含 Git 系文件。

**参考文件**：本 Skill 附带下列文件，此处仅**显式声明其存在**，不展开其正文：

- `references/function-design-rules.md`（公有接口设计规范、伪代码实例、校验规则）：**仅在编写函数 / 方法时**读取；
- `references/call-relationship-rules.md`（同模块 / 跨模块的方法调用方式与依赖注入约束）：**仅在编写方法间的调用时**读取；
- `references/resource-lifecycle-rules.md`（对象销毁时独占资源的释放责任、释放顺序与借用 / 共享引用处理）：**仅在编写对象销毁、资源获取或释放相关代码时**读取；
- `references/rust-global-constraints.md`（Rust 全局约束）：**仅在编写 Rust 代码时**读取；
- `references/GitHub-CLI.md`（gh 命令参考）与 `references/GitHub-submit.md`（Conventional Commits 提交规范与 Git 安全约束）：**仅在执行 git 或 gh 命令时**读取。

## 工作流程

### 1. 了解任务全貌

读取 `docs/dev-docs/<开发序号>/` 下本次任务的开发文档与流程图，即 `<title>-dev-doc.md` 与同目录的 `<title>-flowchart.md`，据此了解本次任务的全貌；再读取 `task-list/` 下的 `execution-order.md`。

开发文档或流程图缺失时，回到 `dev-doc-writer` 阶段补齐；任务清单或执行顺序缺失时，回到 `task-planner` 阶段补齐，均不自行脑补设计。三者均存在且可读时，进入第 2 步。

### 2. 按执行顺序逐项实现

按 `execution-order.md` 给出的顺序逐步推进，不自行改序：

- 逐个读取任务文件 `<seq>-<task-title>.md`，按其「工作区」（引用登记文件中的工作区名称）、「验收标准」与「实现内容」完成代码编写；
- 执行每个子任务时先检查其工作区：工作区**为空** → 自行发挥；工作区**非空** → 先分析现有代码是否符合任务设计，若不符合，则依据任务设计修改现有代码；
- 只改任务声明的工作区：名称对应登记文件工作区表格中的「读写」项时可新增或修改，对应「只读」项时只读不改；
- 任务达到其「验收标准」后，再标记该任务完成；
- 每完成一项子任务，生成一份任务报告 `docs/dev-docs/<开发序号>/task-report/<seq>-<task-title>.md`，开发序号取该任务所属开发文档的序号；报告内容须包含：
  - **修改的信息**：本次改了什么、为何修改（对应任务设计）；
  - **修改的文件与文件内位置**：文件路径及具体位置（行号、函数名或段落）；
  - **检查结果**：对照本任务「验收标准」逐项核对的结论；
- 每完成一项任务，立即提交一次 commit：提交信息由该任务内容总结而来，长度不超过 128 字符；任务报告随该任务的 commit 一并提交；
- 每次 commit 后随即执行一次 push。

全部任务完成且均已提交、push 后，进入第 3 步。

### 3. 函数的编写

函数 / 方法的编写遵循函数的设计规则。

**参考文件**：本 Skill 附带 `references/function-design-rules.md`（公有接口设计规范、伪代码实例、校验规则）。此处仅**显式声明其存在**；**仅在编写函数时才读取该文件内容**，其余阶段不展开其正文。

**调用关系规则**：本 Skill 附带 `references/call-relationship-rules.md`（同模块 / 跨模块的方法调用方式与依赖注入约束）。此处仅**显式声明其存在**；**仅在编写方法间的调用时才读取该文件内容**，其余阶段不展开其正文。

**资源生命周期规则**：本 Skill 附带 `references/resource-lifecycle-rules.md`（对象销毁时独占资源的释放责任、释放顺序与借用 / 共享引用处理）。此处仅**显式声明其存在**；**仅在编写对象销毁、资源获取或释放相关代码时才读取该文件内容**，其余阶段不展开其正文。

### 4. Rust 项目的额外约束

实现语言为 Rust 时，还须遵循 Rust 全局约束。

**参考文件**：本 Skill 附带 `references/rust-global-constraints.md`。此处仅**显式声明其存在**；**仅在编写 Rust 代码时才读取该文件内容**，其余阶段不展开其正文。

其他语言暂不提供额外约束文件，沿用第 3 步的函数设计规则。

### 5. 校验

全部任务完成后，逐项检查以下内容：

- `task-list/` 下每个任务文件在 `task-report/` 下都有同名任务报告，且报告非空，覆盖「修改的信息」「修改的文件与文件内位置」「检查结果」三项；
- 每个任务均已对照其「验收标准」通过，且改动只落在任务声明的读写工作区与 `task-report/`；
- 每个任务都有对应 commit，且均已 push。

**校验脚本**：本 Skill 附带 `evals/verify_artifacts.py`（校验任务报告的位置、命名与内容非空，且与 `task-list/` 任务文件一一对应）。此处仅**显式声明其存在**；**仅在本步骤**调用该脚本：

```bash
python evals/verify_artifacts.py docs/dev-docs/<开发序号>
```

全部检查通过后输出产物并结束本阶段；任一项不通过时，对应任务不得标记完成，回到第 2 步修正后重新校验。

## 输入 / 输出

```text
implementer(
  开发序号: string,          // 必填：取自 docs/dev-docs/<开发序号>/dev-context.md 的登记值
  任务分支: string,          // 必填：取自同一登记文件的「分支名」，本阶段全部改动提交于此
) -> SkillResult

SkillResult {
  status: "success" | "partial" | "failed",
  artifacts: string[],      // 任务报告路径列表
  errors: SkillError[]
}

SkillError {
  code: string,             // 与「失败处理」的错误码一一对应
  message: string,
  recoverable: boolean
}
```

输出产物：

1. **代码改动**：落在任务声明的读写工作区，对应 `task-list/` 中各任务文件。
2. **任务报告** `docs/dev-docs/<开发序号>/task-report/<seq>-<task-title>.md`：与任务文件一一对应，含「修改的信息」「修改的文件与文件内位置」「检查结果」。
3. **commit 记录**：每个任务一次 commit，提交信息不超过 128 字符，任务报告随 commit 提交，完成后随即 push 到登记文件指定的分支。

## 失败处理

| 失败场景             | 判定条件                                                            | 处理动作                                                                            |
| ---------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 开发文档或流程图缺失       | `docs/dev-docs/<开发序号>/` 下不存在 `<title>-dev-doc.md` 或 `<title>-flowchart.md`，或内容为空 | 中断，不改动代码；回到 `dev-doc-writer` 阶段补齐（`DEV_DOC_MISSING`）                            |
| 任务清单或执行顺序缺失      | `task-list/` 下不存在 `execution-order.md`，或其中引用的任务文件缺失                        | 中断，不改动代码；回到 `task-planner` 阶段补齐（`TASK_LIST_MISSING`）                            |
| 开发上下文登记文件缺失 | `docs/dev-docs/<开发序号>/dev-context.md` 不存在，或登记的开发序号与 `task-list/` 目录不一致 | 中断；回到 `spec-manager` 补齐登记文件后再执行（`CONTEXT_MISSING`） |
| git 或 gh 不可用     | `git status` 或 `gh auth status` 报错，或登记文件指定的项目根目录 / 分支不可用               | 中断并保留原始报错；提示人类配置 git / gh 后重试，禁止跳过提交或 push（`GIT_UNAVAILABLE`）                   |
| 登记工作区不可用         | 登记文件指定的项目根目录或分支不存在、无法进入或与当前仓库不一致 | 中断；回到 `spec-manager` 修复登记值后再执行，禁止自行创建工作区（`WORKSPACE_UNAVAILABLE`）       |
| 当前分支不是登记分支 | `git branch --show-current` 与登记「分支名」不一致，且切换失败 | 中断并保留原始报错；提示人类检查分支状态后重试，禁止自行创建分支（`BRANCH_MISMATCH`） |
| 改动越界             | 改动出现在只读工作区、任务声明的工作区之外或 `task-report/` 之外                        | 中断；回退越界改动后重新实现该任务（`OUT_OF_SCOPE_CHANGE`）                                        |
| 验收标准未通过          | 任务「验收标准」中任一项核对不通过                                               | 不得标记该任务完成；修正实现后重新验收（`ACCEPTANCE_FAILED`）                                        |
| commit 或 push 失败 | git / gh 命令非零退出，或提交钩子失败                                         | 中断并保留原始报错；修复问题后新建 commit，禁止 `--amend`、`--no-verify`；push 失败同样不得跳过（`GIT_FAILED`） |
| 改动涉及 Git 系文件 | 任务或实现需要写入 `.git/`、`.gitignore`、`.gitattributes`、`.gitmodules` 等 Git 系文件 | 中断该任务并还原对 Git 系文件的改动；向人类说明原因，由人类决定后续处理（`GIT_FILE_PROTECTED`） |
| 产物校验未通过          | 「5. 校验」中任一项不满足，或 `verify_artifacts.py` 以退出码 1 结束                | 本阶段不得收尾；按校验结果回到第 2 步修正后重新校验（`VALIDATION_FAILED`）                                |

## 示例

### 示例 1：按清单实现两个任务（成功）

输入：

```text
开发序号：001
任务分支：feat/001-order
```

关键步骤：读取 `docs/dev-docs/001/order-system-dev-doc.md`、`order-system-flowchart.md` 与 `task-list/execution-order.md` → 按登记分支 `feat/001-order` 自检并切换 → 依次实现「001 create-orders-table」「002 create-order-validation」，各生成同名任务报告并 commit、push → 运行 `verify_artifacts.py` 校验通过。

输出：

```text
status: success
artifacts: [
  "docs/dev-docs/001/task-report/001-create-orders-table.md",
  "docs/dev-docs/001/task-report/002-create-order-validation.md"
]
errors: []
```

### 示例 2：任务清单缺失（失败）

输入：

```text
开发序号：001
任务分支：feat/001-order
```

输出：

```text
status: failed
errors: [
  { code: "TASK_LIST_MISSING", message: "docs/dev-docs/001/task-list/ 下不存在 execution-order.md，已暂停", recoverable: true }
]
处理动作：中断；回到 task-planner 阶段补齐任务清单后再进入本阶段
```

