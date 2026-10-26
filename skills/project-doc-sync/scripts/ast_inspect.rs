//! 用 syn 解析 Rust 源码，输出 AST 事实 JSON，供 project-doc-sync 与 rustdoc JSON 合并。
//!
//! 运行方式（二选一）：
//! 1. 已安装 rust-script：
//!    `rust-script ast_inspect.rs --src src --crate-root src/lib.rs -o target/rust-fn-doc/ast.json`
//! 2. 未安装 rust-script：按下方 Cargo 依赖建一个二进制 crate，把本文件作为 `src/main.rs` 后 `cargo run -- ...`。
//!
//! ```cargo
//! [dependencies]
//! syn = { version = "2", features = ["full", "visit"] }
//! quote = "1"
//! proc-macro2 = { version = "1", features = ["span-locations"] }
//! serde = { version = "1", features = ["derive"] }
//! serde_json = "1"
//! ```
//!
//! 输出字段说明：
//! - `signature`：包含可见性的完整签名（token 形式整理，仅作事实参考，权威签名以 rustdoc JSON 为准）；
//! - `branches`：函数体内的 if / match 分支；
//! - `error_returns`：`?`、`return Err(...)`、`Err(...)` 构造等错误分支位置；
//! - `panics`：panic 类宏与 unwrap / expect 调用；
//! - `calls`：函数体内出现的调用；
//! - `doc_lines`：源码中的原始 doc 行，用于与 rustdoc JSON 的 docs 做一致性校验；
//! - `data_structures`：结构体、枚举、联合体与类型别名的可见性、字段/变体、泛型与 doc 行，
//!   供生成 `docs/data-struct-and-interface/<模块名>/` 下的数据结构信息。

use quote::ToTokens;
use serde::Serialize;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use syn::spanned::Spanned;

#[derive(Serialize, Clone, Default)]
struct ParamInfo {
    name: String,
    ty: String,
    is_self: bool,
}

#[derive(Serialize, Clone)]
struct BranchInfo {
    kind: String,
    condition: String,
    line: usize,
}

#[derive(Serialize, Clone)]
struct ErrorInfo {
    kind: String,
    expression: String,
    line: usize,
}

#[derive(Serialize, Clone)]
struct FnInfo {
    name: String,
    module_path: String,
    file: String,
    line: usize,
    column: usize,
    container: Option<String>,
    visibility: String,
    is_async: bool,
    is_unsafe: bool,
    is_const: bool,
    is_test: bool,
    signature: String,
    params: Vec<ParamInfo>,
    return_type: String,
    attrs: Vec<String>,
    doc_lines: Vec<String>,
    has_body: bool,
    branches: Vec<BranchInfo>,
    error_returns: Vec<ErrorInfo>,
    panics: Vec<ErrorInfo>,
    calls: Vec<String>,
}

#[derive(Serialize, Clone, Default)]
struct FieldInfo {
    name: String,
    ty: String,
    visibility: String,
    doc_lines: Vec<String>,
}

#[derive(Serialize, Clone, Default)]
struct VariantInfo {
    name: String,
    kind: String,
    fields: Vec<FieldInfo>,
    doc_lines: Vec<String>,
}

#[derive(Serialize, Clone)]
struct DataStructureInfo {
    name: String,
    kind: String,
    module_path: String,
    file: String,
    line: usize,
    visibility: String,
    generics: String,
    alias: String,
    doc_lines: Vec<String>,
    fields: Vec<FieldInfo>,
    variants: Vec<VariantInfo>,
}

#[derive(Serialize)]
struct Output {
    crate_root: String,
    generated_files: Vec<String>,
    functions: Vec<FnInfo>,
    data_structures: Vec<DataStructureInfo>,
}

fn tidy(text: &str) -> String {
    let collapsed = text.split_whitespace().collect::<Vec<_>>().join(" ");
    collapsed
        .replace("# ", "#")
        .replace(" ,", ",")
        .replace(" ;", ";")
        .replace(" :", ":")
        .replace("( ", "(")
        .replace(" )", ")")
        .replace("[ ", "[")
        .replace(" ]", "]")
        .replace("< ", "<")
        .replace(" >", ">")
        .replace(" ::", "::")
        .replace(":: ", "::")
        .replace("& ", "&")
}

fn truncate(text: &str, max_chars: usize) -> String {
    if text.chars().count() <= max_chars {
        return text.to_string();
    }
    let mut out: String = text.chars().take(max_chars).collect();
    out.push('…');
    out
}

