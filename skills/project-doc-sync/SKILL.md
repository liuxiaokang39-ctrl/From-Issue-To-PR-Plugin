---
name: project-doc-sync
description: 项目文档同步阶段（本版本仅支持 Rust）：测试通过后，以 rustdoc JSON 为可信底座、syn AST 补全缺失信息，按固定 Rustdoc Markdown 格式更新公有接口的源码 `///` 文档，并按模块生成 `docs/data-struct-and-interface/<模块名>/` 下的接口与数据结构文档，给出未确认字段清单，不臆造任何事实。当用户要求同步项目文档、更新源码 `///` 注释、生成或更新模块接口与数据结构文档、校验文档覆盖率，或提到「文档同步」「项目文档」「接口文档」「数据结构文档」「未确认字段清单」等说法时使用。
compatibility: python3.12+；Rust nightly 工具链（rustup）、rust-script（依赖 syn、quote、proc-macro2、serde、serde_json）、rustdoc-json-to-markdown 或 rustdoc-llms、cargo，以及可执行 bash 脚本的 shell（Git Bash 或 WSL）。
metadata:
  author: XK_XK
  version: 1.1
---

# project-doc-sync

把测试通过后的真实代码同步回「项目文档」，使项目文档始终描述项目当前状态。本 Skill 位于 `test-runner` 之后、`pr-creator` 之前，只产出项目文档（源码 `///` 与模块文档），不产出开发文档；本版本只处理 Rust 项目，其他语言暂不支持。

## 适用场景

- 适用：Rust 项目测试通过后，需要按当前代码更新公有接口的源码 `///` 文档、按模块生成或更新 `docs/data-struct-and-interface/<模块名>/` 下的 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md`，并校验文档覆盖率；用户提到「文档同步」「更新接口文档」「生成数据结构文档」「未确认字段清单」等说法。
- 不适用：非 Rust 项目；代码尚未经 `test-runner` 验证通过（回到 `test-runner`）；开发文档与流程图（由 `dev-doc-writer` 负责）；PR 提交（由 `pr-creator` 负责）；只需浏览 API 而不写文档。

## 必要前提

1. **待同步代码已通过测试**：`docs/dev-docs/<开发序号>/test-report/测试报告.md` 存在且记录全部场景通过。不满足时中断，回到 `test-runner` 阶段（`NOT_VERIFIED`）。
2. **待同步范围可确定**：crate 名、`Cargo.toml` 路径、源码根（默认 `src`）与 crate 根文件（默认 `src/lib.rs`）可判定，且与 `Cargo.toml` 一致。无法确定时中断，使用 `AskUserQuestion` 向人类确认后再执行（`PARAM_UNKNOWN`）。
3. **工具链与依赖可用**：`rustup` 与 nightly 工具链、`rust-script`、Python 3.12+、`rustdoc-json-to-markdown` 或 `rustdoc-llms`、`bash` 均已安装且可执行。缺失时先自行安装补齐并重试原步骤；确实无法安装时中断该项，说明缺失项、安装命令与受影响的步骤（`RESOURCE_UNAVAILABLE`）。
4. **工作区可读写**：待同步源码文件与 `docs/data-struct-and-interface/` 可写，`target/rust-fn-doc/` 可创建。不可写时中断并提示人类检查目录与权限（`WRITE_FAILED`）。
5. **开发序号已登记**：`<开发序号>` 取自 `docs/dev-docs/<开发序号>/开发上下文.md` 的登记值，且与测试报告所在目录一致。登记文件缺失或不一致时中断，回到 `spec-manager` 补齐，不自行编号或向人类另行确认序号（`CONTEXT_MISSING`）。
6. **crate 可构建**：目标 crate 在其 `Cargo.toml` 下可编译（rustdoc JSON 生成依赖构建成功）。构建失败时中断本阶段并告知人类（`EXTRACT_FAILED`）。

## 执行约束

**文档边界**：本项目存在两类文档，不可混用；本 Skill 只负责项目文档。

| 文档类型 | 定位 | 生命周期 | 典型位置 |
| --- | --- | --- | --- |
| 项目文档 | 描述项目**当前最新状态** | 长期维护，随代码演进持续更新 | `README.md`、`docs/` 下的常驻说明、`docs/data-struct-and-interface/<模块名>/`、源码 `///` 文档注释 |
| 开发文档 | 指导**某一次开发**的设计与实现 | 有明确时效性，是本次开发的迁移文档 | `docs/dev-docs/` |

