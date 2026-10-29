---
name: test-planner
description: 测试流程编写与资源准备：依据开发文档、需求与真实实现设计单元白盒、集成白盒、真实部署黑盒测试，覆盖工作区全部代码并对公有接口做黑盒验证，产出三份测试流程文档并准备执行所需资源，不执行测试。当用户要求编写测试流程、测试计划或测试方案，设计单元白盒 / 集成白盒 / 真实部署黑盒测试，准备测试资源，或提到「测试流程」「测试计划」「测试方案」「白盒测试设计」「黑盒测试设计」「测试资源准备」等说法时使用；典型输入为 docs/dev-docs/<开发序号>/ 下的 `<title>-dev-doc.md`、`<title>-flowchart.md`、需求 Issue 与 task-list/。
compatibility: python3.12+
metadata:
  author: XK_XK
  version: 1.2
---

# test-planner

按开发文档、需求与真实实现，设计并编写三层测试流程（单元白盒、集成白盒、真实部署黑盒），并准备好执行这些流程所需的资源。本 Skill 只做设计与准备，不执行测试，位于任务拆分之后、测试执行之前。

## 适用场景

- 适用：开发文档、流程图、需求 Issue 与任务清单已定稿，需要设计三层测试流程、生成三份测试流程文档并准备测试资源；用户提到「测试流程」「测试计划」「测试方案」「白盒测试设计」「黑盒测试设计」「测试资源准备」等说法。
- 不适用：开发文档或流程图缺失（回到 `dev-doc-writer` 补齐）；任务清单与执行顺序缺失（回到 `task-planner` 补齐）；测试执行与测试报告（由 `test-runner` 处理）；PR 提交（由 `pr-creator` 处理）。

## 必要前提

1. **开发文档与流程图存在**：`docs/dev-docs/<开发序号>/` 下存在 `<title>-dev-doc.md` 与同目录的 `<title>-flowchart.md`，且内容非空。不满足时中断，回到 `dev-doc-writer` 阶段补齐，不自行脑补测试目标。
2. **需求 Issue 留档存在**：`docs/dev-docs/<开发序号>/` 下存在 `<仓库名>-<issue编号>-issue.md` 且内容非空。不满足时中断，回到 `issue-writer` 阶段补齐。
3. **任务清单与执行顺序存在**：`docs/dev-docs/<开发序号>/task-list/` 下存在 `execution-order.md` 与其中引用的任务文件 `<seq>-<task-title>.md`。不满足时中断，回到 `task-planner` 阶段补齐。
4. **工作区代码可读**：登记文件中的工作区目录存在且可逐文件读取（只读与读写工作区均可读取）。不满足时中断，向人类确认被测工作区范围后再执行。
5. **开发序号可确定**：`<开发序号>` 取自 `docs/dev-docs/<开发序号>/dev-context.md` 的登记值，且与开发文档、流程图、需求 Issue 与 `task-list/` 所在目录一致。登记文件缺失或不一致时中断，回到 `spec-manager` 补齐，不自行编号或向人类另行确认序号。
6. **当前分支为登记分支**：执行前用 `git branch --show-current` 检查当前分支是否为登记的「分支名」；不是时切换到该分支，切换失败则中断并报告（`BRANCH_MISMATCH`）。

## 执行约束