fn normalize_path(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}

fn visibility_text(vis: &syn::Visibility) -> String {
    match vis {
        syn::Visibility::Public(_) => "public".to_string(),
        syn::Visibility::Inherited => "private".to_string(),
        syn::Visibility::Restricted(restricted) => {
            let prefix = if restricted.in_token.is_some() {
                "pub(in "
            } else {
                "pub("
            };
            format!(
                "{}{})",
                prefix,
                tidy(&restricted.path.to_token_stream().to_string())
            )
        }
    }
}

fn visibility_prefix(vis: &syn::Visibility) -> String {
    match vis {
        syn::Visibility::Public(_) => "pub ".to_string(),
        syn::Visibility::Inherited => String::new(),
        syn::Visibility::Restricted(restricted) => {
            let prefix = if restricted.in_token.is_some() {
                "pub(in "
            } else {
                "pub("
            };
            format!(
                "{}{}) ",
                prefix,
                tidy(&restricted.path.to_token_stream().to_string())
            )
        }
    }
}

fn doc_lines(attrs: &[syn::Attribute]) -> Vec<String> {
    let mut lines = Vec::new();
    for attr in attrs {
        if !attr.path().is_ident("doc") {
            continue;
        }
        if let syn::Meta::NameValue(name_value) = &attr.meta {
            if let syn::Expr::Lit(syn::ExprLit {
                lit: syn::Lit::Str(value),
                ..
            }) = &name_value.value
            {
                let raw = value.value();
                let trimmed = raw.strip_prefix(' ').unwrap_or(raw.as_str());
                lines.push(trimmed.to_string());
            }
        }
    }
    lines
}

fn generics_text(generics: &syn::Generics) -> String {
    tidy(&generics.to_token_stream().to_string())
}

fn collect_fields(fields: &syn::Fields) -> Vec<FieldInfo> {
    match fields {
        syn::Fields::Named(named) => collect_named_fields(named),
        syn::Fields::Unnamed(unnamed) => unnamed
            .unnamed
            .iter()
            .enumerate()
            .map(|(index, field)| FieldInfo {
                name: index.to_string(),
                ty: tidy(&field.ty.to_token_stream().to_string()),
                visibility: visibility_text(&field.vis),
                doc_lines: doc_lines(&field.attrs),
            })
            .collect(),
        syn::Fields::Unit => Vec::new(),
    }
}

fn fields_kind(fields: &syn::Fields) -> &'static str {
    match fields {
        syn::Fields::Named(_) => "struct",
        syn::Fields::Unnamed(_) => "tuple",
        syn::Fields::Unit => "unit",
    }
}

fn collect_named_fields(fields: &syn::FieldsNamed) -> Vec<FieldInfo> {
    fields
        .named
        .iter()
        .map(|field| FieldInfo {
            name: field
                .ident
                .as_ref()
                .map(|ident| ident.to_string())
                .unwrap_or_default(),
            ty: tidy(&field.ty.to_token_stream().to_string()),
            visibility: visibility_text(&field.vis),
            doc_lines: doc_lines(&field.attrs),
        })
        .collect()
}

fn other_attrs(attrs: &[syn::Attribute]) -> Vec<String> {
    attrs
        .iter()
        .filter(|attr| !attr.path().is_ident("doc"))
        .map(|attr| tidy(&attr.to_token_stream().to_string()))
        .collect()
}

fn has_test_attr(attrs: &[syn::Attribute]) -> bool {
    attrs.iter().any(|attr| {
        attr.path()
            .segments
            .last()
            .map(|segment| segment.ident == "test")
            .unwrap_or(false)
    })
}

fn is_cfg_test(attrs: &[syn::Attribute]) -> bool {
    attrs.iter().any(|attr| {
        attr.path().is_ident("cfg") && attr.to_token_stream().to_string().contains("test")
    })
}

fn build_signature(sig: &syn::Signature, vis: &syn::Visibility) -> String {
    format!(
        "{}{}",
        visibility_prefix(vis),
        tidy(&sig.to_token_stream().to_string())
    )
}

fn collect_params(sig: &syn::Signature) -> Vec<ParamInfo> {
    let mut params = Vec::new();
    for input in &sig.inputs {
        match input {
            syn::FnArg::Receiver(receiver) => {
                params.push(ParamInfo {
                    name: "self".to_string(),
                    ty: tidy(&receiver.to_token_stream().to_string()),
                    is_self: true,
                });
            }
            syn::FnArg::Typed(pat_type) => {
                params.push(ParamInfo {
                    name: tidy(&pat_type.pat.to_token_stream().to_string()),
                    ty: tidy(&pat_type.ty.to_token_stream().to_string()),
                    is_self: false,
                });
            }
        }
    }
    params
}