**载体分工**：

| 载体 | 内容范围 | 更新范围 |
| --- | --- | --- |
| 源码 `///` | 公有接口的对外契约：职责、参数、返回值、错误、示例 | **只更新公有接口**；私有函数、数据结构的注释一律不新增、不修改 |
| `docs/data-struct-and-interface/<模块名>/` 下的 4 个文件 | `公有接口.md`（公有接口）、`公有函数.md`（公有函数）、`私有函数.md`（私有函数）、`数据结构.md`（结构体、枚举、联合体、类型别名等）；每条记录标注定义位置 | 每次同步按当前代码整体生成 |

- 必须：只同步经 `test-runner` 测试通过的代码；未验证的实现不回写项目文档。
- 必须：公有接口的函数签名、可见性、参数与返回值类型、doc 注释只以 rustdoc JSON 为准；AST 只用于补全 rustdoc 无法表达的事实（函数体结构、错误分支、调用关系、私有函数与数据结构）。
- 必须：LLM 只做合成，只负责组织语言与排版，不产生事实；参数含义、错误码、返回值语义、示例行为必须能在 rustdoc JSON 或 AST 结果中找到依据。
- 必须：`<模块名>` 取 Rust 模块路径去掉 crate 根后的层级：`crate::foo::bar` 写入 `docs/data-struct-and-interface/foo/bar/`，crate 根模块写入 `docs/data-struct-and-interface/crate/`；目录内固定 4 个文件。
- 必须：定义位置统一写成 `文件路径:行号`（如 `src/foo.rs:42`），取自 rustdoc JSON 的 span 或 AST 的 `file` / `line`。
- 必须：模块文档只记录事实（签名、类型、可见性、字段、定义位置、既有 doc 摘要），无法证实的说明留「—」；模块文档必须随代码提交维护，`target/` 下的中间产物不提交。
- 必须：以代码为准，项目文档与真实实现一致；不得沿用过期描述，也不得凭开发文档推断现状。
- 必须：奥卡姆剃刀——只更新与本次改动相关的过期内容，不做无关重写。
- 必须：源码 `///` 固定为 Rustdoc Markdown，章节依次为 `///`、`# Arguments`、`# Returns`、`# Errors`、`# Examples`；模块文档固定为 `assets/module_interface_doc.md` 定义的 Markdown 表格格式。
- 必须：无法从 rustdoc JSON 或 AST 证实的内容一律登记到未确认字段清单，字段为：函数 | 字段 | 原因 | 需人类确认的内容 | 位置。典型来源包括参数含义缺失、返回值语义未说明、返回 `Result` 但无 `# Errors`、`# Examples` 缺失或无法验证、rustdoc JSON 与 AST 不一致、类型渲染失败（复杂泛型、`impl Trait` 等）。清单默认只在汇报中给出，不写入项目文档；人类要求留档时再写入指定位置。
- 禁止：不臆造——不得推断或编造参数含义、错误码、返回值语义、示例运行结果；不得把「未确认」写成确定事实。
- 禁止：修改代码逻辑、签名、可见性、测试，或修改开发文档与流程图。
- 必须：开发规范（`docs/开发规范/`）只读；开发序号、分支名、worktree 路径与开发目录一律取自 `docs/dev-docs/<开发序号>/开发上下文.md`，只按登记值执行。
- 禁止：创建 / 切换 / 重命名开发分支或 worktree，禁止写入开发规范与开发上下文登记文件。
- 禁止：在源码中残留 `<!-- 未确认：... -->` 占位标记；定稿前必须确认或删除该表述。
- 只能修改：公有接口（公有函数、公有 trait 方法）的 `///` 注释，以及受本次改动影响的项目说明（如 `README.md` 中的相关描述）。
- 只能写入：`docs/data-struct-and-interface/<模块名>/` 下的 4 个模块文档与 `target/rust-fn-doc/` 下的中间产物；除上述产物外不新增 API 文档副本或其他文件。

**参考文件**：本 Skill 附带下列文件，此处仅**显式声明其存在**，不展开其正文：

