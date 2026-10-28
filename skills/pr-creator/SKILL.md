---
name: pr-creator
description: 提交 PR 阶段：明确待合并分支，fork 仓库先同步上游 main，把待合并分支合入 main 后以草稿 PR 触发 CI，按 CI 报错最小修复至全部通过，再按 GitHub 社区规范提交标题与正文取自 docs 对应序号文件的 PR。当用户要求提交 PR、创建草稿 PR、修复 CI 报错、同步 fork 上游 main，或提到「提交 PR」「创建 PR」「开 PR」「CI 修复」「草稿 PR」「同步上游」等说法时使用；典型输入为 docs/dev-docs/<开发序号>/ 下的开发文档、Issue、测试报告，以及待合并分支与 PR 所在仓库。
compatibility: python3.12+；依赖 git 与 gh CLI（GitHub CLI），执行时 git 与 gh 须可用且 gh auth status 已登录认证，并具备创建 PR、查看 CI 检查的权限。
metadata:
  author: XK_XK
  version: 1.1
---

# pr-creator

把已验证的改动合入 `main`，通过 CI 后按 GitHub 社区规范提交 PR。本 Skill 位于测试与文档同步之后，是整条链路的最后阶段：只负责分支合并、CI 修复与 PR 提交，不改动测试流程与项目文档。

## 适用场景

- 适用：待合并分支已存在、前置阶段已完成，需要判断远端仓库类型、fork 时同步上游 `main`、把待合并分支合入 `main`、以草稿 PR 触发 CI 并修复至全部通过、按 docs 对应序号文件产出 PR 标题与正文；用户提到「提交 PR」「创建 PR」「开 PR」「CI 修复」「草稿 PR」「同步上游」等说法。
- 不适用：代码尚未实现（由 `implementer` 处理）；测试未通过或测试流程需重新设计（由 `test-runner`、`test-planner` 处理）；项目文档未同步（由 `project-doc-sync` 处理）；PR 评审讨论与执行合并（本 Skill 只请求合并，不合并 PR）。

## 必要前提

1. **待合并分支与开发信息已确认**：已明确本次需要合并的分支名，以及对应的开发序号、Issue 编号与 PR 所在仓库名。四者任一无法确定时中断，使用 `AskUserQuestion` 向人类确认后再继续，禁止凭提交记录猜测（`INPUT_MISSING`）。
2. **远端仓库类型可判断**：`git remote -v` 与 `gh repo view --json isFork,parent` 能确认当前远端是主仓库还是 fork 仓库。无法判断时中断，使用 `AskUserQuestion` 向人类确认，不自行执行同步（`REPO_UNKNOWN`）。
3. **工作区干净**：`git status` 显示无未提交改动。存在未提交改动时中断，使用 `AskUserQuestion` 向人类确认处理方式，不强行切换分支或丢弃改动（`WORKTREE_DIRTY`）。
4. **git 与 gh 可用**：`git status` 与 `gh auth status` 均能成功执行，当前仓库存在 `main` 分支。不满足时中断并保留原始报错，提示人类配置 git / gh 后重试（`GIT_UNAVAILABLE`）。

## 执行约束

- 必须：CI 全部通过才算提交完成——PR 先以草稿形式创建以触发 CI，所有 CI 检查实际通过后，才可标记为可评审并请求合并。
- 必须：奥卡姆剃刀——只修改 CI 报错明确指出的错误，不做报错之外的任何改动、重构或「顺手改进」。
- 必须：若修复必然改动代码的执行逻辑，改动后的行为须与 `docs/dev-docs/<开发序号>/<标题>流程图.md` 的描述一致；与流程图冲突时立即停止提交，向人类说明冲突点与原因并等待决定。
- 必须：分支名、仓库类型、PR 的目标仓库、PR 标题与正文来源无法判断或缺失时，先用 `AskUserQuestion` 向人类确认，再继续。
- 禁止：CI 未全部通过时转为可评审、请求合并，或以 `--admin` 等方式强制合并。
- 禁止：跳过、禁用、忽略 CI 检查，或虚构 CI 结果。
- 禁止：自行解决合并冲突或改动合并策略；冲突交由人类决定。
- 禁止：自行修改流程图迁就代码，或为通过 CI 改坏流程。
- 禁止：凭提交记录猜测分支名、仓库类型、开发序号或 Issue 编号。
- 禁止：在 PR 标题与正文中引入 docs 之外的信息，或写入未确认的内容。
- 只能修改：CI 报错指向的代码；合并、同步、推送仅按第 2、3 步的流程执行。
- 只能写入：`docs/dev-docs/<开发序号>/` 下的本地 PR 副本 `<仓库名>-<PR编号>-PR.md`。除远端 PR 与该副本外，不新增文件或目录；`--body-file` 的临时文件须放在仓库之外并在 PR 创建后删除。