fn return_type_text(sig: &syn::Signature) -> String {
    match &sig.output {
        syn::ReturnType::Default => "()".to_string(),
        syn::ReturnType::Type(_, ty) => tidy(&ty.to_token_stream().to_string()),
    }
}

fn is_error_constructor(callee: &str) -> bool {
    callee == "Err" || callee.ends_with("::Err")
}

fn looks_like_error(text: &str) -> bool {
    text.starts_with("Err") || text.starts_with("return Err")
}

struct Collector {
    file: String,
    module_path: String,
    current_container: Option<String>,
    stack: Vec<FnInfo>,
    functions: Vec<FnInfo>,
    data_structures: Vec<DataStructureInfo>,
}

impl Collector {
    fn enter_fn(
        &mut self,
        sig: &syn::Signature,
        vis: &syn::Visibility,
        attrs: &[syn::Attribute],
        has_body: bool,
    ) {
        let start = sig.ident.span().start();
        self.stack.push(FnInfo {
            name: sig.ident.to_string(),
            module_path: self.module_path.clone(),
            file: self.file.clone(),
            line: start.line,
            column: start.column,
            container: self.current_container.clone(),
            visibility: visibility_text(vis),
            is_async: sig.asyncness.is_some(),
            is_unsafe: sig.unsafety.is_some(),
            is_const: sig.constness.is_some(),
            is_test: has_test_attr(attrs),
            signature: build_signature(sig, vis),
            params: collect_params(sig),
            return_type: return_type_text(sig),
            attrs: other_attrs(attrs),
            doc_lines: doc_lines(attrs),
            has_body,
            branches: Vec::new(),
            error_returns: Vec::new(),
            panics: Vec::new(),
            calls: Vec::new(),
        });
    }

    fn exit_fn(&mut self) {
        if let Some(mut info) = self.stack.pop() {
            info.calls.sort();
            info.calls.dedup();
            self.functions.push(info);
        }
    }
}

impl<'ast> syn::visit::Visit<'ast> for Collector {
    fn visit_item_fn(&mut self, node: &'ast syn::ItemFn) {
        if !self.stack.is_empty() || is_cfg_test(&node.attrs) {
            return;
        }
        self.enter_fn(&node.sig, &node.vis, &node.attrs, true);
        syn::visit::visit_item_fn(self, node);
        self.exit_fn();
    }

    fn visit_impl_item_fn(&mut self, node: &'ast syn::ImplItemFn) {
        if !self.stack.is_empty() || is_cfg_test(&node.attrs) {
            return;
        }
        self.enter_fn(&node.sig, &node.vis, &node.attrs, true);
        syn::visit::visit_impl_item_fn(self, node);
        self.exit_fn();
    }

    fn visit_trait_item_fn(&mut self, node: &'ast syn::TraitItemFn) {
        if !self.stack.is_empty() || is_cfg_test(&node.attrs) {
            return;
        }
        self.enter_fn(
            &node.sig,
            &syn::Visibility::Inherited,
            &node.attrs,
            node.default.is_some(),
        );
        if let Some(info) = self.stack.last_mut() {
            info.visibility = "public".to_string();
        }
        syn::visit::visit_trait_item_fn(self, node);
        self.exit_fn();
    }

    fn visit_item_impl(&mut self, node: &'ast syn::ItemImpl) {
        let previous = self
            .current_container
            .replace(tidy(&node.self_ty.to_token_stream().to_string()));
        syn::visit::visit_item_impl(self, node);
        self.current_container = previous;
    }

    fn visit_item_trait(&mut self, node: &'ast syn::ItemTrait) {
        let previous = self.current_container.replace(node.ident.to_string());
        syn::visit::visit_item_trait(self, node);
        self.current_container = previous;
    }

    fn visit_item_struct(&mut self, node: &'ast syn::ItemStruct) {
        if self.stack.is_empty() && !is_cfg_test(&node.attrs) {
            self.data_structures.push(DataStructureInfo {
                name: node.ident.to_string(),
                kind: "struct".to_string(),
                module_path: self.module_path.clone(),
                file: self.file.clone(),
                line: node.ident.span().start().line,
                visibility: visibility_text(&node.vis),
                generics: generics_text(&node.generics),
                alias: String::new(),
                doc_lines: doc_lines(&node.attrs),
                fields: collect_fields(&node.fields),
                variants: Vec::new(),
            });
        }
        syn::visit::visit_item_struct(self, node);
    }