- `scripts/extract_rustdoc_json.sh`（探测 nightly、生成并归档 rustdoc JSON）：**仅在第 1 步与第 5 步**调用；
- `scripts/ast_inspect.rs`（用 syn 提取函数体结构、错误分支、调用关系、源码 doc 与数据结构）：**仅在第 3 步与第 5 步**调用；
- `scripts/generate_fn_docs.py`（合并事实包、生成固定格式骨架与未确认字段清单、按模块生成接口与数据结构文档、执行覆盖率校验）：**仅在第 4、5、6 步**调用；
- `assets/fn_doc.md`（源码 `///` 的固定格式、章节规则与未确认标注约定）：**仅在第 4 步**读取；
- `assets/module_interface_doc.md`（模块接口与数据结构文档的目录规则、固定格式与填写规则）：**仅在第 5 步**读取；
- `evals/verify_doc_coverage.sh`（覆盖率与一致性校验入口，内部调用 `generate_fn_docs.py --verify`）：**仅在第 6 步**调用。

## 工作流程

### 1. 获取可信底座：rustdoc JSON

先确认待同步的 crate、`Cargo.toml` 与测试报告，再生成 rustdoc JSON。

- 运行 `bash scripts/extract_rustdoc_json.sh -p <crate名> --manifest-path <Cargo.toml路径> -o target/rust-fn-doc`；
- 产物：`target/rust-fn-doc/<crate名>.json`（即 rustdoc JSON）；
- 记录 JSON 的 `format_version`；rustdoc JSON 格式随 nightly 变动，更换工具链后必须重新生成，不得混用不同版本的 JSON。

JSON 生成成功且 `format_version` 已记录后，进入第 2 步。依赖缺失时先安装补齐并重试（`RESOURCE_UNAVAILABLE`）；补齐后仍因编译错误或目标 crate 不可构建而失败时中断并告知人类（`EXTRACT_FAILED`），不得改用 AST 签名冒充可信底座。

### 2. 生成可读骨架

用 `rustdoc-json-to-markdown` 或 `rustdoc-llms` 把 JSON 转成可读骨架，便于快速浏览 API 全貌：

```bash
rustdoc-json-to-markdown target/rust-fn-doc/<crate名>.json -o target/rust-fn-doc/skeleton-from-rustdoc.md
```

- 这两个工具为必需外部依赖，尚未安装时先安装（如 `cargo install`）再执行，不得跳过本步骤；
- 骨架只用于阅读，**不是事实来源**：骨架与 JSON 不一致时，一律以 rustdoc JSON 为准。

骨架生成后，进入第 3 步。

### 3. AST 补全：syn 解析源码

用 syn 解析源码，补全 rustdoc JSON 拿不到的事实：

```bash
rust-script scripts/ast_inspect.rs --src src --crate-root src/lib.rs -o target/rust-fn-doc/ast.json
```

- 提取内容：函数签名（token 形式）、函数体分支（`if` / `match`）、错误分支（`?`、`Err(...)`、`return Err(...)`）、panic 类调用（`panic!`、`unwrap`、`expect`、断言宏等）、调用关系、源码中的原始 doc 行，以及数据结构（结构体、枚举、联合体、类型别名的可见性、字段 / 变体、泛型）；
- AST 结果只补事实：它能说明「源码在这里返回了错误」，不能说明「这个错误意味着什么」；后者必须来自 doc 注释或由人类确认；
- 无 `rust-script` 时先安装，或按 `scripts/ast_inspect.rs` 头部注释的 Cargo 依赖自行构建后运行，产物格式不变。

`target/rust-fn-doc/ast.json` 生成后，进入第 4 步。

### 4. 合成为固定格式的 Rustdoc Markdown

先用脚本把「事实」合并成 LLM 可用的输入，再由 LLM 只做合成：

```bash
python3 scripts/generate_fn_docs.py \
  --rustdoc target/rust-fn-doc/<crate名>.json \
  --ast target/rust-fn-doc/ast.json \
  -o target/rust-fn-doc/facts \
  --no-module-docs
```

- 缺少 `python3`（需 Python 3.12+）时先安装解释器再重跑本步骤，不得跳过合并直接由 LLM 凭印象生成文档；
- 本步骤只产出中间事实包，不写模块文档；模块文档在源码 `///` 定稿后的第 5 步统一生成，避免写入过期内容。

脚本产出：

| 文件 | 用途 |
| --- | --- |
| `facts.md` | 逐函数的事实包：签名、可见性、参数类型、返回值、doc 原文、错误分支、调用关系 |
| `skeleton.md` | 固定格式的 `///` 骨架，缺失事实处预置 `<!-- 未确认：... -->` |
| `未确认字段清单.md` | 无法从输入证实、需要人类确认的字段列表 |

