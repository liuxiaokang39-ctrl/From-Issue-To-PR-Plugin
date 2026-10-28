---
name: spec-manager
description: 规范与工作区准备阶段（位于 issue-writer 与 dev-doc-writer 之间）：为项目生成并维护 Rust 编码规范与项目目录架构规范，规范变更写入迁移信息；再为本次开发分配开发序号、创建 docs/dev-docs/<开发序号>/ 目录骨架，并创建与仓库同级的 worktree 与 feat/<Issue编号>-<简述> 分支，最后按需求在 worktree 内确认本次开发目录（复用或新建）并登记到目录架构规范。当用户提到「开发规范」「编码规范」「目录架构」「分配开发序号」「创建 worktree」「准备开发分支」「确定开发目录」「开发环境准备」，或需要在需求确认后、编写开发文档前准备规范与隔离工作区时使用。
compatibility: python3.9+；依赖 git（worktree / branch 是必需能力）；本版本仅支持 Rust 项目。
metadata:
  author: XK_XK
  version: 1.0
---

# spec-manager

位于 `issue-writer` 与 `dev-doc-writer` 之间：先把项目的 Rust 编码规范与目录架构规范建立起来，再为一次开发分配开发序号与隔离工作区，并按需求确认本次编码的开发目录，让后续阶段有统一约束和固定的工作目录。

## 适用场景

- 适用：需求确认之后、编写开发文档之前的准备阶段——生成 / 更新 Rust 编码规范与项目目录架构规范、把规范变更写入迁移信息、分配开发序号与目录骨架、创建 worktree 与开发分支、按需求确认本次开发目录并登记到目录架构规范；用户提到「开发规范」「编码规范」「目录架构」「开发序号」「worktree」「开发分支」「开发目录」等说法时使用。
- 不适用：需求收敛与 Issue 创建（由 `issue-writer` 处理）；状态流转流程图、公有接口契约与开发文档（由 `dev-doc-writer` 处理）；Rust 以外语言的规范生成；规范的可执行校验（clippy / fmt 配置、CI 规则）。

## 必要前提

1. **项目语言可判定**：项目根存在 `Cargo.toml`，或用户明确确认本项目为 Rust 项目；无法判定时必须用 `AskUserQuestion` 询问用户（选项为「Rust」「其他语言」）。判定为其他语言时不满足，见「失败处理」的 `UNSUPPORTED_LANGUAGE`。
2. **项目是可用的 git 仓库**：`git rev-parse --show-toplevel` 能返回仓库根目录；不能返回时中断，提示用户先初始化或修正 git 仓库。
3. **Issue 状态可判定**：能确认本次开发是否已有已确认 Issue（本地留档 `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`）。无法判定时用 `AskUserQuestion` 询问用户（选项为「已有 Issue，需创建分支」「尚无 Issue」）。
4. **开发序号未预先固定时可由用户确认**：进入第 4 步前，`<开发序号>` 必须已由用户确认；未确认时按第 4 步的候选方案用 `AskUserQuestion` 提问。

## 执行约束

- 必须：仅实现 Rust；`SKILL.md` 按语言分派，语言相关参考材料统一放在 `references/<语言>/` 下，当前只有 `references/rust/`，禁止创建其他语言的实现或目录。
- 必须：严格按「规范文档 → 开发序号与目录骨架 → worktree 与分支 → 本次开发目录」的单流程顺序执行，上一环节未完成禁止进入下一环节。
- 必须：规范文档只保留最新约束；发生变更时，变更内容写入 `docs/开发规范/迁移信息/<开发序号>-<规范名>.md`，并同时记录原约束与新约束。
- 必须：规范文档中的每条约束都要标注来源——现状归纳或实践补齐；来源标注规则见 `references/rust/coding-standards-checklist.md`。
- 必须：凡需要用户确认或选择的环节（语言判定、Issue 状态、目录架构方案、开发序号、分支名、本次开发目录、worktree 冲突处理、失败处理去向），一律使用 `AskUserQuestion` 给出可选方案，禁止只以纯文本开放式提问；用户可通过「Other」补充选项之外的内容。
- 禁止：修改其他 Skill 的文件；禁止修改业务代码、`Cargo.toml` 或既有构建配置。
- 禁止：在无 Issue 编号时自行编造分支名；无 Issue 时必须先按第 5 步询问用户。
- 禁止：规范文档中并存历史版本内容；历史变更只出现在 `docs/开发规范/迁移信息/` 下。
- 只能修改：`docs/开发规范/`（两份规范文档 + `迁移信息/`）、`docs/dev-docs/<开发序号>/` 目录骨架、git worktree 与开发分支、worktree 内为本次开发新建的空目录。