- 必须：覆盖全部代码——单元白盒与集成白盒的场景必须能追溯到工作区的每个文件与函数；确实无法覆盖的代码，须在测试文档中标注原因并交人类确认，不得以「不可达」为由默认跳过。
- 必须：测试与源码隔离——测试代码放在独立的测试目录或测试文件中，不写入生产源码；不为测试在生产源码中添加钩子、测试分支或额外导出。
- 必须：公开性不变——设计过程中不得修改函数 / 方法的公开属性。
- 必须：奥卡姆剃刀——只为真实存在的实现写测试，不引入与真实实现无关的测试机制、mock 框架或抽象层；项目已有测试框架能满足需求时，不引入新框架。
- 必须：真实部署黑盒测试的场景列表、执行步骤、期望结果与所需外部资源先交人类审核，经人类决定后才写入测试文档；未经审核不得定稿。
- 必须：资源逐项实际验证其可获取、可安装、可启动或可连通，不得仅凭文档或经验判断为可用；资源不可用时先用 `AskUserQuestion` 询问人类是否使用替代品，记录原资源、替代资源与原因。
- 禁止：执行任何测试场景，或在测试流程文档中写入执行结果（本阶段只设计、只准备）。
- 禁止：虚构测试场景或期望结果；期望结果必须可执行、可判定。
- 禁止：开发文档、流程图或任务清单缺失时自行脑补测试目标。
- 必须：开发规范（`docs/dev-standards/`）只读；开发序号、分支名、项目根目录与工作区一律取自 `docs/dev-docs/<开发序号>/dev-context.md`，只按登记值执行，执行前在项目根目录内按登记分支名自检并切换。
- 禁止：创建 / 重命名 / 删除开发分支，禁止写入开发规范与开发上下文登记文件；当前分支不是登记分支时，只允许切换到登记分支，切换失败中断。
- 必须：凡需要向人类提问或确认的环节（真实部署黑盒测试场景、替代资源、覆盖例外等），一律使用 `AskUserQuestion`（或同类选项式接口）给出可选方案，禁止只以纯文本开放式提问；人类可通过「Other」补充选项之外的内容。唯一例外为流程启动时由入口输出的「请描述本次开发计划的需求」。
- 只能写入：`docs/dev-docs/<开发序号>/test-process/` 下的三份测试流程文档；除这三份文档外不新增其他文件或目录，也不改动生产源码。

**参考文件**：本 Skill 附带下列文件，此处仅**显式声明其存在**，不展开其正文：

- `references/visibility-attributes.md`（函数公开属性定义）：**仅在识别公有接口时**读取；
- `references/resource-lifecycle-rules.md`（对象销毁时独占资源释放、借用 / 共享引用与释放顺序）：**仅在设计对象销毁或资源释放相关测试场景时**读取；
- `assets/unit-whitebox-test-process-template.md`、`assets/integration-whitebox-test-process-template.md`、`assets/deployment-blackbox-test-process-template.md`（三份测试流程文档样板草稿）：**仅在生成对应测试流程文档时**读取；
- `evals/verify_artifacts.py`（校验三份测试流程文档的位置、命名与内容非空）：**仅在第 7 步校验时**调用。

## 工作流程

### 1. 读取输入与真实实现

读取以下内容，确定本次对应的开发文档序号：

- 开发文档：`docs/dev-docs/<开发序号>/` 下的 `<title>-dev-doc.md`、同目录 `<title>-flowchart.md`、`task-list/` 下的任务文件与 `task-list/execution-order.md`；
- 需求：`docs/dev-docs/<开发序号>/` 下的 `<仓库名>-<issue编号>-issue.md`；
- 任务报告：`docs/dev-docs/<开发序号>/task-report/`（若存在）；
- 工作区代码：逐文件读取被测目录的真实实现。

以真实实现为准校准测试预期。文档与实现不一致时，在测试文档中标注差异并按真实实现设计测试，不按文档脑补行为。输入齐备且真实实现已读完时，进入第 2 步。

### 2. 识别公有接口

逐个函数确认公开属性：只有「公有接口」需要追加黑盒测试；公有函数做白盒断言；私有函数只声明前置条件，不重复校验。全部函数完成公开属性判定后，进入第 3 步。

**参考文件**：本 Skill 附带 `references/visibility-attributes.md`（函数公开属性定义）。此处仅**显式声明其存在**；**仅在本步骤读取该文件内容**，其余阶段不展开其正文。

### 3. 设计单元白盒与集成白盒测试

- **单元白盒**：以函数为粒度，覆盖工作区全部代码的可达路径，包含正常分支、边界值、错误返回与异常分支；
- **集成白盒**：以函数间调用链与流程图状态流转为粒度，覆盖工作区全部代码，验证模块协作、状态迁移与数据传递；
- **公有接口黑盒**：对每个公有接口，分别在单元层与集成层追加黑盒场景，只依据公开契约（入参、返回值、错误码）设计，不依赖内部实现。