**参考文件**：本 Skill 附带下列文件，此处仅**显式声明其存在**，不展开其正文：

- `references/GitHub-CLI.md`（gh 命令参考，含 `gh pr create`、`gh pr checks`、`gh pr ready`）：**仅在创建 / 编辑 PR、执行 git 或 gh 命令时**读取；
- `references/GitHub-submit.md`（Conventional Commits 规范与 Git 安全约束）：**仅在执行 git 提交相关操作时**读取；
- `evals/verify_artifacts.py`（校验 PR 本地副本的位置、命名与内容非空）：**仅在第 7 步校验时**调用。

## 工作流程

### 1. 明确本次需要合并的分支

向人类确认：

- 本次需要合并的分支名；
- 该分支对应的开发序号、Issue 编号与 PR 所在仓库名（用于第 5 步取 PR 标题与正文、第 6 步保存本地 PR 副本）。

无法确定时使用 `AskUserQuestion` 向人类询问，禁止凭提交记录猜测。四项均确认后，进入第 2 步。

### 2. 判断远端仓库类型，fork 时先同步上游 main

用 `git remote -v`、`gh repo view --json isFork,parent` 判断当前远端是主仓库还是 fork 仓库：

- **fork 仓库** → 先同步上游：
  - 上游 remote 不存在时添加：`git remote add upstream <上游仓库地址>`；
  - `git fetch upstream`；
  - 切换到 `main`，合并 `upstream/main`（或执行 `gh repo sync`）；
  - 推送到自己的远端：`git push origin main`。
- **主仓库** → 跳过本步。
- **无法判断** → 先询问人类，不自行执行同步。

同步或推送失败、产生冲突时暂停，向人类报告，不擅自解决。远端类型已确定，且 fork 场景的上游 `main` 已同步并推送后，进入第 3 步。

### 3. 合并待合并分支，并从 main 创建 PR

- 确认工作区干净（`git status`）；有未提交改动时先向人类确认处理方式，不强行切换或丢弃。
- 切换到 `main`，先拉取远端最新 `main`，再合并第 1 步确认的分支；
- 合并产生冲突时暂停，向人类说明冲突文件与冲突内容，由人类决定解决方式，禁止自行取舍；
- 推送合并后的 `main`；
- 以 `main` 作为 head 创建 **草稿 PR**，目标分支为上游主仓库的 `main`（fork 场景为 `upstream:main`）。

若远端即主仓库（非 fork），`main` 无法作为 head 向自身提交 PR：此时先向人类确认改用哪个分支作为 head，确认后再提交，不得自行改换。草稿 PR 创建成功后，进入第 4 步。

### 4. 按 CI 反馈修复，直到全部通过

- 等待并查看 CI 结果：`gh pr checks <PR编号> --watch`；
- 失败时获取实际报错：`gh run view <run-id> --log-failed`，以报错原文为准，不猜测原因；
- 只修改报错指向的代码；修复是否改动执行逻辑，按执行约束「若修复必然改动代码的执行逻辑」一条判断：仅当改动后的行为与对应流程图一致时才继续，否则暂停并告知人类；
- 每次修复提交并推送后，重新等待 CI，直到所有检查通过；不得只验证失败项就宣称通过；
- 全部通过后再标记可评审：`gh pr ready <PR编号>`。

全部 CI 检查通过且 PR 已转为可评审后，进入第 5 步。

### 5. 从 docs 获取 PR 标题与正文

PR 标题与正文一律取自 `docs/` 下对应序号的文件，不自行编造、不引入 docs 之外的信息：

- **标题**：取自 `docs/dev-docs/<开发序号>/<标题>开发文档.md` 文件名中的 `<标题>`；
- **背景**：取自 `docs/dev-docs/<开发序号>/<仓库名>-<issue编号>-issue.md`；
- **改动摘要**：取自开发文档中的数据结构与函数定义，并与实际 diff 对齐；
- **验证方式**：取自 `docs/dev-docs/<开发序号>/test-report/测试报告.md` 中的实际执行命令与结果；
- **影响面**：取自开发文档声明的工作区与本次 diff 涉及的文件；
- **回滚方案**：依据本次 diff 与开发文档的改动范围给出。

docs 中缺失对应信息时，使用 `AskUserQuestion` 向人类询问后再写，不得写成未确认的内容。标题与正文各段齐备后，进入第 6 步。

### 6. 按 GitHub 社区规范编写 PR

PR 标题、正文格式与创建命令遵循 GitHub 社区规范。

**参考文件**：本 Skill 附带 `references/GitHub-CLI.md`（gh 命令参考，含 `gh pr create`、`gh pr checks`、`gh pr ready`）与 `references/GitHub-submit.md`（Conventional Commits 规范与 Git 安全约束），据此选定参数。此处仅**显式声明其存在**；**仅在创建 / 编辑 PR、执行 git 或 gh 命令时**读取这两个文件内容，其余阶段不展开其正文。

