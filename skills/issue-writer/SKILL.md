---
name: issue-writer
description: 需求确认阶段（阶段 A）：通过对话把模糊需求收敛为一份可评审的 Issue（范围边界、背景与目标、需求列表、每项需求的期望行为与期望结果），先确认「做什么 / 不做什么」再确认具体需求，在远端仓库创建 Issue 后调用 spec-manager 一次性分配开发序号、分支、项目根目录与开发工作区，并按返回的开发序号本地留档。
compatibility: python3.12+；依赖 git 与 gh CLI（GitHub CLI），执行时需要 git 与 gh 可用并已登录认证。
metadata:
  author: XK_XK
  version: 2.1
---

# issue-writer

把用户口述的模糊需求，通过对话收敛为一份可评审的 Issue，在远端仓库创建后调用 `spec-manager` 一次性取得开发信息，并按返回的开发序号完成本地留档，供后续阶段继续推进。

## 适用场景

- 适用：用户给出模糊、零散或未成型的需求描述，需要先收敛再产出 Issue；用户提到「需求确认」「整理需求」「写/创建 Issue」「把需求做成 Issue」等说法，以及需求列表、期望行为、期望结果、范围边界等输入形态。
- 不适用：需求已完全明确、无需对话收敛；Issue 的评审讨论；开发序号与工作区分配（由 `spec-manager` 处理）；以及 /docs 之外的普适文档编写（由其他 Skill 或人工处理）。

## 必要前提

1. **需求已收敛并确认**：已通过对话与用户逐条确认需求清单、每项需求的期望行为与期望结果、范围边界；未决项已列入「待确认问题」。不满足时必须用 `AskUserQuestion` 继续提问，不得进入制作 Issue 阶段。
2. **远端仓库类型可判断**：能确认项目远端是主仓库还是 fork 仓库；无法判断或没有远端仓库时，须先用 `AskUserQuestion` 向用户提问，选项至少包含「主仓库」「fork 仓库」「没有远端仓库」。
3. **gh CLI 可用**：执行 `gh auth status` 能确认已登录认证；未安装或未认证时，用 `AskUserQuestion` 向用户提问，选项为「安装/认证后继续」与「降级为仅本地留档」。
4. **spec-manager 可调用**：本 Skill 创建 Issue 后需要调用一次 `spec-manager` 分配开发信息；该 Skill 不可用时中断并报告，不自行分配开发序号或创建工作区。

## 执行约束

- 必须：只保留用户确认过的需求，不添加未经确认的需求、字段或章节（奥卡姆剃刀）。
- 必须：先确认「本期做什么、不做什么」，再确认具体需求；顺序不得颠倒。
- 必须：凡「是否需要该需求」「需求本身」「期望行为」「期望结果」存在不明确处，一律向用户提问并由用户决定；禁止自行脑补、假设或替用户拍板。
- 必须：开发序号、分支名、项目根目录与工作区一律取自 `spec-manager` 一次调用的返回值，本地留档只使用返回的开发序号；禁止自行确认序号或自建分支。
- 必须：开发规范（`docs/dev-standards/`）与开发上下文登记文件（`docs/dev-docs/<开发序号>/dev-context.md`）只读，禁止写入或改写。
- 必须：凡需要向用户提问或确认的环节（背景与范围、需求与验收标准、远端仓库类型、Issue 正文确认、失败处理去向），一律使用 `AskUserQuestion`（或同类选项式接口）给出可选方案，禁止只以纯文本开放式提问；用户可通过「Other」补充选项之外的内容。唯一例外为流程启动时由入口输出的「请描述本次开发计划的需求」。
- 禁止：把已被推翻、已过时的旧需求迁移进 Issue——报告只包含最新需求。
- 禁止：除「远端 Issue 与本地留档文件」外，新增其他文件或目录；禁止创建 `docs/dev-docs/<开发序号>/` 目录骨架（由 `spec-manager` 创建）。
- 只能修改：通过 `gh issue create` 在已确认的远端仓库创建 Issue；本地留档写入 `spec-manager` 已建好的 `docs/dev-docs/<开发序号>/` 目录。

**参考文件**：本 Skill 附带三份参考材料，此处仅**显式声明其存在**，不展开其正文：