    fn visit_item_enum(&mut self, node: &'ast syn::ItemEnum) {
        if self.stack.is_empty() && !is_cfg_test(&node.attrs) {
            let variants = node
                .variants
                .iter()
                .map(|variant| VariantInfo {
                    name: variant.ident.to_string(),
                    kind: fields_kind(&variant.fields).to_string(),
                    fields: collect_fields(&variant.fields),
                    doc_lines: doc_lines(&variant.attrs),
                })
                .collect();
            self.data_structures.push(DataStructureInfo {
                name: node.ident.to_string(),
                kind: "enum".to_string(),
                module_path: self.module_path.clone(),
                file: self.file.clone(),
                line: node.ident.span().start().line,
                visibility: visibility_text(&node.vis),
                generics: generics_text(&node.generics),
                alias: String::new(),
                doc_lines: doc_lines(&node.attrs),
                fields: Vec::new(),
                variants,
            });
        }
        syn::visit::visit_item_enum(self, node);
    }

    fn visit_item_union(&mut self, node: &'ast syn::ItemUnion) {
        if self.stack.is_empty() && !is_cfg_test(&node.attrs) {
            self.data_structures.push(DataStructureInfo {
                name: node.ident.to_string(),
                kind: "union".to_string(),
                module_path: self.module_path.clone(),
                file: self.file.clone(),
                line: node.ident.span().start().line,
                visibility: visibility_text(&node.vis),
                generics: generics_text(&node.generics),
                alias: String::new(),
                doc_lines: doc_lines(&node.attrs),
                fields: collect_named_fields(&node.fields),
                variants: Vec::new(),
            });
        }
        syn::visit::visit_item_union(self, node);
    }

    fn visit_item_type(&mut self, node: &'ast syn::ItemType) {
        if self.stack.is_empty() && !is_cfg_test(&node.attrs) {
            self.data_structures.push(DataStructureInfo {
                name: node.ident.to_string(),
                kind: "type_alias".to_string(),
                module_path: self.module_path.clone(),
                file: self.file.clone(),
                line: node.ident.span().start().line,
                visibility: visibility_text(&node.vis),
                generics: generics_text(&node.generics),
                alias: tidy(&node.ty.to_token_stream().to_string()),
                doc_lines: doc_lines(&node.attrs),
                fields: Vec::new(),
                variants: Vec::new(),
            });
        }
        syn::visit::visit_item_type(self, node);
    }

    fn visit_item_mod(&mut self, node: &'ast syn::ItemMod) {
        if is_cfg_test(&node.attrs) || node.content.is_none() {
            return;
        }
        let previous = self.module_path.clone();
        self.module_path.push_str("::");
        self.module_path.push_str(&node.ident.to_string());
        syn::visit::visit_item_mod(self, node);
        self.module_path = previous;
    }

    fn visit_expr_if(&mut self, node: &'ast syn::ExprIf) {
        if let Some(info) = self.stack.last_mut() {
            info.branches.push(BranchInfo {
                kind: "if".to_string(),
                condition: truncate(&tidy(&node.cond.to_token_stream().to_string()), 120),
                line: node.span().start().line,
            });
        }
        syn::visit::visit_expr_if(self, node);
    }

    fn visit_expr_match(&mut self, node: &'ast syn::ExprMatch) {
        if let Some(info) = self.stack.last_mut() {
            info.branches.push(BranchInfo {
                kind: "match".to_string(),
                condition: truncate(&tidy(&node.expr.to_token_stream().to_string()), 120),
                line: node.span().start().line,
            });
        }
        syn::visit::visit_expr_match(self, node);
    }

    fn visit_expr_try(&mut self, node: &'ast syn::ExprTry) {
        if let Some(info) = self.stack.last_mut() {
            info.error_returns.push(ErrorInfo {
                kind: "question_mark".to_string(),
                expression: truncate(&tidy(&node.expr.to_token_stream().to_string()), 120),
                line: node.span().start().line,
            });
        }
        syn::visit::visit_expr_try(self, node);
    }