**参考文件**：本 Skill 附带 `assets/fn_doc.md`（固定格式、章节规则与未确认标注约定）。此处仅**显式声明其存在**；**仅在本步骤才读取该文件内容**，其余阶段不展开其正文。

合成规则：

- **允许**：组织语句、合并同义事实、按模板排版、从 doc 原文提炼摘要。
- **禁止**：新增参数含义、错误码、返回值语义、示例输出；改写签名或类型；把「未确认」写成确定事实。
- **章节取舍**：有参数才写 `# Arguments`；返回值非 `()` 才写 `# Returns`；返回 `Result` 才写 `# Errors`；`# Examples` 只在能给出可对应真实签名的示例时写入。
- **未确认处理**：无法证实的内容保留 `<!-- 未确认：... -->` 标记，并登记到清单；定稿前必须消除这些标记（确认或删除该表述），不得把占位标记留在源码中。
- **改动范围**：只修改公有接口（公有函数、公有 trait 方法）的 `///` 注释以及受本次改动影响的项目说明；私有函数与数据结构不写源码注释；不修改代码逻辑、签名、可见性、测试。

源码 `///` 定稿且未确认占位已全部消除后，进入第 5 步。

### 5. 生成模块接口与数据结构文档

源码 `///` 定稿后，先重新生成 rustdoc JSON 与 AST（源码 doc 已变化，旧 JSON 视为过期），再按模块输出接口与数据结构文档：

```bash
bash scripts/extract_rustdoc_json.sh -p <crate名> --manifest-path <Cargo.toml路径> -o target/rust-fn-doc
rust-script scripts/ast_inspect.rs --src src --crate-root src/lib.rs -o target/rust-fn-doc/ast.json
python3 scripts/generate_fn_docs.py \
  --rustdoc target/rust-fn-doc/<crate名>.json \
  --ast target/rust-fn-doc/ast.json \
  --docs-root docs/data-struct-and-interface
```

- 产物：`docs/data-struct-and-interface/<模块名>/` 下固定 4 个文件，分别收录：
  - `公有接口.md`：公有 trait 及其方法；
  - `公有函数.md`：公有函数的签名、入参、返回值；
  - `私有函数.md`：私有函数（含 `pub(crate)` 等非公有函数，以及未进入公有 API 的 `pub` 函数）的签名、入参、返回值；
  - `数据结构.md`：结构体、枚举、联合体、类型别名等，含字段 / 变体与可见性。
- 每条记录必须标注定义位置（`文件路径:行号`）：公有接口与公有函数取自 rustdoc JSON 的 span，私有函数与数据结构取自 AST 的 `file` / `line`。
- 事实来源：公有接口与公有函数取自 rustdoc JSON（权威），私有函数与数据结构取自 AST；不得据此推断语义，无法证实的说明留「—」并登记到未确认字段清单。
- crate 根模块写入 `crate/`；`crate::foo::bar` 写入 `foo/bar/`，两者都包含上述 4 个文件。
- 源码 `///` 不为私有函数、数据结构补注释；它们只出现在模块文档中。

**参考文件**：本 Skill 附带 `assets/module_interface_doc.md`（目录规则、固定格式与填写规则）。此处仅**显式声明其存在**；**仅在本步骤读取该模板正文**，其余阶段不展开其内容。

4 个文件全部生成且每条记录都带定义位置后，进入第 6 步。

### 6. 校验

交付前逐项检查以下内容：

- 每个公有函数都有非空文档摘要；
- 有参数时存在 `# Arguments`，且每个参数都被说明；
- 返回值非 `()` 时存在 `# Returns`；
- 返回 `Result` 时存在 `# Errors`；
- 源码 doc 与 rustdoc JSON 的 `docs` 一致（不一致说明 JSON 已过期，必须回到第 1 / 5 步重新生成）；
- 源码中不残留「未确认」占位标记；
- 每个模块目录都存在且固定包含 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md`，并分别覆盖该模块的公有接口、公有函数、私有函数与数据结构；每条记录都带定义位置；
- `# Examples` 缺失按警告提示，不计为失败。

**校验脚本**：本 Skill 附带 `evals/verify_doc_coverage.sh`（覆盖率与一致性校验入口，内部调用 `generate_fn_docs.py --verify`）。此处仅**显式声明其存在**；**仅在本步骤**调用：

