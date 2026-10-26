---
name: project-doc-sync
description: 项目文档同步阶段（本版本仅支持 Rust）：在测试通过后，以 rustdoc JSON 为可信底座、syn AST 补全缺失信息，按固定 Rustdoc Markdown 格式更新公有接口的源码文档，并按模块额外生成 docs/data-struct-and-interface/<模块名>/ 下的接口与数据结构文档，给出未确认字段清单，不臆造任何事实。
---

# project-doc-sync

把测试通过后的真实代码同步回「项目文档」，使项目文档始终描述项目当前状态。

> 适用范围：本版本只处理 Rust 项目；其他语言暂不支持。Rust 公有接口以源码 `///` 文档注释承载，全量接口与数据结构信息落盘在 `docs/data-struct-and-interface/<模块名>/`，必要时同步 `README.md` 等常驻说明。

## 职责边界

本项目存在两类文档，不可混用：

| 文档类型 | 定位 | 生命周期 | 典型位置 |
| --- | --- | --- | --- |
| 项目文档 | 描述项目**当前最新状态** | 长期维护，随代码演进持续更新 | `README.md`、`docs/` 下的常驻说明、`docs/data-struct-and-interface/<模块名>/`、源码 `///` 文档注释 |
| 开发文档 | 指导**某一次开发**的设计与实现 | 有明确时效性，是本次开发的迁移文档 | `docs/dev-docs/` |

- 本 Skill 只负责项目文档；开发文档及其流程图由 `dev-doc-writer` 负责，不在本 Skill 的同步范围内。

## 源码注释与模块文档的分工

| 载体 | 内容范围 | 更新范围 |
| --- | --- | --- |
| 源码 `///` | 公有接口的对外契约：职责、参数、返回值、错误、示例 | **只更新公有接口**；私有函数、数据结构的注释一律不新增、不修改 |
| `docs/data-struct-and-interface/<模块名>/` 下的 4 个文件 | `公有接口.md`（公有接口）、`公有函数.md`（公有函数）、`私有函数.md`（私有函数）、`数据结构.md`（结构体、枚举、联合体、类型别名等）；每条记录标注定义位置 | 每次同步按当前代码整体生成 |

- `<模块名>` 取 Rust 模块路径去掉 crate 根后的层级：`crate::foo::bar` 写入 `docs/data-struct-and-interface/foo/bar/`，crate 根模块写入 `docs/data-struct-and-interface/crate/`；目录内固定 4 个文件。
- 定义位置统一写成 `文件路径:行号`（如 `src/foo.rs:42`），取自 rustdoc JSON 的 span 或 AST 的 `file` / `line`。
- 模块文档是项目文档的一部分，必须随代码提交维护；`target/` 下的中间产物不提交。
- 模块文档只记录事实（签名、类型、可见性、字段、定义位置、既有 doc 摘要），不推断语义；无法证实的说明留「—」，需要语义解释时登记到未确认字段清单。

## 必要前提