    fn visit_expr_return(&mut self, node: &'ast syn::ExprReturn) {
        if let Some(expr) = &node.expr {
            let text = tidy(&expr.to_token_stream().to_string());
            if looks_like_error(&text) {
                if let Some(info) = self.stack.last_mut() {
                    info.error_returns.push(ErrorInfo {
                        kind: "return_err".to_string(),
                        expression: truncate(&text, 120),
                        line: node.span().start().line,
                    });
                }
            }
        }
        syn::visit::visit_expr_return(self, node);
    }

    fn visit_expr_call(&mut self, node: &'ast syn::ExprCall) {
        let callee = truncate(&tidy(&node.func.to_token_stream().to_string()), 120);
        if let Some(info) = self.stack.last_mut() {
            info.calls.push(callee.clone());
            if is_error_constructor(&callee) {
                info.error_returns.push(ErrorInfo {
                    kind: "err_constructor".to_string(),
                    expression: truncate(&tidy(&node.to_token_stream().to_string()), 160),
                    line: node.span().start().line,
                });
            }
        }
        syn::visit::visit_expr_call(self, node);
    }

    fn visit_expr_method_call(&mut self, node: &'ast syn::ExprMethodCall) {
        let method = node.method.to_string();
        let receiver = tidy(&node.receiver.to_token_stream().to_string());
        if let Some(info) = self.stack.last_mut() {
            info.calls
                .push(truncate(&format!("{}.{}", receiver, method), 120));
            if method == "unwrap" || method == "expect" {
                info.panics.push(ErrorInfo {
                    kind: method.clone(),
                    expression: truncate(&format!("{}.{}", receiver, method), 160),
                    line: node.span().start().line,
                });
            }
        }
        syn::visit::visit_expr_method_call(self, node);
    }

    fn visit_macro(&mut self, node: &'ast syn::Macro) {
        let name = node
            .path
            .segments
            .last()
            .map(|segment| segment.ident.to_string())
            .unwrap_or_default();
        let is_panic_macro = matches!(
            name.as_str(),
            "panic"
                | "unreachable"
                | "todo"
                | "unimplemented"
                | "assert"
                | "assert_eq"
                | "assert_ne"
                | "debug_assert"
                | "debug_assert_eq"
                | "debug_assert_ne"
        );
        if is_panic_macro {
            if let Some(info) = self.stack.last_mut() {
                info.panics.push(ErrorInfo {
                    kind: format!("{}!", name),
                    expression: truncate(&tidy(&node.to_token_stream().to_string()), 160),
                    line: node.span().start().line,
                });
            }
        }
        syn::visit::visit_macro(self, node);
    }
}

fn collect_rs_files(path: &Path, out: &mut Vec<PathBuf>) {
    if path.is_file() {
        let is_rust = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext == "rs")
            .unwrap_or(false);
        if is_rust {
            out.push(path.to_path_buf());
        }
        return;
    }
    if !path.is_dir() {
        return;
    }
    let entries = match fs::read_dir(path) {
        Ok(entries) => entries,
        Err(_) => return,
    };
    let mut children: Vec<PathBuf> = entries
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .collect();
    children.sort();
    for child in children {
        let name = child
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("");
        if name == "target" || name.starts_with('.') {
            continue;
        }
        collect_rs_files(&child, out);
    }
}

fn module_path_for(file: &Path, roots: &[PathBuf]) -> String {
    for root in roots {
        if let Ok(relative) = file.strip_prefix(root) {
            let mut parts: Vec<String> = relative
                .iter()
                .map(|component| component.to_string_lossy().to_string())
                .collect();
            if parts.is_empty() {
                continue;
            }
            let last = parts.pop().unwrap_or_default();
            if last != "lib.rs" && last != "main.rs" && last != "mod.rs" && !last.is_empty() {
                parts.push(last.trim_end_matches(".rs").to_string());
            }
            let mut module_path = String::from("crate");
            for part in parts {
                if part.is_empty() {
                    continue;
                }
                module_path.push_str("::");
                module_path.push_str(&part);
            }
            return module_path;
        }
    }
    let stem = file
        .file_stem()
        .and_then(|stem| stem.to_str())
        .unwrap_or("unknown");
    if stem == "lib" || stem == "main" {
        "crate".to_string()
    } else {
        format!("crate::{}", stem)
    }
}

fn print_usage() {
    eprintln!(
        "用法：rust-script ast_inspect.rs [--src <目录或文件> ...] [--crate-root <文件>] [-o <输出文件>]\n\
         默认 --src src、--crate-root src/lib.rs；未指定 -o 时输出到标准输出。"
    );
}