用 `gh pr create --draft` 创建 PR 时按上述参考文件选定参数。使用 `--body-file` 时，临时文件放在仓库之外，PR 创建后删除，不在仓库内留下临时副本。

PR 创建成功后，从返回的 PR URL 取得 `<PR编号>`，在 `docs/dev-docs/<开发序号>/` 下保存一份与远端 PR 同标题、同正文的本地副本，命名为 `<仓库名>-<PR编号>-PR.md`（仓库名取 PR 所在仓库名）。本地副本写入后，进入第 7 步。

### 7. 校验

交付前逐项检查以下内容：

- CI 全部检查已实际通过（`gh pr checks <PR编号>` 无失败、无待处理项），PR 已用 `gh pr ready <PR编号>` 转为可评审，且未使用 `--admin` 或跳过、禁用、忽略检查；
- PR 标题取自 `docs/dev-docs/<开发序号>/<标题>开发文档.md` 的文件名，正文各段取自第 5 步声明的 docs 文件与真实 diff，未引入 docs 之外的信息；
- 本地副本 `docs/dev-docs/<开发序号>/<仓库名>-<PR编号>-PR.md` 存在且内容非空，标题与正文与远端 PR 一致；
- 除远端 PR 与本地副本外未新增文件或目录，`--body-file` 临时文件已删除且位于仓库之外。

**校验脚本**：本 Skill 附带 `evals/verify_artifacts.py`（校验 PR 本地副本的位置、命名与内容非空）。此处仅**显式声明其存在**；**仅在本步骤**调用该脚本：

```bash
python evals/verify_artifacts.py docs/dev-docs/<开发序号>
```

脚本以退出码 0 结束且上述检查全部通过后输出产物并结束本阶段；任一项不通过时，回到第 6 步补齐 PR 信息或本地副本后重新校验，禁止以手工检查替代脚本。

## 输入 / 输出

```text
pr_creator(
  待合并分支: string,                       // 必填：本次要合入 main 的分支名，须由人类确认
  开发序号: string,                         // 必填：docs/dev-docs/<开发序号>/ 的目录名，须由人类确认
  Issue编号: string,                        // 必填：用于取 PR 背景，须由人类确认
  PR仓库名: string,                         // 必填：PR 所在仓库名，用于本地副本命名，须由人类确认
  远端仓库类型: "main" | "fork" | null,     // 可选：由第 2 步判断；无法判断时向人类确认
) -> SkillResult

SkillResult {
  status: "success" | "failed",
  artifacts: string[],      // 远端 PR 地址 + 本地 PR 副本路径
  errors: SkillError[]
}

SkillError {
  code: string,             // 与「失败处理」的错误码一一对应
  message: string,
  recoverable: boolean
}
```

输出产物：

1. **远端 PR**：以 `gh pr create --draft` 创建，地址取自命令返回的 PR URL；CI 全部通过后以 `gh pr ready` 转为可评审，本 Skill 只请求合并、不执行合并。
2. **本地 PR 副本** `docs/dev-docs/<开发序号>/<仓库名>-<PR编号>-PR.md`：与远端 PR 同标题、同正文，内容非空。

## 失败处理