**参考文件**：本 Skill 附带以下参考材料，此处仅**显式声明其存在**，不展开其正文：

- `references/rust/coding-standards-checklist.md`（Rust 编码规范五类章节的检查项与来源标注口径）：**仅在第 2 步生成或更新编码规范时**读取；
- `references/rust/project-architecture-scan.md`（目录扫描范围、职责描述口径与无目录架构时的推荐方案）：**仅在第 3 步扫描或描述项目目录架构时**读取；
- `assets/rust-coding-standards-template.md`（编码规范文档模板）：**仅在第 2 步写入编码规范时**读取；
- `assets/project-architecture-template.md`（目录架构规范文档模板）：**仅在第 3 步写入目录架构规范时**读取；
- `assets/migration-info-template.md`（迁移信息模板）：**仅在第 4 步写入迁移信息时**读取；
- `evals/verify_artifacts.py`（产物校验脚本）：**仅在第 7 步**调用。

## 工作流程

### 1. 判定语言并读取现状

- 读取项目根，确认 `Cargo.toml` 存在或用户确认语言为 Rust；不是 Rust 时中断（`UNSUPPORTED_LANGUAGE`）。
- 记录已有产物：`docs/开发规范/Rust编码规范.md`、`docs/开发规范/项目目录架构规范.md` 是否存在；`docs/dev-docs/` 下已有开发序号目录；当前 Issue 本地留档所在目录。

进入下一步的判定条件：语言已判定为 Rust，且 git 仓库可用。

### 2. 扫描并生成 / 更新 Rust 编码规范

- 扫描代码现状，归纳项目实际采用的约定，覆盖五类章节：命名、错误处理、所有权 / 借用、文档注释、模块组织与可见性。
- 缺失或明显不规范的地方，用通用 Rust 最佳实践补齐，并标注为「实践补齐」；来自代码现状的条目标注为「现状归纳」。
- 已有规范文档时，只更新与现状不一致的条目，并在内存中记录「变更项：原约束 → 新约束」供第 4 步写入迁移信息。
- 写入 `docs/开发规范/Rust编码规范.md`；文档内只保留最新约束，不保留历史版本。
- **参考文件**：`references/rust/coding-standards-checklist.md` 与 `assets/rust-coding-standards-template.md` 在本步读取。

进入下一步的判定条件：编码规范文档存在且内容非空。

### 3. 扫描并描述项目目录架构

- 已有目录结构时，按模板同时给出目录树与目录职责表（逐个目录描述职责），写入 `docs/开发规范/项目目录架构规范.md`；扫描范围与描述口径按参考文件执行。
- 项目尚无目录架构规划时，用 `AskUserQuestion` 给出推荐方案供用户选择（选项至少包含「采用推荐方案」「在现有目录上补充说明」「由我描述（Other）」），按用户选择写入。
- 已有规范文档时，只更新发生变化的目录职责，并记录变更项供第 4 步使用。
- **参考文件**：`references/rust/project-architecture-scan.md` 与 `assets/project-architecture-template.md` 在本步读取。

进入下一步的判定条件：目录架构规范文档存在且每个目录都有职责描述，目录架构方案已由用户确认。

### 4. 分配开发序号、创建目录骨架并写入迁移信息

- 扫描 `docs/dev-docs/` 取最大序号 +1 作为候选序号；若本次 Issue 已归档在某序号目录下，优先把该序号作为首选候选。
- 用 `AskUserQuestion` 请用户确认序号，选项给出上述候选，其他值由用户通过「Other」自行填写。
- 创建 `docs/dev-docs/<开发序号>/`，并预建 `task-list/`、`test-process/`、`task-report/`、`test-report/` 四个子目录。
- 创建 `docs/开发规范/迁移信息/` 目录；仅当第 2、3 步记录了变更项时，按 `assets/migration-info-template.md` 写入 `docs/开发规范/迁移信息/<开发序号>-<规范名>.md`（`<规范名>` 取 `Rust编码规范` 或 `项目目录架构规范`）。
- 首次生成规范文档且此前不存在时，不写迁移信息。

进入下一步的判定条件：开发序号已由用户确认，目录骨架与迁移信息目录已创建。

### 5. 创建 worktree 与分支

