---
description: 项目文档同步：以 rustdoc JSON 为底座更新公有接口文档并按模块生成接口文档
argument-hint: "[开发序号] [模块名]"
---

调用 `project-doc-sync` Skill 执行本阶段。

- 用户输入：`$ARGUMENTS`（开发序号与模块名；模块缺失时先问用户）
- 前置：代码已通过测试；本 Skill 仅支持 Rust
- 产物：公有接口源码 `///`（`# Arguments`、`# Returns`、`# Errors`、`# Examples`）+ `docs/data-struct-and-interface/<模块名>/` 四类模块文档
- 流程：`scripts/extract_rustdoc_json.sh` → `scripts/ast_inspect.rs` → `scripts/generate_fn_docs.py`
- 收尾校验：`bash skills/project-doc-sync/evals/verify_doc_coverage.sh --rustdoc target/rust-fn-doc/<crate名>.json --ast target/rust-fn-doc/ast.json --docs-root docs/data-struct-and-interface`
- 下一阶段：`/from-issue-to-pr:pr`
