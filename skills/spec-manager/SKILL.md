---
name: spec-manager
description: 开发流程的管理角色（不占阶段序号）：流程启动时检查项目现状并生成 / 更新 Rust 编码规范与项目目录架构规范，规范变更写入迁移信息；issue-writer 创建 Issue 后调用一次，一次性分配开发序号、开发分支与本次开发项目目录工作区（名称 / 类型（只读 | 读写）/ 目录，至少一条读写），创建 docs/dev-docs/<开发序号>/ 骨架并写入统一开发上下文登记文件。当用户提到「开发规范」「编码规范」「目录架构」「分配开发序号」「准备开发分支」「确定开发工作区」「开发信息登记」时使用。
compatibility: python3.9+；依赖 git（branch 是必需能力）；本版本仅支持 Rust 项目。
metadata:
  author: XK_XK
  version: 3.0
---

# spec-manager

开发流程的管理角色，不是阶段链路中的一站：负责独占维护项目的 Rust 编码规范与项目目录架构规范，并独占分配每次开发的序号、分支与项目目录工作区清单（只读 / 读写）。所有分配结果写入统一登记文件，其他 Skill 只读规范、只按登记值执行。

## 适用场景

- 适用：流程启动时由编排器调用，检查项目现状并生成 / 更新 `docs/dev-standards/` 下的两份规范；`issue-writer` 确认需求并创建 Issue 后调用一次，分配开发序号、`feat/<Issue编号>-<简述>` 分支与本次开发项目目录工作区，并创建目录骨架与登记文件；用户提到「开发规范」「目录架构」「开发序号」「开发分支」「工作区」时使用。
- 不适用：需求收敛与 Issue 创建（由 `issue-writer` 处理）；状态流转流程图、公有接口契约与开发文档（由 `dev-doc-writer` 处理）；Rust 以外语言的规范生成；规范的可执行校验（clippy / fmt 配置、CI 规则）。

## 必要前提

1. **执行模式可判定**：本次调用是「启动检查（bootstrap）」还是「开发信息分配（allocate）」。无法判定时必须用 `AskUserQuestion` 询问用户（选项为「启动检查」「开发信息分配」），不得自行猜测。
2. **项目语言可判定**：项目根存在 `Cargo.toml`，或用户明确确认本项目为 Rust 项目；无法判定时必须用 `AskUserQuestion` 询问用户（选项为「Rust」「其他语言」）。判定为其他语言时不满足，见「失败处理」的 `UNSUPPORTED_LANGUAGE`。
3. **项目是可用的 git 仓库**：`git rev-parse --show-toplevel` 能返回仓库根目录；不能返回时中断，提示用户先初始化或修正 git 仓库。
4. **开发信息分配模式已有已确认 Issue**：能确认本次开发的 Issue 编号与标题（本地留档 `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`，或由 `issue-writer` 返回的远端 Issue 链接）。不满足时中断并回流 `issue-writer`（`ISSUE_MISSING`）。
5. **授权标记可创建**：能写入 `<仓库根>/.git/from-issue-to-pr/spec-manager.lock`；hooks 依据该标记放行本 Skill 对规范、序号目录与分支的独占操作。无法创建时中断，提示用户检查 `.git` 目录权限（`LOCK_UNAVAILABLE`）。
6. **开发信息分配模式下两份规范已存在**：`docs/dev-standards/rust-coding-standards.md` 与 `docs/dev-standards/project-architecture-standards.md` 均已由流程启动时的启动检查生成；缺失时中断，先执行启动检查（`SPEC_MISSING`）。

## 执行约束