两层场景集合必须能追溯到工作区的每个文件与函数。无法覆盖的代码按「执行约束」标注原因并交人类确认。场景集合完成且覆盖可追溯后，进入第 4 步。

**参考文件**：本 Skill 附带 `references/resource-lifecycle-rules.md`（对象销毁时独占资源释放、借用 / 共享引用与释放顺序的测试场景设计）。此处仅**显式声明其存在**；**仅在设计对象销毁或资源释放相关测试场景时才读取该文件内容**，其余阶段不展开其正文。

### 4. 设计真实部署黑盒测试并交人类审核

依据开发文档、需求、任务报告与真实实现，设计真实部署形态下的端到端场景：真实启动、真实依赖、真实网络 / 数据库 / 外部服务、真实用户操作路径。黑盒设计只描述外部可观察的输入与结果，不依赖内部函数。

先把「场景列表、执行步骤、期望结果、所需外部资源」告知人类，并使用 `AskUserQuestion` 询问是否有补充内容；经人类审核决定后，按人类结论写入测试文档。未经人类审核，真实部署黑盒测试不得定稿，也不得进入后续步骤。

### 5. 生成测试流程文档

- 目录：`docs/dev-docs/<开发序号>/test-process/`；
- 文件固定为三份：`1-unit-whitebox-test-process.md`、`2-integration-whitebox-test-process.md`、`3-real-deployment-blackbox-test-process.md`；
- 每份文档统一按六节组织：1. 测试目标、2. 验收标准、3. 工作区范围、4. 测试步骤与期望结果、5. 测试所需外部资源（如果有）、6. 注意事项（如果有）；
- 在「工作区范围」列出被测文件 / 函数与覆盖它们的场景编号，形成覆盖清单。

三份文档写完后，进入第 6 步。

**参考文件**：本 Skill 附带三份样板草稿 `assets/unit-whitebox-test-process-template.md`、`assets/integration-whitebox-test-process-template.md`、`assets/deployment-blackbox-test-process-template.md`。此处仅**显式声明其存在**；**仅在生成对应测试文档时才读取对应模板**，其余阶段不展开其正文。

### 6. 准备测试资源

汇总三份文档「测试所需外部资源」中的全部项，在执行前逐项准备：

- 测试框架、编译器、运行时与依赖包；
- 环境变量、配置文件、测试数据与测试账号；
- 测试数据库、消息队列、外部服务及访问凭据；
- 真实部署黑盒所需的部署环境、网络与端口；
- 上述各类资源的下载链接（含官方发布页 / 安装包 / 依赖包地址），供无法自动安装或需人类提供时使用。

准备要求：

- 项目已有测试框架能满足需求时使用现有框架，不引入新框架；
- 测试流程指定使用某资源时，必须准备并使用该指定资源本身，不得以其他资源替代；指定资源不可用时按「资源不可用时先询问人类」处理；
- 具备安装 / 配置能力时自行完成；安装失败则提示人类安装，不得跳过；
- 确认当前环境可配置测试执行所需的沙箱环境（含网络、端口与依赖服务）；不具备时先自行配置，仍不可用则提示人类；
- 只准备资源，不编写测试用例代码、不预先记录任何执行结果；
- **必须逐项确认资源可用**：实际验证其可获取、可安装、可启动或可连通，不得仅凭文档或经验判断为可用；
- **资源不可用时先询问人类**：说明不可用的资源项、失败原因与影响范围，并使用 `AskUserQuestion` 询问人类是否需要寻找替代品；未经人类确认，不得自行更换或准备替代资源；
- **人类确认使用替代品后再准备**：记录原资源、替代资源及替代原因；人类拒绝替代时，说明该资源缺失的影响，不得宣称流程可直接执行。

全部资源项完成上述确认后，进入第 7 步。

### 7. 校验

交付前逐项检查以下内容：