```bash
bash evals/verify_doc_coverage.sh \
  --rustdoc target/rust-fn-doc/<crate名>.json \
  --ast target/rust-fn-doc/ast.json \
  --docs-root docs/data-struct-and-interface
```

脚本以退出码 0 结束且上述检查全部通过后，进入第 7 步；任一项失败必须回到对应步骤修复后重跑，不得跳过，禁止以手工检查替代脚本。必要时补充执行 `cargo test --doc` 与 `cargo doc --no-deps` 验证示例与文档可构建。

### 7. 汇报

汇报中必须包含：

1. 修改的文件与位置，以及新增 / 更新的模块文档路径；
2. 覆盖率校验结论；
3. **未确认字段清单**（表格：函数 | 字段 | 原因 | 需人类确认的内容 | 位置）；
4. 依赖补齐情况；若因依赖确实无法安装而阻塞，说明缺失项、安装命令与受影响的步骤。

清单默认只在回复中给出，不写入项目文档；人类要求留档时再写入指定位置。汇报完成后本阶段结束。

## 输入 / 输出

```text
project_doc_sync(
  crate名: string,                 // 必填：待同步的 crate 名，须与 Cargo.toml 中的包名一致
  开发序号: string,                // 必填：取自 docs/dev-docs/<开发序号>/开发上下文.md 的登记值，用于确认测试已通过
  manifest路径: string,            // 必填：Cargo.toml 路径，工作区多包时必须显式指定
  源码根: string,                  // 可选：默认 src
  crate根文件: string,             // 可选：默认 src/lib.rs
  模块名: string[] | null,         // 可选：仅同步指定模块；缺省同步全部模块
) -> SkillResult

SkillResult {
  status: "success" | "partial" | "failed",
  artifacts: string[],             // 源码 /// 所在文件与模块文档路径
  errors: SkillError[]
}

SkillError {
  code: string,                    // 与「失败处理」的错误码一一对应
  message: string,
  recoverable: boolean
}
```

输出产物：

1. 就地更新的源码 `///` 文档注释：仅公有接口，不新建 API 文档副本；
2. `docs/data-struct-and-interface/<模块名>/` 下的 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md`：按分类保存公有接口、公有函数、私有函数的出入参与数据结构信息，每条记录标注定义位置（提交到项目）；
3. `target/rust-fn-doc/` 下的 `<crate名>.json`、`ast.json`、`skeleton-from-rustdoc.md`、`facts.md`、`skeleton.md`、`未确认字段清单.md`：工作区临时产物，不提交；
4. 未确认字段清单：默认在汇报中给出，人类要求留档时才写入指定位置。

状态取值：

- `success`：全部校验项通过且无未确认字段；
- `partial`：校验通过但仍存在待人类确认的未确认字段，或依赖经补齐后才完成；
- `failed`：任一失败场景导致中断，未完成同步。

## 失败处理

| 失败场景 | 判定条件 | 处理动作 |
| --- | --- | --- |
| 待同步代码未通过测试 | `test-report/测试报告.md` 缺失，或记录中存在失败 / 未执行场景 | 中断，不同步；回到 `test-runner` 阶段（`NOT_VERIFIED`） |
| 待同步范围无法确定 | crate 名、`Cargo.toml` 路径、源码根或 crate 根文件无法判定，或与 `Cargo.toml` 不一致 | 中断；使用 `AskUserQuestion` 向人类确认后再执行（`PARAM_UNKNOWN`） |
| 依赖缺失 | `rustup`、nightly、`rust-script`、Python 3.12+、`rustdoc-json-to-markdown` / `rustdoc-llms` 或 `bash` 不可用 | 先安装补齐并重试原步骤；安装失败时中断该项，保留原始报错并给出安装命令与受影响步骤（`RESOURCE_UNAVAILABLE`） |
| rustdoc JSON 生成失败 | 脚本非零退出，且报错为编译错误或目标 crate 不可构建 | 中断本阶段并告知人类；不得改用 AST 签名冒充可信底座（`EXTRACT_FAILED`） |
| rustdoc JSON 已过期 | 源码 doc 与 JSON 的 `docs` 不一致，或更换 nightly 工具链后未重新生成 | 停止合成；回到第 1 / 5 步重新生成 JSON 与 AST（`STALE_JSON`） |
| 开发上下文登记文件缺失 | `docs/dev-docs/<开发序号>/开发上下文.md` 不存在，或登记的开发序号与测试报告所在目录不一致 | 中断；回到 `spec-manager` 补齐登记文件后再执行（`CONTEXT_MISSING`） |
| 事实来源冲突 | 骨架与 JSON 不一致，或 rustdoc JSON 与 AST 的签名 / doc 不一致 | 以 rustdoc JSON 为准并重新提取；无法消解时中断并登记未确认字段（`FACT_CONFLICT`） |
| 存在无法证实的内容 | 事实包或模块文档出现「未确认」占位，或某字段无任何依据 | 登记到未确认字段清单；定稿前必须确认或删除该表述，不得把占位留在源码（`UNCONFIRMED_FACT`） |
| 写入失败 | 源码文件、`docs/data-struct-and-interface/` 或 `target/rust-fn-doc/` 无法写入 | 中断并保留原始报错；提示人类检查目录与权限后重试（`WRITE_FAILED`） |
| 校验脚本无法执行 | 脚本非零退出且报错不属于上述业务错误（Python 未安装、路径错误、权限不足） | 中断并保留原始报错；修复环境后重试，禁止以手工检查替代脚本（`SCRIPT_FAILED`） |
| 校验未通过 | 「6. 校验」中任一项不满足，或校验脚本以非零退出码结束 | 文档不得交付；回到对应步骤修复后重跑校验（`VALIDATION_FAILED`） |

## 示例

### 示例 1：同步通过（成功）

输入：

```text
crate名：orders
开发序号：001
manifest路径：Cargo.toml
源码根：src
crate根文件：src/lib.rs
模块名：null
```

关键步骤：确认 `docs/dev-docs/001/test-report/测试报告.md` 全部场景通过 → 生成 `target/rust-fn-doc/orders.json` 并记录 `format_version` → 生成可读骨架 → 运行 `scripts/ast_inspect.rs` 得到 `ast.json` → 合并事实包，按 `assets/fn_doc.md` 定稿公有接口 `///` 且无未确认占位 → 重新生成 JSON 与 AST，产出 `docs/data-struct-and-interface/service/` 下 4 个文件（每条带定义位置）→ 校验脚本退出码 0 → 汇报。