- 判断 Issue 状态：
  - 已有 Issue：从 Issue 编号与标题归纳分支名 `feat/<Issue编号>-<简述>`，用 `AskUserQuestion` 确认分支名（给出归纳结果，其他值由用户通过「Other」填写）；
  - 尚无 Issue：用 `AskUserQuestion` 让用户选择「先补 Issue（回到 issue-writer）」或「仅做规范与骨架（跳过本步）」；选择前者时中断并回流，选择后者时跳过本步。
- 检查冲突：目标 worktree 路径或分支名已存在时，中断并用 `AskUserQuestion` 询问用户（选项为「复用已有 worktree 与分支」「换序号新建」「取消本次执行」）。
- 创建 worktree：路径为与仓库同级的 `<仓库名>-dev-<开发序号>`，分支为已确认的 `feat/<Issue编号>-<简述>`，以当前仓库 HEAD 为基准。
- 创建后由 Agent 复核 `git worktree list` 与 `git branch` 中存在对应条目。

进入下一步的判定条件：worktree 与分支已创建，或用户明确选择「仅做规范与骨架」。

### 6. 在 worktree 内分配本次开发目录

- 依据 Issue 需求与第 3 步的目录架构规范，判断本次编码应落在 worktree 内的哪个目录：
  - 已有目录职责匹配：用 `AskUserQuestion` 给出候选目录（如 `src/<模块>/`），请用户确认；
  - 无目录职责匹配：提出新建目录方案（路径、一句话职责、命名理由），用 `AskUserQuestion` 请用户确认（选项至少包含「采用新目录」「在现有目录上调整」「由我描述（Other）」）。
- 候选目录已存在但职责不符时，中断并用 `AskUserQuestion` 询问用户（选项为「沿用并扩展职责」「新建其他目录」「取消本次执行」）。
- 目录不存在时，在 worktree 内创建该目录；本步只创建目录，禁止写入业务代码。
- 将确认后的目录登记到第 3 步写入的同一份 `docs/开发规范/项目目录架构规范.md` 的目录树与职责表；该登记属于规范变更，按第 4 步的迁移信息规则写入 `docs/开发规范/迁移信息/<开发序号>-项目目录架构规范.md`，并与第 3 步的变更项合并到同一文件，不重复建文件。
- 用户在第 5 步选择「仅做规范与骨架」时，本步跳过。

进入下一步的判定条件：本次开发目录已由用户确认、在 worktree 内已存在，并已登记到目录架构规范；或用户选择「仅做规范与骨架」。

### 7. 校验

- 逐项检查：两份规范文档存在且内容非空；`docs/开发规范/迁移信息/` 存在；`docs/dev-docs/<开发序号>/` 及其下 `task-list/`、`test-process/`、`task-report/`、`test-report/` 四个子目录存在；worktree 与分支已在第 5 步复核通过；本次开发目录已在第 6 步确认并登记（用户选择「仅做规范与骨架」时除外）。
- 调用校验脚本：

```bash
python skills/spec-manager/evals/verify_artifacts.py <项目根> <开发序号>
```

脚本校验规范文档、迁移信息目录与目录骨架；worktree、分支与本次开发目录由 Agent 按第 5、6 步的复核结果确认。

全部检查通过后输出产物并结束本阶段；任一项不通过时回到对应步骤修正后重新校验。

## 输入 / 输出