- `docs/dev-docs/<开发序号>/test-process/` 下同时存在 `1-unit-whitebox-test-process.md`、`2-integration-whitebox-test-process.md`、`3-real-deployment-blackbox-test-process.md`，命名一致且内容非空；
- 每份文档均按六节组织且无空节，含「工作区范围」覆盖清单，清单中的场景编号与正文场景一一对应；
- 覆盖清单能追溯到工作区的每个文件与函数，未覆盖项已标注原因并经人类确认；
- 真实部署黑盒文档记录的人类审核结论与人类确认一致；
- 「测试所需外部资源」中的全部项已在第 6 步逐项确认可用，替代资源已记录原资源、替代资源与原因；
- 文档中不含任何执行结果。

**校验脚本**：本 Skill 附带 `evals/verify_artifacts.py`（校验三份测试流程文档的位置、命名与内容非空）。此处仅**显式声明其存在**；**仅在本步骤**调用该脚本：

```bash
python evals/verify_artifacts.py docs/dev-docs/<开发序号>
```

全部检查通过后进入第 8 步；任一项不通过时，测试文档不得定稿，回到对应步骤修订后重新校验。

### 8. 汇报设计结果

向人类汇报：三份流程文档各自的场景总数、覆盖的文件与函数数量、公有接口黑盒场景数、真实部署黑盒的人类审核结论、每项资源的准备状态（已就绪 / 待人类提供 / 无法准备及原因），以及确实无法覆盖的代码与原因。未经人类确认资源就绪前，不进入测试执行阶段。

## 输入 / 输出

```text
test_planner(
  开发序号: string,            // 必填：取自 docs/dev-docs/<开发序号>/dev-context.md 的登记值
  开发文档: string,            // 必填：docs/dev-docs/<开发序号>/<title>-dev-doc.md，须已定稿
  流程图: string,              // 必填：同目录 <title>-flowchart.md，提供状态流转作为集成白盒设计依据
  需求Issue留档: string,       // 必填：docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md
  任务清单: string,            // 必填：docs/dev-docs/<开发序号>/task-list/execution-order.md 及其引用的任务文件
  任务报告: string | null,     // 可选：docs/dev-docs/<开发序号>/task-report/；缺省视为无任务报告
  人类补充场景: string[] | null, // 可选：真实部署黑盒人类审核时补充的场景；缺省按 AI 设计稿执行审核
) -> SkillResult

SkillResult {
  status: "success" | "partial" | "failed",
  artifacts: string[],        // 三份测试流程文档路径
  errors: SkillError[]
}

SkillError {
  code: string,               // 与「失败处理」的错误码一一对应
  message: string,
  recoverable: boolean
}
```

输出产物均位于 `docs/dev-docs/<开发序号>/test-process/`：

1. `1-unit-whitebox-test-process.md`：单元白盒与公有接口单元层黑盒场景；
2. `2-integration-whitebox-test-process.md`：集成白盒与公有接口集成层黑盒场景；
3. `3-real-deployment-blackbox-test-process.md`：真实部署形态的端到端黑盒场景，须经人类审核。

## 失败处理