1. **只同步已验证代码**：仅同步经 `test-runner` 测试通过的代码，未验证的实现不回写项目文档。
2. **可信底座唯一**：公有接口的函数签名、可见性、参数与返回值类型、doc 注释只以 rustdoc JSON 为准；AST 只用于补全 rustdoc 无法表达的事实（函数体结构、错误分支、调用关系、私有函数与数据结构）。
3. **LLM 只做合成**：LLM 负责组织语言与排版，不负责产生事实。参数含义、错误码、返回值语义、示例行为必须能在 rustdoc JSON 或 AST 结果中找到依据。
4. **不臆造**：不得推断或编造参数含义、错误码、返回值语义、示例运行结果；无法证实的内容必须标注为未确认。
5. **以代码为准**：项目文档必须与真实实现一致，不得沿用过期描述，也不得凭开发文档推断现状。
6. **奥卡姆剃刀**：只更新与本次改动相关的过期内容，不做无关重写。
7. **格式固定**：源码 `///` 固定为 Rustdoc Markdown，章节依次为 `///`、`# Arguments`、`# Returns`、`# Errors`、`# Examples`；模块文档固定为 `assets/module_interface_doc.md` 定义的 Markdown 表格格式。
8. **双轨输出**：源码 `///` 只更新公有接口的接口信息（职责、参数、返回值、错误、示例）；私有函数与数据结构（结构体、枚举、联合体、类型别名等）不改源码注释，其函数出入参（公有函数、私有函数）与数据结构信息统一写入 `docs/data-struct-and-interface/<模块名>/`，并按类别固定分为 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md` 4 个文件，每条记录标注定义位置（`文件路径:行号`）。
9. **依赖缺失先补齐**：执行本 Skill 的脚本或校验命令时，如果因依赖缺失（Python 解释器、Rust nightly 工具链、`rust-script`、Python 包等）无法运行，先自行安装 / 补齐依赖并重试，补齐后继续原流程；不得因为缺依赖就跳过步骤，也不得改用其他来源替代可信底座。确实无法安装时，才停止并说明缺失项、安装命令与受影响的步骤。

## 三层职责

| 层 | 职责 | 实现方式 |
| --- | --- | --- |
| 1. 结构化提取 | 获取函数签名、参数、返回值、可见性、doc 注释 | rustdoc JSON（`scripts/extract_rustdoc_json.sh`）+ `rustdoc-json-to-markdown` / `rustdoc-llms` 生成可读骨架 |
| 2. AST 补全 | 解析源码，提取函数体结构、错误分支、调用关系、私有函数与数据结构 | `syn` + `quote`（`scripts/ast_inspect.rs`）；必要时改用 `ra_ap_syntax` / `workspacer-syntax` |
| 3. 文档合成 | 生成源码 `///` 与按模块分类的接口 / 数据结构文档 | 公有接口由 LLM 依据 JSON 事实合成；模块文档由 `scripts/generate_fn_docs.py` 依据 JSON + AST 生成 |

## 工作流程

### 1. 获取可信底座：rustdoc JSON

先确认待同步的 crate、`Cargo.toml` 与测试报告，再生成 rustdoc JSON。

**脚本**：本 Skill 附带 `scripts/extract_rustdoc_json.sh`，负责探测工具链、调用 rustdoc 并归档 JSON：

```bash
bash scripts/extract_rustdoc_json.sh -p <crate名> --manifest-path <Cargo.toml路径> -o target/rust-fn-doc
```

- 产物：`target/rust-fn-doc/<crate名>.json`（即 rustdoc JSON）。
- rustdoc JSON 需要 nightly 工具链；脚本会检查 `rustup` 与 `nightly` 是否可用，缺失时报错并给出安装命令。按必要前提 9，先补齐 nightly 依赖并重跑脚本，不得降级改用其他来源。
- 记录 JSON 的 `format_version`。rustdoc JSON 格式随 nightly 变动，更换工具链后必须重新生成，不得混用不同版本的 JSON。
- 依赖补齐后仍生成失败（编译错误、目标 crate 不可构建）时停止本阶段并告知人类；不得改用 AST 签名冒充可信底座。

### 2. 生成可读骨架

必须用 `rustdoc-json-to-markdown` 或 `rustdoc-llms` 把 JSON 转成可读骨架，便于人工快速浏览 API 全貌：

```bash
rustdoc-json-to-markdown target/rust-fn-doc/<crate名>.json -o target/rust-fn-doc/skeleton-from-rustdoc.md
```

- 这两个工具为必需外部依赖。尚未安装时，按必要前提 9 先安装（如 `cargo install`）再执行；不得跳过本步骤。
- 骨架只用于阅读，**不是事实来源**：骨架与 JSON 不一致时，一律以 rustdoc JSON 为准。

### 3. AST 补全：syn 解析源码

用 syn 解析源码，补全 rustdoc JSON 拿不到的事实：