- `assets/issue-template.md`（Issue 正文结构模板）：**仅在制作 Issue 时**读取该文件内容并据其结构撰写；
- `references/GitHub-CLI.md`（gh 命令参考，含 `gh issue create`）：**仅在创建 Issue、需要使用 gh 命令时**读取；
- `references/GitHub-submit.md`（git 提交规范与 Git 安全约束）：**仅在创建 Issue、需要进行 git 操作时**读取。

## 工作流程

### 第 1 步：先确认「做什么 / 不做什么」，再确认背景与目标

使用 `AskUserQuestion` 先确认范围边界，再补齐背景与目标；每个问题都给出可选方案：

- **本期做什么**（范围边界）；
- **本期不做什么**（范围边界）；
- **为什么做**；
- **解决什么问题**；
- **提供什么功能**。

范围边界确认后，才能进入第 2 步确认具体需求；不得颠倒顺序。

### 第 2 步：逐条确认需求与验收标准（合并「需求列表」与「期望行为/期望结果」）

对每一条需求，使用 `AskUserQuestion` 逐项确认：「必要需求 / 可选需求」必须作为二选一选项给出，其余问题给出可选方案，开放式内容由用户通过「Other」补充：

- **这条需求是必要需求还是可选需求**；
- **使用场景是什么**（什么条件下触发）；
- **系统应如何表现**（行为）；
- **如何验证达成**（可观察、可验证的结果）。

### 第 3 步：汇总 Issue 并请用户确认

- 只写最新确认的需求；
- 不允许有未确认内容；
- 用 `AskUserQuestion` 请用户确认 Issue 正文，选项为「确认并创建 Issue」「需要修改」「暂不创建」；用户确认正文后再创建 Issue。

### 第 4 步：创建 Issue、取得开发信息并本地留档

创建前判断主仓库/fork：

- 主仓库 → 在主仓库创建；
- fork 仓库 → 在被 fork 的仓库创建；
- 无法判断远端类型或没有远端仓库时，用 `AskUserQuestion` 向用户提问（选项为「主仓库」「fork 仓库」「没有远端仓库」），确认后再执行。

用 `gh issue create` 创建 Issue，取得 Issue 链接与 Issue 编号。创建成功后：

- 用 Issue 链接调用一次 `spec-manager`（模式为「开发信息分配」），取得开发序号、分支名（`feat/<Issue编号>-<简述>`）、项目根目录、工作区清单四项返回值；`spec-manager` 负责创建目录骨架、开发上下文登记文件与分支，本 Skill 只接收返回值，不重复确认或改写；
- 开发信息缺失或调用失败时中断，保留已创建的 Issue 链接并报告错误；
- 按返回的开发序号本地留档：目录为 `docs/dev-docs/<开发序号>/`（目录已由 `spec-manager` 创建），文件名为 `<仓库名>-<issue编号>-issue.md`（仓库名取实际创建 Issue 的仓库名，如 `From-Issue-To-PR-Skill-12-issue.md`），内容只包含用户确认过的最新需求；
- 回传 Issue 链接与本地留档路径。

### 第 5 步：校验

创建与留档完成后，逐项检查以下内容：

- 远端 Issue 已创建，并取得 Issue 链接；
- 本地留档文件 `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md` 存在且内容非空，文件名中的仓库名、issue 编号与实际创建的 Issue 一致；
- 留档内容只包含用户确认过的最新需求，无未确认内容或已过时需求；
- 已取得 `spec-manager` 返回的四项开发信息，未自行分配序号或创建工作区。

**校验脚本**：本 Skill 附带 `evals/verify_artifacts.py`（校验本地留档的位置、命名与内容非空）。此处仅**显式声明其存在**；**仅在本步骤**调用该脚本：

```bash
python evals/verify_artifacts.py docs/dev-docs/<开发序号>
```

全部检查通过后输出产物并结束本阶段；任一项不通过时，回到第 4 步修正本地留档后重新校验。

## 输入 / 输出