| 失败场景 | 判定条件 | 处理动作 |
| --- | --- | --- |
| 开发文档或流程图缺失 | `docs/dev-docs/<开发序号>/` 下不存在 `<title>-dev-doc.md` 或 `<title>-flowchart.md`，或内容为空 | 中断，不设计测试；回到 `dev-doc-writer` 阶段补齐（`INPUT_INVALID`） |
| 需求 Issue 留档缺失 | `docs/dev-docs/<开发序号>/` 下不存在 `<仓库名>-<issue编号>-issue.md`，或内容为空 | 中断；回到 `issue-writer` 阶段补齐（`INPUT_INVALID`） |
| 任务清单或执行顺序缺失 | `task-list/` 下不存在 `execution-order.md` 或其引用的任务文件 | 中断；回到 `task-planner` 阶段补齐（`INPUT_INVALID`） |
| 开发上下文登记文件缺失 | `docs/dev-docs/<开发序号>/dev-context.md` 不存在，或登记的开发序号与文档、需求、`task-list/` 不一致 | 中断；回到 `spec-manager` 补齐登记文件后再执行（`CONTEXT_MISSING`） |
| 当前分支不是登记分支 | `git branch --show-current` 与登记「分支名」不一致，且切换失败 | 中断并保留原始报错；提示人类检查分支状态后重试，禁止自行创建分支（`BRANCH_MISMATCH`） |
| 存在无法覆盖的代码 | 单元 / 集成白盒场景无法追溯到某个文件或函数 | 中断该部分定稿；标注原因并用 `AskUserQuestion` 交人类确认，未确认前不得声明覆盖完成（`COVERAGE_GAP`） |
| 真实部署黑盒未经人类审核 | 人类尚未对场景列表、执行步骤、期望结果与外部资源给出审核结论 | 中断；测试文档不得定稿，用 `AskUserQuestion` 取得审核结论后再继续（`NOT_REVIEWED`） |
| 资源不可用或安装失败 | 资源无法获取、安装、启动或连通，或安装命令非零退出 | 中断该项；保留原始报错，说明影响范围并用 `AskUserQuestion` 询问人类是否使用替代品，不得自行替换（`RESOURCE_UNAVAILABLE`） |
| 沙箱执行能力不可用 | 当前环境无法配置测试所需的沙箱环境（网络、端口或依赖服务），自行配置后仍不可用 | 中断资源准备；提示人类配置沙箱环境后重试，不得跳过资源确认（`SANDBOX_UNAVAILABLE`） |
| 文件写入失败 | 写入 `docs/dev-docs/<开发序号>/test-process/` 失败（路径非法、权限或磁盘错误） | 中断并保留原始报错；提示人类检查目录后重试（`WRITE_FAILED`） |
| 校验脚本无法执行 | Python 未安装、脚本路径错误或权限不足，且报错不属于上述业务错误 | 中断并保留原始报错；提示人类安装 Python 或检查路径后重试，禁止以手工检查替代脚本（`SCRIPT_FAILED`） |
| 校验未通过 | 「7. 校验」中任一项不满足，或 `verify_artifacts.py` 以退出码 1 结束 | 测试文档不得定稿；按校验结果回到对应步骤修订后重新校验（`VALIDATION_FAILED`） |

## 示例

### 示例 1：完成三层测试设计并准备资源（成功）

输入：

```text
开发序号：001
开发文档：docs/dev-docs/001/order-system-dev-doc.md
流程图：docs/dev-docs/001/order-system-flowchart.md
需求Issue留档：docs/dev-docs/001/From-Issue-To-PR-Skill-12-issue.md
任务清单：docs/dev-docs/001/task-list/execution-order.md
任务报告：docs/dev-docs/001/task-report/
人类补充场景：null
```

关键步骤：逐文件读取 `src/orders/` 真实实现 → 判定 `OrderService.create_order` 为公有接口、`_validate_amount` 为私有函数 → 设计单元白盒 18 个、集成白盒 9 个场景并追加 4 个公有接口黑盒场景 → 真实部署黑盒 5 个场景经人类审核确认 → 按模板生成三份文档 → 安装 pytest 并逐项验证数据库与部署环境可用 → 运行 `python evals/verify_artifacts.py docs/dev-docs/001` 通过 → 向人类汇报。

输出：

```text
status: success
artifacts: [
  "docs/dev-docs/001/test-process/1-unit-whitebox-test-process.md",
  "docs/dev-docs/001/test-process/2-integration-whitebox-test-process.md",
  "docs/dev-docs/001/test-process/3-real-deployment-blackbox-test-process.md"
]
errors: []
```

### 示例 2：真实部署黑盒未获人类审核（失败）

输入：

```text
开发序号：002
开发文档：docs/dev-docs/002/refund-approval-dev-doc.md
流程图：docs/dev-docs/002/refund-approval-flowchart.md
需求Issue留档：docs/dev-docs/002/From-Issue-To-PR-Skill-13-issue.md
任务清单：docs/dev-docs/002/task-list/execution-order.md
任务报告：null
人类补充场景：null
```

关键步骤：完成单元与集成白盒设计后，向人类提交真实部署黑盒的 6 个场景与所需外部资源，人类未给出审核结论。

输出：

```text
status: failed
errors: [
  { code: "NOT_REVIEWED", message: "真实部署黑盒测试未经人类审核，文档不得定稿", recoverable: true }
]
```