输出：

```text
status: success
artifacts: [
  "src/service.rs",
  "docs/data-struct-and-interface/service/公有接口.md",
  "docs/data-struct-and-interface/service/公有函数.md",
  "docs/data-struct-and-interface/service/私有函数.md",
  "docs/data-struct-and-interface/service/数据结构.md"
]
errors: []
```

### 示例 2：存在未确认字段（部分成功）

输入：

```text
crate名：payments
开发序号：002
manifest路径：Cargo.toml
源码根：src
crate根文件：src/lib.rs
模块名：null
```

关键步骤：公有函数 `refund` 返回 `Result`，源码无 `# Errors`，AST 仅能定位错误分支位置 → 依人类确认补写 `# Errors` 并删除 `<!-- 未确认：... -->` 占位 → 生成模块文档 → 校验脚本退出码 0；`refund` 的 `reason: &str` 参数含义仍无依据，作为未确认字段列入汇报清单。

输出：

```text
status: partial
artifacts: [
  "src/refund.rs",
  "docs/data-struct-and-interface/refund/公有函数.md",
  "docs/data-struct-and-interface/refund/私有函数.md",
  "docs/data-struct-and-interface/refund/数据结构.md",
  "docs/data-struct-and-interface/refund/公有接口.md"
]
errors: [
  { code: "UNCONFIRMED_FACT", message: "refund 的 reason 参数含义无依据，已列入未确认字段清单", recoverable: true }
]
```

### 示例 3：rustdoc JSON 已过期（失败）

输入：

```text
crate名：billing
开发序号：003
manifest路径：Cargo.toml
源码根：src
crate根文件：src/lib.rs
模块名：null
```

关键步骤：第 6 步校验报告「源码 doc 与 rustdoc JSON 的 `docs` 不一致」→ 判定 JSON 已过期 → 本次不交付，回到第 5 步重新生成 JSON 与 AST 后重跑全流程。

输出：

```text
status: failed
artifacts: []
errors: [
  { code: "STALE_JSON", message: "源码 doc 与 rustdoc JSON 的 docs 不一致，需重新生成 JSON 与 AST", recoverable: true }
]
```