| 失败场景 | 判定条件 | 处理动作 |
| --- | --- | --- |
| 分支或仓库信息缺失 | 待合并分支名、开发序号、Issue 编号或 PR 所在仓库名任一无法确定 | 中断，不执行 git / gh 操作；使用 `AskUserQuestion` 向人类确认后再继续，禁止凭提交记录猜测（`INPUT_MISSING`） |
| 远端仓库类型无法判断 | `git remote -v` 与 `gh repo view --json isFork,parent` 无法判定主仓库或 fork，或没有远端仓库 | 中断；使用 `AskUserQuestion` 向人类确认仓库类型后再继续，不自行执行同步（`REPO_UNKNOWN`） |
| 工作区不干净 | `git status` 显示存在未提交改动 | 中断；使用 `AskUserQuestion` 向人类确认处理方式，禁止强行切换分支或丢弃改动（`WORKTREE_DIRTY`） |
| git 或 gh 不可用 | `git status` 或 `gh auth status` 报错，或 `main` 分支不存在 | 中断并保留原始报错；提示人类配置 git / gh 后重试（`GIT_UNAVAILABLE`） |
| 上游同步或推送失败 | `git fetch upstream`、合并 `upstream/main` 或 `git push origin main` 非零退出或产生冲突 | 暂停并保留原始报错；向人类报告，不擅自解决（`SYNC_FAILED`） |
| 待合并分支合入冲突 | 将待合并分支合入 `main` 时产生冲突 | 暂停，报告冲突文件与冲突内容，由人类决定解决方式，禁止自行取舍（`MERGE_CONFLICT`） |
| head 分支无法确定 | 远端即主仓库（非 fork），`main` 无法作为 head 向自身提交 PR | 中断；使用 `AskUserQuestion` 向人类确认改用哪个分支作为 head 后再提交（`HEAD_UNKNOWN`） |
| CI 检查失败 | `gh pr checks <PR编号>` 存在失败的检查 | 按 `gh run view <run-id> --log-failed` 的报错原文最小修复并推送，重新等待 CI，直至全部检查通过（`CI_FAILED`） |
| 修复与流程图冲突 | 修复必然改动执行逻辑，且改动后与 `docs/dev-docs/<开发序号>/<标题>流程图.md` 的描述冲突 | 立即停止提交；向人类说明冲突点与原因并等待决定，禁止修改流程图迁就代码，禁止为通过 CI 改坏流程（`LOGIC_CONFLICT`） |
| PR 标题或正文来源缺失 | `docs/dev-docs/<开发序号>/` 下缺少开发文档、Issue、测试报告等第 5 步所需信息 | 中断；使用 `AskUserQuestion` 向人类询问后再写，不得写成未确认的内容（`DOCS_MISSING`） |
| gh 或 git 命令失败 | `gh pr create`、`gh pr ready` 等命令非零退出，或网络、权限报错 | 中断并保留原始报错；向人类报告后由人类决定，禁止伪造 CI 结果或跳过失败（`COMMAND_FAILED`） |
| 校验脚本无法执行 | Python 未安装、脚本路径错误或权限不足 | 中断并保留原始报错；提示人类安装 Python 或检查路径后重试，禁止以手工检查替代脚本（`SCRIPT_FAILED`） |
| 产物校验未通过 | 「7. 校验」中任一项不满足，或 `verify_artifacts.py` 以退出码 1 结束 | 本阶段不得收尾；回到第 6 步补齐 PR 信息或本地副本后重新校验（`VALIDATION_FAILED`） |

## 示例

### 示例 1：fork 仓库提交 PR 并通过 CI（成功）

输入：

```text
待合并分支：feat/001-order
开发序号：001
Issue编号：12
PR仓库名：From-Issue-To-PR-Skill
远端仓库类型：fork
```

关键步骤：`gh repo view --json isFork,parent` 判定为 fork → 添加 upstream 并 `git fetch upstream`，合并 `upstream/main` 后 `git push origin main` → 将 `feat/001-order` 合入 `main` 并推送 → `gh pr create --draft` 指定 head 为 `main`、目标为 `upstream:main`，得到 PR #45 → CI 报导入顺序错误，按报错最小修复后推送，`gh pr checks 45 --watch` 全部通过 → `gh pr ready 45` → 标题取自 `订单系统开发文档.md`，正文取自 Issue、开发文档与 `test-report/测试报告.md` → 写入本地副本 → `python evals/verify_artifacts.py docs/dev-docs/001` 退出码 0。

输出：

```text
status: success
artifacts: [
  "https://github.com/<owner>/<repo>/pull/45",
  "docs/dev-docs/001/From-Issue-To-PR-Skill-45-PR.md"
]
errors: []
```

### 示例 2：主仓库场景确认 head 分支（成功）

输入：

```text
待合并分支：feat/001-order
开发序号：001
Issue编号：12
PR仓库名：order-service
远端仓库类型：main
```

关键步骤：判定非 fork，跳过上游同步 → 将 `feat/001-order` 合入 `main` 并推送 → `main` 无法作为 head 向自身提交 PR，使用 `AskUserQuestion` 请人类确认改用 `feat/001-order` 作为 head → 草稿 PR 创建成功 → CI 全部通过后 `gh pr ready` → 正文取自 docs → 写入本地副本 → 校验脚本退出码 0。

输出：

```text
status: success
artifacts: [
  "https://github.com/<owner>/order-service/pull/46",
  "docs/dev-docs/001/order-service-46-PR.md"
]
errors: []
```

### 示例 3：修复与流程图冲突（失败）

输入：

```text
待合并分支：feat/001-order
开发序号：001
Issue编号：12
PR仓库名：order-service
远端仓库类型：fork
```

关键步骤：CI 失败指向订单取消分支 → 核对后确认修复须改变状态判定逻辑，且改动后与 `docs/dev-docs/001/订单系统流程图.md` 的「已支付 → 已取消」流转冲突 → 停止提交，未修改流程图，未执行 `gh pr ready`。

输出：

```text
status: failed
errors: [
  { code: "LOGIC_CONFLICT", message: "修复需改变取消分支的执行逻辑，与 docs/dev-docs/001/订单系统流程图.md 冲突，已暂停", recoverable: true }
]
处理动作：中断；向人类说明冲突点与原因，等待人类决定后再继续
```