- 必须：作为开发规范、开发序号目录骨架、开发上下文登记文件与开发分支的创建与登记者；分支只登记名称，不锁定、不独占。禁止其他 Skill 创建 / 重命名 / 删除分支，只允许切换到登记分支。
- 必须：规范文档只保留最新约束；发生变更时把「原约束 + 新约束 + 变更原因」写入 `docs/dev-standards/migration-info/<开发序号>-<规范短名>.md`（规范短名为 `rust-coding-standards` 或 `project-architecture-standards`）。启动检查模式尚未分配开发序号时，迁移信息文件名中的 `<开发序号>` 取 `000`，表示非某次开发引入的规范维护。
- 必须：规范文档中的每条约束都要标注来源——现状归纳或实践补齐；来源标注规则见 `references/rust/coding-standards-checklist.md`。
- 必须：开发信息分配模式一次性产出开发序号、分支名、项目根目录与工作区清单（名称、类型、目录）四项，并写入 `docs/dev-docs/<开发序号>/dev-context.md`；四项缺一不可，工作区清单至少一条为「读写」。
- 必须：执行开始前创建 `<仓库根>/.git/from-issue-to-pr/spec-manager.lock`，全部动作结束或中断时删除该标记；除本 Skill 外，任何 Skill 禁止创建、保留或伪造该标记。
- 必须：严格遵守「规范文档 → 开发序号与目录骨架 → 开发分支 → 本次开发工作区」的顺序，上一环节未完成禁止进入下一环节。
- 必须：一次开发只使用一个开发分支；多个工作区都位于项目根目录内，不额外创建分支，也不创建与仓库同级的独立工作目录。
- 必须：凡需要用户确认或选择的环节（执行模式、语言判定、序号、分支名、目录架构方案、工作区名称 / 类型 / 目录、分支冲突处理、失败处理去向），一律使用 `AskUserQuestion`（或同类选项式接口）给出可选方案，禁止只以纯文本开放式提问；用户可通过「Other」补充选项之外的内容。分支名按 `feat/<Issue编号>-<简述>` 规则归纳后确认。唯一例外为流程启动时由入口输出的「请描述本次开发计划的需求」。
- 禁止：修改其他 Skill 的文件；禁止修改业务代码、`Cargo.toml` 或既有构建配置。
- 禁止：在无 Issue 编号时自行编造分支名；无 Issue 时不得进入开发信息分配模式。
- 禁止：规范文档中并存历史版本内容；历史变更只出现在 `docs/dev-standards/migration-info/` 下。
- 禁止：由其他 Skill 代为写入开发上下文登记文件，或把登记值改为未经本 Skill 确认的值。
- 只能修改：`docs/dev-standards/`（两份规范文档 + `migration-info/`）、`docs/dev-docs/<开发序号>/` 目录骨架与 `dev-context.md`、开发分支、项目根内为本次开发工作区新建的空目录、`.git/from-issue-to-pr/spec-manager.lock`。

**参考文件**：本 Skill 附带以下参考材料，此处仅**显式声明其存在**，不展开其正文：

- `references/rust/coding-standards-checklist.md`（Rust 编码规范五类章节的检查项与来源标注口径）：**仅在第 2 步生成或更新编码规范时**读取；
- `references/rust/project-architecture-scan.md`（目录扫描范围、职责描述口径与无目录架构时的推荐方案）：**仅在第 3、7 步扫描或描述项目目录架构时**读取；
- `assets/rust-coding-standards-template.md`（编码规范文档模板）：**仅在第 2 步写入编码规范时**读取；
- `assets/project-architecture-template.md`（目录架构规范文档模板）：**仅在第 3 步写入目录架构规范时**读取；
- `assets/migration-info-template.md`（迁移信息模板）：**仅在第 2、3、7 步写入迁移信息时**读取；
- `assets/dev-context-template.md`（开发上下文登记文件模板）：**仅在第 7 步写入登记文件时**读取；
- `evals/verify_artifacts.py`（产物校验脚本）：**仅在第 8 步**调用。

## 工作流程

### 1. 判定执行模式并完成前置校验