```bash
rust-script scripts/ast_inspect.rs --src src --crate-root src/lib.rs -o target/rust-fn-doc/ast.json
```

- 提取内容：函数签名（token 形式）、函数体分支（`if` / `match`）、错误分支（`?`、`Err(...)`、`return Err(...)`）、panic 类调用（`panic!`、`unwrap`、`expect`、断言宏等）、调用关系、源码中的原始 doc 行，以及数据结构（结构体、枚举、联合体、类型别名的可见性、字段 / 变体、泛型）。
- AST 结果只补事实：它能说明「源码在这里返回了错误」，不能说明「这个错误意味着什么」。后者必须来自 doc 注释或由人类确认。
- 无 `rust-script` 时按必要前提 9 先安装 `rust-script`，或按 `scripts/ast_inspect.rs` 头部注释的 Cargo 依赖自行构建后运行，产物格式不变。

### 4. 合成为固定格式的 Rustdoc Markdown

先用脚本把「事实」合并成 LLM 可用的输入，再由 LLM 只做合成：

```bash
python3 scripts/generate_fn_docs.py \
  --rustdoc target/rust-fn-doc/<crate名>.json \
  --ast target/rust-fn-doc/ast.json \
  -o target/rust-fn-doc/facts \
  --no-module-docs
```

- 缺少 `python3`（需 Python 3.9+）时按必要前提 9 先安装解释器再重跑本步骤，不得跳过合并直接由 LLM 凭印象生成文档。
- 本步骤只产出中间事实包，不写模块文档；模块文档在源码 `///` 定稿后的步骤 5 统一生成，避免写入过期内容。

脚本产出：

| 文件 | 用途 |
| --- | --- |
| `facts.md` | 逐函数的事实包：签名、可见性、参数类型、返回值、doc 原文、错误分支、调用关系 |
| `skeleton.md` | 固定格式的 `///` 骨架，缺失事实处预置 `<!-- 未确认：... -->` |
| `未确认字段清单.md` | 无法从输入证实、需要人类确认的字段列表 |

**参考模板**：本 Skill 附带 `assets/fn_doc.md`（固定格式、章节规则与未确认标注约定）。此处仅**显式声明其存在**；**仅在本步骤才读取该文件内容**，其余阶段不展开其正文。

合成规则：

- **允许**：组织语句、合并同义事实、按模板排版、从 doc 原文提炼摘要。
- **禁止**：新增参数含义、错误码、返回值语义、示例输出；改写签名或类型；把「未确认」写成确定事实。
- **章节取舍**：有参数才写 `# Arguments`；返回值非 `()` 才写 `# Returns`；返回 `Result` 才写 `# Errors`；`# Examples` 只在能给出可对应真实签名的示例时写入。
- **未确认处理**：无法证实的内容保留 `<!-- 未确认：... -->` 标记，并登记到清单。定稿前必须消除这些标记（确认或删除该表述），不得把占位标记留在源码中。
- **改动范围**：只修改公有接口（公有函数、公有 trait 方法）的 `///` 注释以及受本次改动影响的项目说明；私有函数与数据结构不写源码注释；不修改代码逻辑、签名、可见性、测试。

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
- 固定格式见 `assets/module_interface_doc.md`；仅在本步骤读取该模板正文。
- crate 根模块写入 `crate/`；`crate::foo::bar` 写入 `foo/bar/`，两者都包含上述 4 个文件。模块文档必须提交，随代码一起维护。
- 源码 `///` 不为私有函数、数据结构补注释；它们只出现在模块文档中。

### 6. 校验覆盖率与一致性

```bash
bash evals/verify_doc_coverage.sh \
  --rustdoc target/rust-fn-doc/<crate名>.json \
  --ast target/rust-fn-doc/ast.json \
  --docs-root docs/data-struct-and-interface
```

校验项：