```text
issue_writer(
  模糊需求: string,                            // 必填：用户口述的原始需求
  需求列表: Requirement[],                     // 必填：与用户逐条确认后的需求（含是否必需）
  期望行为与期望结果: Map<编号, {行为, 结果}>, // 必填：每项需求的行为与可验证结果
  范围边界: string,                            // 可选：确认「做什么 / 不做什么」后写入
  远端仓库类型: "main" | "fork" | null,        // 可选：无法判定时先用 AskUserQuestion 向用户提问
) -> SkillResult

SkillResult {
  status: "success" | "partial" | "failed",
  artifacts: string[],        // 远端 Issue 地址 + 本地留档文件路径
  开发信息: {                 // 来自 spec-manager 的一次调用返回值
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
| 需求信息不足 | 存在未确认的需求、期望行为或期望结果，却直接进入制作 Issue | 中断；用 `AskUserQuestion` 逐条向用户提问补齐，补齐前不得写入 Issue（`INPUT_INCOMPLETE`） |
| gh 认证失败 | `gh auth status` 未认证，或 `gh issue create` 因认证报错 | 中断并保留原始报错；用 `AskUserQuestion` 询问用户选择「安装/认证后重试」或「降级为仅本地留档」（`AUTH_FAILED`） |
| `gh issue create` 失败 | 命令非零退出、网络或权限错误 | 重试一次；仍失败则中断，保留原始报错，仅完成本地留档，并提示用户改为手动创建（`CREATE_FAILED`） |
| 远端仓库类型无法判断 | 无法确认主仓库或 fork，或没有远端仓库 | 中断；用 `AskUserQuestion` 询问目标仓库（「主仓库」「fork 仓库」「没有远端仓库」）后再执行（`REPO_UNKNOWN`） |
| spec-manager 调用失败 | `spec-manager` 未返回完整的四项开发信息，或执行失败 | 中断并保留已创建的 Issue 链接；向用户报告缺失项，待 `spec-manager` 补齐后再本地留档，禁止自行补序号或自建工作区（`SPEC_MANAGER_FAILED`） |
| 留档校验未通过 | 「第 5 步：校验」中任一项不满足，或 `verify_artifacts.py` 以退出码 1 结束 | 中断；回到第 4 步修正本地留档后重新校验（`VALIDATION_FAILED`） |

## 示例

### 示例 1：成功收敛、创建 Issue 并取得开发信息

输入：

```text
模糊需求：登录成功后展示最近一周的操作记录
需求列表：1. 登录后展示操作记录（必需）；2. 记录用户操作日志（必需）
期望行为与期望结果：1. 登录成功后在首页展示最近一周操作，判定=列表含当日与最近7天数据；
                     2. 记录关键操作日志，判定=日志文件有对应记录
范围边界：不涉及操作明细导出
远端仓库类型：main
```

关键步骤：确认需求 → 创建远端 Issue #12 → 调用 `spec-manager`（开发信息分配）→ 返回开发序号 12、分支 `feat/12-order-cancel`、项目根目录与工作区清单 → 按返回序号写 `docs/dev-docs/12/From-Issue-To-PR-Skill-12-issue.md` → 校验通过。

输出：

```text
gh issue create 成功，issue #12
artifacts: [
  "https://github.com/<owner>/From-Issue-To-PR-Skill/issues/12",
  "docs/dev-docs/12/From-Issue-To-PR-Skill-12-issue.md"
]
开发信息: {
  开发序号: 12,
  分支名: "feat/12-order-cancel",
  项目根目录: "E:/From-Issue-To-PR-Skill",
  工作区: [
    { 名称: "ordering", 类型: "读写", 目录: "src/ordering/" },
    { 名称: "docs", 类型: "只读", 目录: "docs/" }
  ]
}
status: success
errors: []
```

### 示例 2：需求信息不足（失败）

输入：

```text
模糊需求：给系统加个导出功能
需求列表：1. 导出报表（是否必需？）
期望行为与期望结果：（未确认）
```

输出：

```text
status: failed
errors: [
  { code: "INPUT_INCOMPLETE", message: "期望行为与期望结果未确认，已暂停", recoverable: true }
]
处理动作：中断；用 `AskUserQuestion` 逐条向用户提问确认导出场景、期望结果与是否必需后再继续
```

### 示例 3：spec-manager 未返回完整开发信息（失败）

输入：

```text
模糊需求：登录成功后展示最近一周的操作记录（已确认）
远端 Issue：https://github.com/<owner>/From-Issue-To-PR-Skill/issues/12（已创建）
```

输出：

```text
status: failed
errors: [
  { code: "SPEC_MANAGER_FAILED", message: "spec-manager 未返回开发信息（开发序号 / 分支名 / 项目根目录 / 工作区），已暂停", recoverable: true }
]
处理动作：中断并保留 Issue 链接；向用户报告缺失项，待 spec-manager 补齐后再留档
```