- 判定本次调用为「启动检查」还是「开发信息分配」；无法判定时用 `AskUserQuestion` 询问用户。
- 确认项目根：`git rev-parse --show-toplevel` 返回仓库根目录；读取 `Cargo.toml` 或经用户确认语言为 Rust，否则中断（`UNSUPPORTED_LANGUAGE` / `REPO_INVALID`）。
- 创建授权标记 `<仓库根>/.git/from-issue-to-pr/spec-manager.lock`；创建失败时中断（`LOCK_UNAVAILABLE`）。
- 记录已有产物：`docs/dev-standards/rust-coding-standards.md`、`docs/dev-standards/project-architecture-standards.md` 是否存在；`docs/dev-docs/` 下已有开发序号目录；创建 `docs/dev-standards/migration-info/`（不存在时）。

进入下一步的判定条件：执行模式已判定；启动检查模式进入第 2 步，开发信息分配模式跳过第 2～4 步、直接进入第 5 步。

### 2. 启动检查模式：扫描并生成 / 更新 Rust 编码规范

本步仅在启动检查模式下执行；开发信息分配模式不修改编码规范。

- 扫描代码现状，归纳项目实际采用的约定，覆盖五类章节：命名、错误处理、所有权 / 借用、文档注释、模块组织与可见性。
- 缺失或明显不规范的地方，用通用 Rust 最佳实践补齐，并标注为「实践补齐」；来自代码现状的条目标注为「现状归纳」。
- 已有规范文档时，只更新与现状不一致的条目，并记录「变更项：原约束 → 新约束 → 变更原因」。
- 写入 `docs/dev-standards/rust-coding-standards.md`，文档内只保留最新约束；存在变更项时按 `assets/migration-info-template.md` 写入 `docs/dev-standards/migration-info/000-rust-coding-standards.md`。
- **参考文件**：`references/rust/coding-standards-checklist.md` 与 `assets/rust-coding-standards-template.md` 在本步读取。

进入下一步的判定条件：编码规范文档存在且内容非空。

### 3. 启动检查模式：扫描并生成 / 更新项目目录架构规范

本步仅在启动检查模式下执行；开发信息分配模式不修改目录架构规范。

- 已有目录结构时，按模板同时给出目录树与目录职责表（逐个目录描述职责），写入 `docs/dev-standards/project-architecture-standards.md`；扫描范围与描述口径按参考文件执行。
- 项目尚无目录架构规划时，用 `AskUserQuestion` 给出推荐方案供用户选择（选项至少包含「采用推荐方案」「在现有目录上补充说明」「由我描述（Other）」），按用户选择写入。
- 已有规范文档时，只更新发生变化的目录职责，并记录变更项；存在变更项时按迁移信息规则写入 `docs/dev-standards/migration-info/000-project-architecture-standards.md`。
- **参考文件**：`references/rust/project-architecture-scan.md` 与 `assets/project-architecture-template.md` 在本步读取。

进入下一步的判定条件：目录架构规范文档存在且每个目录都有职责描述，目录架构方案已由用户确认。

### 4. 启动检查模式收尾：校验并结束

- 启动检查模式不分配开发序号、不创建开发分支、不写登记文件。
- 执行第 8 步的校验（不传开发序号），通过后删除授权标记并结束。
- 本步仅在启动检查模式下执行；开发信息分配模式直接进入第 5 步。

### 5. 分配开发信息：确认开发序号与分支名

- 扫描 `docs/dev-docs/` 取最大序号 +1 作为候选序号；若本次 Issue 已归档在某序号目录下，优先把该序号作为首选候选。
- 用 `AskUserQuestion` 请用户确认开发序号，选项给出上述候选，其他值由用户通过「Other」自行填写。
- 从 Issue 编号与标题归纳分支名 `feat/<Issue编号>-<简述>`，用 `AskUserQuestion` 确认（给出归纳结果，其他值由用户通过「Other」填写）。
- 检查 `git branch` 是否已存在同名分支，冲突时中断并用 `AskUserQuestion` 询问用户（选项为「复用已有分支」「换序号新建」「取消本次执行」），禁止直接覆盖（`WORKSPACE_EXISTS`）。

进入下一步的判定条件：开发序号与分支名已由用户确认，分支名未被占用。