fn main() {
    let mut sources: Vec<PathBuf> = Vec::new();
    let mut crate_root = String::new();
    let mut output: Option<PathBuf> = None;

    let args: Vec<String> = env::args().skip(1).collect();
    let mut index = 0;
    while index < args.len() {
        match args[index].as_str() {
            "--src" => {
                index += 1;
                if index >= args.len() {
                    eprintln!("--src 缺少取值");
                    std::process::exit(2);
                }
                sources.push(PathBuf::from(&args[index]));
            }
            "--crate-root" => {
                index += 1;
                if index >= args.len() {
                    eprintln!("--crate-root 缺少取值");
                    std::process::exit(2);
                }
                crate_root = args[index].clone();
            }
            "-o" | "--output" => {
                index += 1;
                if index >= args.len() {
                    eprintln!("-o 缺少取值");
                    std::process::exit(2);
                }
                output = Some(PathBuf::from(&args[index]));
            }
            "-h" | "--help" => {
                print_usage();
                return;
            }
            other => {
                eprintln!("未知参数：{}", other);
                print_usage();
                std::process::exit(2);
            }
        }
        index += 1;
    }

    if sources.is_empty() {
        sources.push(PathBuf::from("src"));
    }
    if crate_root.is_empty() {
        crate_root = "src/lib.rs".to_string();
    }
    for source in &sources {
        if !source.exists() {
            eprintln!("找不到源码路径：{}", source.display());
            std::process::exit(2);
        }
    }

    let roots: Vec<PathBuf> = sources
        .iter()
        .map(|source| {
            if source.is_dir() {
                source.clone()
            } else {
                source
                    .parent()
                    .map(|parent| parent.to_path_buf())
                    .unwrap_or_else(|| PathBuf::from("."))
            }
        })
        .collect();

    let mut files: Vec<PathBuf> = Vec::new();
    for source in &sources {
        collect_rs_files(source, &mut files);
    }
    files.sort();
    files.dedup();

    let mut functions: Vec<FnInfo> = Vec::new();
    let mut data_structures: Vec<DataStructureInfo> = Vec::new();
    let mut generated_files: Vec<String> = Vec::new();

    for file in &files {
        let display = normalize_path(file);
        generated_files.push(display.clone());
        let content = match fs::read_to_string(file) {
            Ok(content) => content,
            Err(error) => {
                eprintln!("读取 {} 失败：{}", display, error);
                std::process::exit(1);
            }
        };
        let syntax = match syn::parse_file(&content) {
            Ok(syntax) => syntax,
            Err(error) => {
                eprintln!("解析 {} 失败：{}", display, error);
                std::process::exit(1);
            }
        };
        let module_path = module_path_for(file, &roots);
        let mut collector = Collector {
            file: display,
            module_path,
            current_container: None,
            stack: Vec::new(),
            functions: Vec::new(),
            data_structures: Vec::new(),
        };
        syn::visit::Visit::visit_file(&mut collector, &syntax);
        functions.extend(collector.functions);
        data_structures.extend(collector.data_structures);
    }

    functions.sort_by(|left, right| {
        left.file
            .cmp(&right.file)
            .then(left.line.cmp(&right.line))
            .then(left.name.cmp(&right.name))
    });
    data_structures.sort_by(|left, right| {
        left.file
            .cmp(&right.file)
            .then(left.line.cmp(&right.line))
            .then(left.name.cmp(&right.name))
    });

    let data = Output {
        crate_root,
        generated_files,
        functions,
        data_structures,
    };
    let json = match serde_json::to_string_pretty(&data) {
        Ok(json) => json,
        Err(error) => {
            eprintln!("序列化 AST 事实失败：{}", error);
            std::process::exit(1);
        }
    };

    match output {
        Some(path) => {
            if let Some(parent) = path.parent() {
                if !parent.as_os_str().is_empty() {
                    if let Err(error) = fs::create_dir_all(parent) {
                        eprintln!("创建目录 {} 失败：{}", parent.display(), error);
                        std::process::exit(1);
                    }
                }
            }
            if let Err(error) = fs::write(&path, json) {
                eprintln!("写入 {} 失败：{}", path.display(), error);
                std::process::exit(1);
            }
            eprintln!(
                "AST 事实：{}（{} 个文件，{} 个函数，{} 个数据结构）",
                path.display(),
                data.generated_files.len(),
                data.functions.len(),
                data.data_structures.len()
            );
        }
        None => println!("{}", json),
    }
}
