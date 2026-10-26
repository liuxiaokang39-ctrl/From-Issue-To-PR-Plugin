# 模块接口与数据结构文档模板

> 每个模块一个目录，路径固定为 `docs/data-struct-and-interface/<模块名>/`。
> 目录内固定 4 个文件，分别保存公有接口、公有函数、私有函数与数据结构信息。
> 事实来源：公有接口与公有函数取自 rustdoc JSON，私有函数与数据结构取自 syn AST。
> 不推断语义；无法证实的说明留「—」，需要人类解释的内容登记到「未确认字段清单」。

## 目录与命名

| 项 | 规则 |
| --- | --- |
| 根目录 | `docs/data-struct-and-interface/` |
| 模块目录 | Rust 模块路径去掉 crate 根：`crate::foo::bar` → `foo/bar`；crate 根 → `crate` |
| 公有接口文件 | `公有接口.md` |
| 公有函数文件 | `公有函数.md` |
| 私有函数文件 | `私有函数.md` |
| 数据结构文件 | `数据结构.md` |
| 提交 | 模块文档属于项目文档，必须随代码提交 |

## 固定格式

````markdown
# 模块 crate::foo::bar · 公有接口

> 由 project-doc-sync 依据 rustdoc JSON 与 syn AST 生成：公有接口与公有函数取自 rustdoc JSON，
> 私有函数与数据结构取自 AST。不推断语义，无法证实的说明记为「—」。

| 接口 | 定义位置 | 可见性 | 方法 | 说明 |
| --- | --- | --- | --- | --- |
| `crate::foo::Bar` | `src/foo.rs:30` | public | `run`、`stop` | 接口职责摘要 |
````

````markdown
# 模块 crate::foo::bar · 公有函数

> 由 project-doc-sync 依据 rustdoc JSON 与 syn AST 生成：公有接口与公有函数取自 rustdoc JSON，
> 私有函数与数据结构取自 AST。不推断语义，无法证实的说明记为「—」。

| 函数 | 定义位置 | 签名 | 入参 | 返回值 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `crate::foo::run` | `src/foo.rs:10` | `fn run(input: &str) -> Result<u32, Error>` | `input: &str` | `Result<u32, Error>` | 函数职责摘要 |
````

````markdown
# 模块 crate::foo::bar · 私有函数

> 由 project-doc-sync 依据 rustdoc JSON 与 syn AST 生成：公有接口与公有函数取自 rustdoc JSON，
> 私有函数与数据结构取自 AST。不推断语义，无法证实的说明记为「—」。

| 函数 | 定义位置 | 签名 | 入参 | 返回值 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `normalize` | `src/foo.rs:42` | `fn normalize(raw: &str) -> String` | `raw: &str` | `String` | 函数职责摘要 |
````

````markdown
# 模块 crate::foo::bar · 数据结构

> 由 project-doc-sync 依据 rustdoc JSON 与 syn AST 生成：公有接口与公有函数取自 rustdoc JSON，
> 私有函数与数据结构取自 AST。不推断语义，无法证实的说明记为「—」。

| 名称 | 定义位置 | 类型 | 可见性 | 字段 / 变体 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `Config` | `src/foo.rs:1` | struct | public | `pub name: String、timeout: u64` | 结构体职责摘要 |
| `State` | `src/foo.rs:20` | enum | private | `Idle`、`Busy(u32)` | 枚举职责摘要 |
| `Alias` | `src/foo.rs:60` | type_alias | public | `= crate::foo::Config` | 类型别名职责摘要 |
````

## 填写规则

- 每个模块固定 4 个文件，文件名与内容类别一一对应；某类为空时在对应文件写「（无）」，不得省略文件或删除表格标题。
- 每条记录都必须包含「定义位置」列，格式为 `文件路径:行号`（如 `src/foo.rs:42`）；路径无法确定时写「—」。
- 表格只填事实：签名与类型取自 rustdoc JSON（公有）或 AST（私有、数据结构）；说明列只能取既有 doc 摘要，缺失写「—」。
- 入参按签名顺序书写，格式为 `` `name: Type` ``，多项用「、」分隔；返回值为 `()` 时写 `()`。
- 函数名、类型名、路径、定义位置一律用反引号包裹；表格单元格内不得出现未转义的 `|`。
- 「私有函数」收录所有非公有函数，含 `pub(crate)` / `pub(in ...)` 与完全私有的函数，以及未进入公有 API 的 `pub` 函数。
- 数据结构需标注可见性；字段保留字段可见性，枚举记录变体与载荷类型，类型别名记录等号右侧类型。
- 不新增本模板之外的章节；不写内部实现细节、错误码语义或示例（这些属于源码公有接口文档或未确认字段清单）。
- 公有函数的说明与源码 `///` 摘要保持一致；不一致时以源码为准并重新生成模块文档。