### 6. 创建开发序号目录骨架

- 创建 `docs/dev-docs/<开发序号>/`，并预建 `task-list/`、`test-process/`、`task-report/`、`test-report/` 四个子目录。

进入下一步的判定条件：开发序号目录与四个子目录均已创建。

### 7. 创建开发分支，确定并登记本次开发工作区

- 以当前仓库 HEAD 为基准创建分支 `feat/<Issue编号>-<简述>`（`git branch <分支名>`）；创建后复核 `git branch` 中存在对应条目。本次开发只使用这一个分支，多个工作区都位于项目根目录内。
- 扫描项目根目录内的仓库目录，结合 Issue 需求与 `docs/dev-standards/project-architecture-standards.md` 的职责表，提出本次开发涉及的工作区候选清单，每条包含名称、类型（只读 / 读写）与目录（项目根相对路径）；一次开发涉及分层实现或跨多个相关目录时，按实际改动需要列出多条候选。
- 用 `AskUserQuestion` 逐项确认每个工作区的名称、类型与目录：
  - 名称：给出候选名称，其他值由用户通过「Other」填写；名称在同一份登记文件内唯一；
  - 类型：选项为「读写」「只读」；
  - 目录：给出候选目录（如 `src/<模块>/`），其他值由用户通过「Other」填写；
  - 候选目录已存在但职责不符时，用 `AskUserQuestion` 询问用户（选项为「沿用并扩展职责」「新建其他目录」「取消本次执行」）。
- 工作区清单至少一条为「读写」；全部为「只读」时中断，用 `AskUserQuestion` 请用户补充读写工作区后重新确认。
- 读写工作区的目录不存在时，在项目根目录内创建该目录；本步只创建目录，禁止写入业务代码。
- 将读写工作区的新目录登记到 `docs/dev-standards/project-architecture-standards.md` 的目录树与职责表；该登记属于规范变更，按迁移信息规则写入 `docs/dev-standards/migration-info/<开发序号>-project-architecture-standards.md`。
- 按 `assets/dev-context-template.md` 写入 `docs/dev-docs/<开发序号>/dev-context.md`，内容为开发序号、分支名、项目根目录与工作区表格（名称 / 类型（只读 | 读写）/ 目录）；该文件是其他 Skill 的唯一取值来源。分支只登记名称，不锁定、不独占，由各阶段执行前按登记分支自检并切换。

进入下一步的判定条件：开发分支已创建并复核通过，工作区清单已确认且至少一条为「读写」、目录在项目根目录内存在，登记文件内容齐全。

### 8. 校验并收尾

- 逐项检查：两份规范文档存在且内容非空；`docs/dev-standards/migration-info/` 存在；开发信息分配模式下 `docs/dev-docs/<开发序号>/` 及其四个子目录存在、`dev-context.md` 内容齐全且工作区表格至少一条为「读写」；开发分支已复核通过。
- 调用校验脚本：

```bash
# 启动检查模式
python skills/spec-manager/evals/verify_artifacts.py <项目根>

# 开发信息分配模式
python skills/spec-manager/evals/verify_artifacts.py <项目根> <开发序号>
```

脚本校验规范文档、迁移信息目录、目录骨架、登记文件与工作区表格；开发分支与各工作区目录由 Agent 按第 7 步的复核结果确认。

全部检查通过后删除授权标记，输出产物并结束；任一项不通过时回到对应步骤修正后重新校验，修正仍失败时删除授权标记并中断。

## 输入 / 输出