- 每个公有函数都有非空文档摘要；
- 有参数时存在 `# Arguments`，且每个参数都被说明；
- 返回值非 `()` 时存在 `# Returns`；
- 返回 `Result` 时存在 `# Errors`；
- 源码 doc 与 rustdoc JSON 的 `docs` 一致（不一致说明 JSON 已过期，必须重新生成）；
- 源码中不残留 `未确认` 占位标记；
- 每个模块目录都存在且固定包含 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md`，并分别覆盖该模块的公有接口、公有函数、私有函数与数据结构；每条记录都带定义位置；
- `# Examples` 缺失按警告提示，不计为失败。

任一项失败必须修复后重跑，不得跳过。必要时补充执行 `cargo test --doc` 与 `cargo doc --no-deps` 验证示例与文档可构建。

### 7. 汇报

汇报中必须包含：

1. 修改的文件与位置，以及新增 / 更新的模块文档路径；
2. 覆盖率校验结论；
3. **未确认字段清单**（表格：函数 | 字段 | 原因 | 需人类确认的内容 | 位置）；
4. 依赖补齐情况；若因依赖确实无法安装而阻塞，说明缺失项、安装命令与受影响的步骤。

清单默认只在回复中给出，不写入项目文档；人类要求留档时再写入指定位置。

## 未确认字段清单

清单只收录「无法从 rustdoc JSON 或 AST 证实」的内容，典型来源：

- 参数含义缺失或 doc 未逐个说明参数；
- 返回值语义未说明；
- 返回 `Result` 但无 `# Errors`，仅能从 AST 看到错误分支位置；
- `# Examples` 缺失，或示例无法验证；
- rustdoc JSON 与 AST 的签名 / doc 不一致（需重新提取）；
- 类型渲染失败（复杂泛型、`impl Trait` 等），只能从 AST 或源码确认。

## 产物

- 就地更新的源码 `///` 文档注释：仅公有接口，不新建 API 文档副本。
- `docs/data-struct-and-interface/<模块名>/` 下的 `公有接口.md`、`公有函数.md`、`私有函数.md`、`数据结构.md`：按分类保存公有接口、公有函数、私有函数的出入参与数据结构信息，每条记录标注定义位置（提交到项目）。
- `target/rust-fn-doc/` 下的中间产物：rustdoc JSON、AST JSON、事实包、骨架、未确认字段清单（均为工作区临时产物，不提交）。

## 脚本与资源

| 路径 | 职责 |
| --- | --- |
| `scripts/extract_rustdoc_json.sh` | 探测 nightly、生成并归档 rustdoc JSON |
| `scripts/ast_inspect.rs` | 用 syn 提取函数体结构、错误分支、调用关系、源码 doc 与数据结构（结构体 / 枚举 / 联合体 / 类型别名） |
| `scripts/generate_fn_docs.py` | 合并事实包、生成固定格式骨架与未确认字段清单、按模块生成接口与数据结构文档、执行覆盖率校验 |
| `assets/fn_doc.md` | 源码 `///` 的 Rustdoc Markdown 固定格式与未确认标注约定 |
| `assets/module_interface_doc.md` | 模块接口与数据结构文档的目录规则、固定格式与填写规则 |
| `evals/verify_doc_coverage.sh` | 覆盖率与一致性校验入口，内部调用 `generate_fn_docs.py --verify` |

## 约束

- 不修改开发文档与流程图（由 `dev-doc-writer` 负责）。
- 不同步未通过测试的代码。
- 优先使用 rustdoc JSON 中的签名与 doc 注释；缺失信息才用 AST 提取结果补充。
- 不允许臆造参数含义、错误码、返回值语义；未确认项一律显式标注，不得写成已确认。
- 源码 `///` 只更新公有接口的接口信息；私有函数与数据结构不改源码注释，只写入模块文档。
- 模块文档必须按模块覆盖公有接口、公有函数、私有函数与数据结构，不得遗漏。
- 模块文档与源码 `///` 冲突时，以 rustdoc JSON / 源码为准并重新生成，不在文档里「适配」。
- 本版本只支持 Rust；其他语言的文档同步不在本 Skill 范围内。