```text
spec_manager(
  项目根: string,                   // 必填：git 仓库根目录
  语言: "rust",                     // 必填：本版本仅支持 rust，其他值直接失败
  已确认Issue: string | null,       // 可选：docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md；null 表示尚无 Issue
  开发序号: number | null,          // 可选：用户已确认的开发序号；缺省按第 4 步扫描结果给出候选
  分支名: string | null,            // 可选：feat/<Issue编号>-<简述>；缺省按 Issue 标题归纳后请用户确认
  开发目录: string | null,          // 可选：worktree 内用于本次编码的目录；缺省按需求与目录架构规范给出候选，经用户确认
  目录架构方案: string | null,      // 可选：用户确认的目录职责描述或推荐方案；缺省按扫描结果生成
) -> SkillResult

SkillResult {
  status: "success" | "partial" | "failed",   // partial：用户选择「仅做规范与骨架」，未创建 worktree、分支与开发目录
  artifacts: string[],        // 两份规范文档、迁移信息文件（如有）、docs/dev-docs/<开发序号>/ 骨架、worktree 路径、分支名与本次开发目录路径
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
| git 仓库不可用 | `git rev-parse --show-toplevel` 失败或返回空 | 中断并保留原始报错；提示用户检查仓库后重试（`REPO_INVALID`） |
| Issue 状态无法判定 | 无法确认本次开发是否已有 Issue | 中断；用 `AskUserQuestion` 询问用户（「已有 Issue，需创建分支」「尚无 Issue」）后再继续（`ISSUE_UNKNOWN`） |
| 目录架构方案未确认 | 项目无目录架构，且用户未选择推荐方案或自述方案 | 中断；用 `AskUserQuestion` 给出方案选项，确认后再写入（`DESIGN_UNCONFIRMED`） |
| 开发序号未确认 | 用户未确认 `<开发序号>` | 中断；用 `AskUserQuestion` 给出候选序号（含「Other」）后再创建骨架（`SEQ_UNCONFIRMED`） |
| worktree 或分支已存在 | 目标路径或分支名已存在于 `git worktree list` / `git branch` | 中断；用 `AskUserQuestion` 询问（「复用已有」「换序号新建」「取消」），不得直接覆盖（`WORKSPACE_EXISTS`） |
| git 命令失败 | `git worktree add` 或 `git branch` 非零退出 | 中断并保留原始报错；不自动删除已创建的部分产物，提示用户确认后重试（`GIT_FAILED`） |
| 开发目录未确认 | 已给出候选目录或新建目录方案，但用户未确认 | 中断；用 `AskUserQuestion` 确认后再创建目录并登记到目录架构规范（`DEV_DIR_UNCONFIRMED`） |
| 产物写入失败 | 写入 `docs/开发规范/`、`docs/dev-docs/<开发序号>/` 或 worktree 内目录失败（路径非法、权限或磁盘错误） | 中断并保留原始报错；提示用户检查目录后重试（`WRITE_FAILED`） |
| 产物校验未通过 | 第 7 步任一项不满足，或 `verify_artifacts.py` 以退出码 1 结束 | 中断；回到对应步骤修正后重新校验（`VALIDATION_FAILED`） |

## 示例

### 示例 1：已有 Issue，完成规范与工作区准备（成功）

输入：

```text
项目根：E:\Demo-Rust
语言：rust
已确认Issue：docs/dev-docs/4/Demo-Rust-4-issue.md（已确认）
开发序号：null
分支名：null
开发目录：null
目录架构方案：null
```

关键步骤：扫描并生成 `docs/开发规范/Rust编码规范.md` 与 `docs/开发规范/项目目录架构规范.md` → 用户确认开发序号 4 → 创建 `docs/dev-docs/4/` 与四个子目录 → 用户确认分支名 `feat/4-spec-manager` → 创建同级 worktree `Demo-Rust-dev-4` → 按需求提出开发目录 `src/ordering/` 并由用户确认 → 在 worktree 内创建该目录并登记到目录架构规范。

输出：

```text
status: success
artifacts: [
  "docs/开发规范/Rust编码规范.md",
  "docs/开发规范/项目目录架构规范.md",
  "docs/dev-docs/4/",
  "E:/Demo-Rust-dev-4",
  "feat/4-spec-manager",
  "E:/Demo-Rust-dev-4/src/ordering/"
]
errors: []
```

### 示例 2：尚无 Issue，仅做规范与骨架（部分成功）

输入：

```text
项目根：E:\Demo-Rust
语言：rust
已确认Issue：null
开发序号：5
分支名：null
开发目录：null
目录架构方案：采用推荐方案
```

关键步骤：生成两份规范文档 → 创建 `docs/dev-docs/5/` 与四个子目录 → 无 Issue，用户选择「仅做规范与骨架」→ 跳过 worktree、分支与开发目录。

输出：

```text
status: partial
artifacts: [
  "docs/开发规范/Rust编码规范.md",
  "docs/开发规范/项目目录架构规范.md",
  "docs/dev-docs/5/"
]
errors: []
处理动作：提示用户补齐 Issue 后可重新执行本 Skill 完成 worktree、分支与开发目录创建
```

### 示例 3：worktree 已存在（失败）

输入：

```text
项目根：E:\Demo-Rust
语言：rust
已确认Issue：docs/dev-docs/4/Demo-Rust-4-issue.md（已确认）
开发序号：4
分支名：feat/4-spec-manager
```

输出：

```text
status: failed
errors: [
  { code: "WORKSPACE_EXISTS", message: "worktree 或分支已存在，已暂停", recoverable: true }
]
处理动作：中断；用 `AskUserQuestion` 询问「复用已有」「换序号新建」「取消」，不得覆盖已有工作区
```