```text
spec_manager(
  模式: "bootstrap" | "allocate",     // 必填：bootstrap=流程启动检查；allocate=Issue 创建后一次性分配开发信息
  项目根: string,                     // 必填：git 仓库根目录
  语言: "rust",                       // 必填：本版本仅支持 rust，其他值直接失败
  已确认Issue: string | null,         // allocate 必填：Issue 链接或本地留档路径；bootstrap 为 null
  开发序号: number | null,            // allocate 可选：用户已确认的序号；缺省按扫描结果给出候选
  分支名: string | null,              // allocate 可选：feat/<Issue编号>-<简述>；缺省按 Issue 标题归纳后请用户确认
  工作区: Workspace[] | null,         // allocate 可选：本次开发工作区清单（名称 / 类型 / 目录），至少一条读写；缺省按仓库扫描与 Issue 需求给出候选，经用户逐项确认
  目录架构方案: string | null,        // 可选：用户确认的目录职责描述或推荐方案；缺省按扫描结果生成
) -> SkillResult

Workspace {
  名称: string,                // 同一份登记文件内唯一，任务文件的「工作区」字段引用此名称
  类型: "只读" | "读写",       // 至少一条为「读写」
  目录: string                 // 项目根相对路径
}

SkillResult {
  status: "success" | "failed",
  artifacts: string[],        // 规范文档、迁移信息文件（如有）、docs/dev-docs/<开发序号>/ 骨架与登记文件、分支名
  开发信息: {                 // allocate 模式返回，四项即登记文件内容；bootstrap 模式为 null
    开发序号: number,
    分支名: string,
    项目根目录: string,
    工作区: Workspace[]
  } | null,
  errors: SkillError[]
}

SkillError {
  code: string,               // 与「失败处理」的错误码一一对应
  message: string,
  recoverable: boolean
}
```

## 失败处理

| 失败场景 | 判定条件 | 处理动作 |
| --- | --- | --- |
| 非 Rust 项目 | 项目根无 `Cargo.toml`，且用户确认为其他语言 | 中断；说明本版本仅支持 Rust，不生成任何规范文档（`UNSUPPORTED_LANGUAGE`） |
| 执行模式无法判定 | 用户未明确本次是启动检查还是开发信息分配 | 中断；用 `AskUserQuestion` 询问（「启动检查」「开发信息分配」）后再继续（`MODE_UNKNOWN`） |
| git 仓库不可用 | `git rev-parse --show-toplevel` 失败或返回空 | 中断并保留原始报错；提示用户检查仓库后重试（`REPO_INVALID`） |
| 授权标记无法创建 | `.git/from-issue-to-pr/spec-manager.lock` 写入失败 | 中断并保留原始报错；提示用户检查 `.git` 目录权限后重试，禁止绕过标记直接执行（`LOCK_UNAVAILABLE`） |
| 缺少已确认 Issue | 分配模式下无法确认 Issue 编号或标题 | 中断并回流 `issue-writer`；不创建任何开发产物（`ISSUE_MISSING`） |
| 开发规范缺失 | 分配模式下两份规范文档缺失 | 中断；先执行启动检查生成规范，再重新分配（`SPEC_MISSING`） |
| 目录架构方案未确认 | 项目无目录架构，且用户未选择推荐方案或自述方案 | 中断；用 `AskUserQuestion` 给出方案选项，确认后再写入（`DESIGN_UNCONFIRMED`） |
| 开发序号未确认 | 用户未确认 `<开发序号>` | 中断；用 `AskUserQuestion` 给出候选序号（含「Other」）后再创建骨架（`SEQ_UNCONFIRMED`） |
| 分支名未确认 | 用户未确认 `feat/<Issue编号>-<简述>` | 中断；用 `AskUserQuestion` 确认分支名后再创建工作区（`BRANCH_UNCONFIRMED`） |
| 分支已存在 | 分支名已存在于 `git branch` | 中断；用 `AskUserQuestion` 询问（「复用已有」「换序号新建」「取消」），禁止直接覆盖（`WORKSPACE_EXISTS`） |
| 工作区未确认 | 已给出工作区候选，但用户未确认名称、类型或目录 | 中断；用 `AskUserQuestion` 逐项确认后再创建目录并登记到目录架构规范（`WORKSPACE_UNCONFIRMED`） |
| 工作区无读写项 | 工作区清单中没有任何「读写」工作区 | 中断；用 `AskUserQuestion` 请用户补充读写工作区后再写入登记文件（`WORKSPACE_NOT_WRITABLE`） |
| git 命令失败 | `git branch` 非零退出 | 中断并保留原始报错；不自动删除已创建的部分产物，提示用户确认后重试（`GIT_FAILED`） |
| 产物写入失败 | 写入 `docs/dev-standards/`、`docs/dev-docs/<开发序号>/` 或项目根内目录失败（路径非法、权限或磁盘错误） | 中断并保留原始报错；提示用户检查目录后重试（`WRITE_FAILED`） |
| 登记文件内容不全 | `dev-context.md` 缺少开发序号、分支名、项目根目录任一项，或工作区表格缺失、类型非法、没有「读写」项 | 中断；回到第 7 步补齐后重新校验（`CONTEXT_INCOMPLETE`） |
| 产物校验未通过 | 第 8 步任一项不满足，或 `verify_artifacts.py` 以退出码 1 结束 | 中断；回到对应步骤修正后重新校验（`VALIDATION_FAILED`） |

> 以上任一中断路径均须先删除授权标记 `.git/from-issue-to-pr/spec-manager.lock`，再向用户报告。

## 示例

### 示例 1：流程启动检查（成功）

输入：

```text
模式：bootstrap
项目根：E:\Demo-Rust
语言：rust
已确认Issue：null
```

关键步骤：判定为启动检查 → 创建授权标记 → 扫描并生成 `docs/dev-standards/rust-coding-standards.md` 与 `docs/dev-standards/project-architecture-standards.md`（首次生成，不写迁移信息）→ 校验通过 → 删除授权标记。

输出：

```text
status: success
artifacts: [
  "docs/dev-standards/rust-coding-standards.md",
  "docs/dev-standards/project-architecture-standards.md",
  "docs/dev-standards/migration-info/"
]
开发信息: null
errors: []
```

### 示例 2：Issue 创建后一次性分配开发信息（成功）

输入：

```text
模式：allocate
项目根：E:\Demo-Rust
语言：rust
已确认Issue：https://github.com/<owner>/Demo-Rust/issues/12
开发序号：null
分支名：null
工作区：null
目录架构方案：null
```

关键步骤：更新两份规范（无变更不写迁移信息）→ 用户确认开发序号 4 → 确认分支名 `feat/12-order-cancel` → 创建 `docs/dev-docs/4/` 与四个子目录 → 创建分支 `feat/12-order-cancel` → 按需求提出工作区 `ordering`（读写，`src/ordering/`）与 `docs`（只读，`docs/`）并逐项确认 → 登记到目录架构规范并写迁移信息 → 写 `docs/dev-docs/4/dev-context.md` → 校验通过。

输出：

```text
status: success
artifacts: [
  "docs/dev-standards/rust-coding-standards.md",
  "docs/dev-standards/project-architecture-standards.md",
  "docs/dev-standards/migration-info/4-project-architecture-standards.md",
  "docs/dev-docs/4/",
  "docs/dev-docs/4/dev-context.md",
  "feat/12-order-cancel"
]
开发信息: {
  开发序号: 4,
  分支名: "feat/12-order-cancel",
  项目根目录: "E:/Demo-Rust",
  工作区: [
    { 名称: "ordering", 类型: "读写", 目录: "src/ordering/" },
    { 名称: "docs", 类型: "只读", 目录: "docs/" }
  ]
}
errors: []
```

### 示例 3：分支已存在（失败）

输入：

```text
模式：allocate
项目根：E:\Demo-Rust
语言：rust
已确认Issue：https://github.com/<owner>/Demo-Rust/issues/12
开发序号：4
分支名：feat/12-order-cancel
```

输出：

```text
status: failed
errors: [
  { code: "WORKSPACE_EXISTS", message: "分支已存在，已暂停", recoverable: true }
]
处理动作：中断并删除授权标记；用 `AskUserQuestion` 询问「复用已有」「换序号新建」「取消」，不得覆盖已有分支
```
