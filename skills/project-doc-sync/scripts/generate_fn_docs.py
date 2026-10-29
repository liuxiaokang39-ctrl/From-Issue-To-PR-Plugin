#!/usr/bin/env python3
"""合并 rustdoc JSON 与 syn AST 事实，生成函数文档骨架、未确认字段清单，并校验覆盖率。

用法：
    python3 generate_fn_docs.py --rustdoc <rustdoc.json> --ast <ast.json> -o <输出目录> \
        [--docs-root docs/data-struct-and-interface]
    python3 generate_fn_docs.py --verify --rustdoc <rustdoc.json> [--ast <ast.json>] \
        [--docs-root <模块文档根目录>]

非校验模式输出到 -o 目录：facts.md（事实包）、skeleton.md（固定格式骨架）、
unconfirmed-fields.md（无法从输入证实的字段）；同时按模块生成
<docs-root>/<模块名>/ 下的 4 个文件（public-interface.md、public-functions.md、private-functions.md、data-structures.md），
分别收录公有接口、公有函数、私有函数与数据结构，并标注各自定义位置。
校验模式打印覆盖率报告并以非零状态码表示存在缺失章节、残留「未确认」占位、
rustdoc JSON 已过期或模块文档缺失覆盖。

约束：
    - 签名、可见性、参数与返回值类型、doc 注释只取自 rustdoc JSON；
    - AST 只补函数体分支、错误分支、调用关系、私有函数与数据结构；
    - 本脚本不生成语义，参数含义、错误码、返回值语义一律标记为未确认。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

SECTION_RE = re.compile(
    r"^#\s+(Arguments|Returns|Errors|Examples|Panics|Safety)\s*$", re.MULTILINE
)
UNRESOLVED = "<未解析"

MODULE_DOC_FILES = {
    "interfaces": "public-interface.md",
    "public_functions": "public-functions.md",
    "internal_functions": "private-functions.md",
    "data_structures": "data-structures.md",
}
MODULE_DOC_TITLES = {
    "interfaces": "公有接口",
    "public_functions": "公有函数",
    "internal_functions": "私有函数",
    "data_structures": "数据结构",
}


@dataclass
class Param:
    name: str
    ty: str
    is_self: bool = False


@dataclass
class Gap:
    function: str
    field_name: str
    reason: str
    needs: str
    location: str


@dataclass
class FunctionDoc:
    path: str
    name: str
    visibility: str
    file: str
    line: int
    signature: str
    params: list[Param]
    returns: str
    docs: str
    sections: dict[str, str]
    ast: Optional[dict] = None
    owner: Optional[str] = None
    notes: list[str] = field(default_factory=list)


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise SystemExit(f"读取失败：{path}（{exc}）") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON 解析失败：{path}（{exc}）") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"JSON 顶层必须是对象：{path}")
    return data


def normalize_source_path(path: str) -> str:
    cleaned = str(path or "").replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def same_file(left: str, right: str) -> bool:
    first = normalize_source_path(left)
    second = normalize_source_path(right)
    if not first or not second:
        return False
    if first == second:
        return True
    return first.endswith("/" + second) or second.endswith("/" + first)


def normalize_doc(text: str) -> str:
    lines = [line.rstrip() for line in (text or "").replace("\r\n", "\n").splitlines()]
    return "\n".join(lines).strip()


def split_sections(docs: str) -> dict[str, str]:
    text = docs or ""
    matches = list(SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    first_heading = matches[0].start() if matches else len(text)
    sections["summary"] = text[:first_heading].strip()
    for index, match in enumerate(matches):
        name = match.group(1).lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections


def render_type(node: Any) -> tuple[str, bool]:
    """尽力把 rustdoc JSON 的类型节点渲染成 Rust 类型文本。

    返回 (文本, 是否完整解析)。无法解析时文本包含 `<未解析...>`，调用方必须把它
    视为未确认事实，不得据此编造语义。
    """
    if isinstance(node, str):
        return node, True
    if not isinstance(node, dict) or not node:
        return "<未解析类型>", False

    if "primitive" in node:
        value = node["primitive"]
        return (value, True) if isinstance(value, str) else ("<未解析类型>", False)

    if "resolved_path" in node:
        data = node["resolved_path"] or {}
        name = data.get("path") or data.get("name")
        args_text, args_ok = render_args(data.get("args"))
        if not isinstance(name, str) or not name:
            return "<未解析类型>", False
        return f"{name}{args_text}", args_ok

    if "generic" in node:
        value = node["generic"]
        return (value, True) if isinstance(value, str) else ("<未解析类型>", False)

    if "infer" in node:
        return "_", True

    if "borrowed_ref" in node:
        data = node["borrowed_ref"] or {}
        inner, ok = render_type(data.get("type"))
        lifetime = data.get("lifetime")
        mutability = "mut " if data.get("is_mutable") else ""
        prefix = "&"
        if isinstance(lifetime, str) and lifetime:
            prefix += lifetime + " "
        return f"{prefix}{mutability}{inner}", ok

    if "raw_pointer" in node:
        data = node["raw_pointer"] or {}
        inner, ok = render_type(data.get("type"))
        mutability = "mut" if data.get("is_mutable") else "const"
        return f"*{mutability} {inner}", ok

    if "tuple" in node:
        items = node["tuple"] or []
        rendered: list[str] = []
        ok = True
        for item in items:
            text, resolved = render_type(item)
            rendered.append(text)
            ok = ok and resolved
        if not rendered:
            return "()", True
        if len(rendered) == 1:
            return f"({rendered[0]},)", ok
        return f"({', '.join(rendered)})", ok

    if "slice" in node:
        inner, ok = render_type(node["slice"])
        return f"[{inner}]", ok

    if "array" in node:
        data = node["array"] or {}
        inner, ok = render_type(data.get("type"))
        length = data.get("len")
        if isinstance(length, str):
            length_text = length
        elif length is None:
            length_text = "?"
            ok = False
        else:
            length_text = str(length)
            ok = False
        return f"[{inner}; {length_text}]", ok

    if "impl_trait" in node:
        bounds_text, ok = render_bounds(node["impl_trait"] or [])
        return f"impl {bounds_text}", ok

    if "dyn_trait" in node:
        data = node["dyn_trait"] or {}
        bounds_text, ok = render_bounds(data.get("traits") or [])
        lifetime = data.get("lifetime")
        suffix = f" + {lifetime}" if isinstance(lifetime, str) and lifetime else ""
        return f"dyn {bounds_text}{suffix}", ok

    if "function_pointer" in node:
        data = node["function_pointer"] or {}
        inputs: list[str] = []
        ok = True
        for input_type in data.get("inputs") or []:
            text, resolved = render_type(input_type)
            inputs.append(text)
            ok = ok and resolved
        output, output_ok = render_type(data.get("output"))
        ok = ok and output_ok
        return f"fn({', '.join(inputs)}) -> {output}", ok

    if "pat" in node:
        data = node["pat"] or {}
        inner, ok = render_type(data.get("type"))
        return inner, ok

    if "qualified_path" in node:
        data = node["qualified_path"] or {}
        name = data.get("name") or "?"
        return f"{name}<未解析限定路径>", False

    compact = json.dumps(node, ensure_ascii=False, separators=(",", ":"))
    return f"<未解析类型:{compact[:60]}>", False


def render_args(args: Any) -> tuple[str, bool]:
    if args is None:
        return "", True
    if not isinstance(args, dict):
        return "", False
    if "angle_bracketed" in args:
        data = args["angle_bracketed"] or {}
        rendered: list[str] = []
        ok = True
        for arg in data.get("args") or []:
            if not isinstance(arg, dict):
                rendered.append("<未解析参数>")
                ok = False
                continue
            if "type" in arg:
                text, resolved = render_type(arg["type"])
            elif "lifetime" in arg:
                lifetime = arg["lifetime"]
                text = lifetime if isinstance(lifetime, str) else "<未解析生命周期>"
                resolved = isinstance(lifetime, str)
            elif "const" in arg:
                text, resolved = render_const(arg["const"])
            elif "binding" in arg:
                binding = arg["binding"] or {}
                name = binding.get("name") or "?"
                text = f"{name}=<未解析绑定>"
                resolved = False
            else:
                text, resolved = "<未解析参数>", False
            rendered.append(text)
            ok = ok and resolved
        if not rendered:
            return "", ok
        return f"<{', '.join(rendered)}>", ok
    if "parenthesized" in args:
        data = args["parenthesized"] or {}
        rendered = []
        ok = True
        for arg in data.get("inputs") or []:
            text, resolved = render_type(arg)
            rendered.append(text)
            ok = ok and resolved
        return f"({', '.join(rendered)})", ok
    return "", False


def render_const(node: Any) -> tuple[str, bool]:
    if isinstance(node, str):
        return node, True
    if isinstance(node, dict):
        for key in ("value", "expr"):
            value = node.get(key)
            if isinstance(value, str):
                return value, True
    return "<未解析常量>", False


def render_bounds(bounds: Any) -> tuple[str, bool]:
    if not isinstance(bounds, list):
        return "<未解析约束>", False
    rendered: list[str] = []
    ok = True
    for bound in bounds:
        if not isinstance(bound, dict):
            rendered.append("<未解析约束>")
            ok = False
            continue
        if "lifetime" in bound:
            lifetime = bound["lifetime"]
            if isinstance(lifetime, str):
                rendered.append(lifetime)
            else:
                rendered.append("<未解析生命周期>")
                ok = False
            continue
        if "outlives" in bound:
            outlives = bound["outlives"]
            if isinstance(outlives, str):
                rendered.append(outlives)
            else:
                rendered.append("<未解析约束>")
                ok = False
            continue
        if "trait_bound" in bound:
            data = bound["trait_bound"] or {}
        elif "trait" in bound:
            data = bound
        else:
            rendered.append("<未解析约束>")
            ok = False
            continue
        trait = data.get("trait") or {}
        if not isinstance(trait, dict):
            rendered.append("<未解析约束>")
            ok = False
            continue
        path = trait.get("path") or trait.get("name")
        args_text, args_ok = render_args(trait.get("args"))
        generic_params = data.get("generic_params") or []
        prefix = ""
        if generic_params:
            prefix = "for<> "
            ok = False
        if not isinstance(path, str) or not path:
            rendered.append("<未解析约束>")
            ok = False
            continue
        rendered.append(f"{prefix}{path}{args_text}")
        ok = ok and args_ok
    if not rendered:
        return "<未解析约束>", False
    return " + ".join(rendered), ok


def render_generics(generics: Any) -> tuple[str, bool]:
    if not isinstance(generics, dict):
        return "", True
    params = generics.get("params") or []
    if not params:
        return "", True
    rendered: list[str] = []
    ok = True
    for param in params:
        if not isinstance(param, dict):
            rendered.append("<未解析泛型>")
            ok = False
            continue
        if "lifetime" in param:
            data = param["lifetime"] or {}
            name = data.get("name")
            if isinstance(name, str):
                rendered.append(name)
            else:
                rendered.append("<未解析生命周期>")
                ok = False
        elif "type" in param:
            data = param["type"] or {}
            name = data.get("name")
            if not isinstance(name, str) or not name:
                rendered.append("<未解析泛型>")
                ok = False
                continue
            pieces = [name]
            bounds = data.get("bounds") or []
            if bounds:
                bounds_text, bounds_ok = render_bounds(bounds)
                pieces.append(": " + bounds_text)
                ok = ok and bounds_ok
            default = data.get("default")
            if isinstance(default, dict) and default:
                default_text, default_ok = render_type(default)
                pieces.append(" = " + default_text)
                ok = ok and default_ok
            rendered.append("".join(pieces))
        elif "const" in param:
            data = param["const"] or {}
            name = data.get("name") or "?"
            type_text, type_ok = render_type(data.get("type"))
            rendered.append(f"const {name}: {type_text}")
            ok = ok and type_ok
        else:
            rendered.append("<未解析泛型>")
            ok = False
    return f"<{', '.join(rendered)}>", ok


def visibility_text(value: Any) -> str:
    if value == "public":
        return "public"
    if value == "crate":
        return "pub(crate)"
    if value == "default":
        return "private"
    if isinstance(value, dict):
        restricted = value.get("restricted") or {}
        parent = restricted.get("parent")
        if isinstance(parent, str) and parent:
            return f"pub({parent})"
    return str(value)


def is_unit(returns: str) -> bool:
    compact = "".join((returns or "").split())
    return compact in ("", "()")


def is_result(returns: str) -> bool:
    return "Result<" in "".join((returns or "").split())


def parse_params(sig: dict) -> tuple[list[Param], bool]:
    params: list[Param] = []
    ok = True
    for entry in sig.get("inputs") or []:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            raw_name, type_node = entry[0], entry[1]
        elif isinstance(entry, dict):
            raw_name, type_node = entry.get("name"), entry.get("type")
        else:
            ok = False
            continue
        name = str(raw_name) if raw_name is not None else ""
        ty, type_ok = render_type(type_node)
        ok = ok and type_ok
        is_self = name == "self"
        if not name:
            name = f"<未解析参数{len(params) + 1}>"
            ok = False
        params.append(Param(name=name, ty=ty, is_self=is_self))
    return params, ok


def parse_return(sig: dict) -> tuple[str, bool]:
    output = sig.get("output")
    if output is None:
        return "()", True
    text, ok = render_type(output)
    if is_unit(text):
        return "()", ok
    return text, ok


def build_signature(
    name: str, generics_text: str, params: list[Param], returns: str, header: dict
) -> str:
    pieces: list[str] = []
    if header.get("is_const"):
        pieces.append("const")
    if header.get("is_async"):
        pieces.append("async")
    if header.get("is_unsafe"):
        pieces.append("unsafe")
    abi = header.get("abi")
    if isinstance(abi, str) and abi:
        pieces.append(f'extern "{abi}"')
    prefix = (" ".join(pieces) + " ") if pieces else ""
    param_text = ", ".join(f"{param.name}: {param.ty}" for param in params)
    signature = f"{prefix}fn {name}{generics_text}({param_text})"
    if not is_unit(returns):
        signature += f" -> {returns}"
    return signature


def canonical_path(item_id: str, item: dict, paths: dict) -> Optional[str]:
    entry = paths.get(item_id) if isinstance(paths, dict) else None
    if isinstance(entry, dict):
        parts = entry.get("path")
        if isinstance(parts, list) and parts:
            return "::".join(str(part) for part in parts)
    return None


def span_location(item: dict) -> tuple[str, int]:
    span = item.get("span") or {}
    filename = span.get("filename") or ""
    begin = span.get("begin") or []
    line = begin[0] if isinstance(begin, list) and begin else 0
    try:
        line = int(line)
    except (TypeError, ValueError):
        line = 0
    return str(filename), line


def collect_functions(data: dict) -> list[FunctionDoc]:
    index = data.get("index")
    if not isinstance(index, dict):
        raise SystemExit("rustdoc JSON 缺少 index 字段，无法提取函数")
    paths = data.get("paths") or {}

    trait_parents: dict[str, str] = {}
    for item_id, item in index.items():
        if not isinstance(item, dict):
            continue
        inner = item.get("inner") or {}
        trait_data = inner.get("trait")
        if not isinstance(trait_data, dict):
            continue
        trait_path = canonical_path(str(item_id), item, paths) or str(
            item.get("name") or "trait"
        )
        for child_id in trait_data.get("items") or []:
            child_key = str(child_id)
            child = index.get(child_key)
            if not isinstance(child, dict):
                continue
            if "function" in (child.get("inner") or {}):
                trait_parents[child_key] = trait_path

    functions: list[FunctionDoc] = []
    for item_id, item in index.items():
        if not isinstance(item, dict):
            continue
        inner = item.get("inner") or {}
        fn_data = inner.get("function")
        if not isinstance(fn_data, dict):
            continue
        item_key = str(item_id)
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue
        visibility = visibility_text(item.get("visibility"))
        is_trait_item = item_key in trait_parents
        if visibility != "public" and not is_trait_item:
            continue

        sig = fn_data.get("sig") or {}
        header = fn_data.get("header") or {}
        params, params_ok = parse_params(sig)
        generics_text, generics_ok = render_generics(fn_data.get("generics"))
        returns, returns_ok = parse_return(sig)
        signature = build_signature(name, generics_text, params, returns, header)

        docs = item.get("docs")
        docs_text = docs if isinstance(docs, str) else ""
        sections = split_sections(docs_text)

        path = canonical_path(item_key, item, paths)
        if not path and is_trait_item:
            path = f"{trait_parents[item_key]}::{name}"
        if not path:
            path = name

        filename, line = span_location(item)

        notes: list[str] = []
        if not (params_ok and generics_ok and returns_ok) or UNRESOLVED in signature:
            notes.append("rustdoc JSON 类型渲染不完整，签名含未解析片段，需以源码复核")
        generics_data = fn_data.get("generics") or {}
        if isinstance(generics_data, dict) and generics_data.get("where_predicates"):
            notes.append("泛型 where 子句未展开到签名中，需以源码 / AST 签名为准")

        functions.append(
            FunctionDoc(
                path=path,
                name=name,
                visibility="public" if is_trait_item else visibility,
                file=filename,
                line=line,
                signature=signature,
                params=params,
                returns=returns,
                docs=docs_text,
                sections=sections,
                owner=trait_parents.get(item_key),
                notes=notes,
            )
        )

    functions.sort(key=lambda fn: (fn.path, fn.line))
    return functions


def attach_ast(functions: list[FunctionDoc], ast_functions: list[dict]) -> None:
    by_name: dict[str, list[dict]] = {}
    for entry in ast_functions:
        if isinstance(entry, dict):
            by_name.setdefault(str(entry.get("name") or ""), []).append(entry)

    for fn in functions:
        candidates = by_name.get(fn.name) or []
        matched: Optional[dict] = None
        exact = [
            candidate
            for candidate in candidates
            if same_file(str(candidate.get("file") or ""), fn.file)
            and _as_int(candidate.get("line")) == fn.line
        ]
        if exact:
            matched = exact[0]
        else:
            same = [
                candidate
                for candidate in candidates
                if same_file(str(candidate.get("file") or ""), fn.file)
            ]
            if len(same) == 1:
                matched = same[0]
            elif len(candidates) == 1:
                matched = candidates[0]

        fn.ast = matched
        if matched is None:
            fn.notes.append("未匹配到 AST 函数，错误分支与源码 doc 一致性未核实")
            continue

        source_doc = "\n".join(str(line) for line in (matched.get("doc_lines") or []))
        if (
            normalize_doc(source_doc)
            and normalize_doc(fn.docs)
            and normalize_doc(source_doc) != normalize_doc(fn.docs)
        ):
            fn.notes.append(
                "源码 doc 与 rustdoc JSON 的 docs 不一致：rustdoc JSON 可能已过期，需重新生成"
            )


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def module_key_from_rustdoc_path(path: str) -> str:
    """把 rustdoc 的完整路径转换为模块键（crate::a::b）。

    rustdoc 路径最后一段可能是函数、方法或类型；对 impl / trait 方法，
    末尾的类型名按 Rust 命名习惯（首字母大写）剔除，避免生成以类型为名的伪模块目录。
    """
    parts = [part for part in (path or "").split("::") if part]
    if len(parts) <= 1:
        return "crate"
    module_parts = parts[:-1]
    while len(module_parts) > 1 and module_parts[-1][:1].isupper():
        module_parts.pop()
    module_parts[0] = "crate"
    return "::".join(module_parts)


def module_dir_name(module_path: str) -> str:
    """把模块键转换为 docs 下的相对目录：crate::a::b -> a/b，crate -> crate。"""
    parts = [part for part in (module_path or "").split("::") if part and part != "crate"]
    return "/".join(parts) if parts else "crate"


def display_path(path: str) -> str:
    """把 rustdoc 路径的 crate 名替换为 crate，保持模块文档内路径一致。"""
    parts = [part for part in (path or "").split("::") if part]
    if not parts:
        return "crate"
    parts[0] = "crate"
    return "::".join(parts)


def collect_interfaces(data: dict) -> list[dict]:
    """提取公有 trait 接口：路径、说明与包含的方法名。"""
    index = data.get("index")
    if not isinstance(index, dict):
        return []
    paths = data.get("paths") or {}
    interfaces: list[dict] = []
    for item_id, item in index.items():
        if not isinstance(item, dict):
            continue
        inner = item.get("inner") or {}
        trait_data = inner.get("trait")
        if not isinstance(trait_data, dict):
            continue
        if item.get("visibility") != "public":
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue
        methods: list[str] = []
        for child_id in trait_data.get("items") or []:
            child = index.get(str(child_id))
            if not isinstance(child, dict):
                continue
            if "function" not in (child.get("inner") or {}):
                continue
            child_name = child.get("name")
            if isinstance(child_name, str) and child_name:
                methods.append(child_name)
        docs = item.get("docs")
        docs_text = docs if isinstance(docs, str) else ""
        filename, line = span_location(item)
        interfaces.append(
            {
                "path": canonical_path(str(item_id), item, paths) or name,
                "name": name,
                "file": normalize_source_path(filename),
                "line": line,
                "summary": split_sections(docs_text).get("summary", ""),
                "methods": methods,
            }
        )
    interfaces.sort(key=lambda entry: entry["path"])
    return interfaces


def _ast_key(entry: dict) -> tuple[str, int, str]:
    return (
        str(entry.get("file") or ""),
        _as_int(entry.get("line")),
        str(entry.get("name") or ""),
    )


def collect_internal_functions(
    ast_functions: list[dict], public_functions: list[FunctionDoc]
) -> list[dict]:
    """非公有 API 函数：未出现在 rustdoc 公有函数中的 AST 函数（含 pub(crate) 与私有函数）。"""
    documented = {_ast_key(fn.ast) for fn in public_functions if fn.ast}
    internal: list[dict] = []
    for entry in ast_functions:
        if not isinstance(entry, dict):
            continue
        if entry.get("is_test") or _ast_key(entry) in documented:
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            continue
        internal.append(entry)
    return internal


def collect_data_structures(ast_data: dict) -> list[dict]:
    """结构体、枚举、联合体与类型别名，只取自 AST（AST 覆盖公有与私有）。"""
    items = ast_data.get("data_structures") or []
    if not isinstance(items, list):
        return []
    structures: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and name:
            structures.append(item)
    return structures


def build_modules(
    functions: list[FunctionDoc],
    internal: list[dict],
    interfaces: list[dict],
    structures: list[dict],
) -> dict[str, dict]:
    """按 Rust 模块聚合公有接口、公有函数、私有函数与数据结构。"""
    modules: dict[str, dict] = {}

    def ensure(module_path: str) -> dict:
        return modules.setdefault(
            module_path,
            {
                "public_functions": [],
                "internal_functions": [],
                "interfaces": [],
                "data_structures": [],
            },
        )

    for fn in functions:
        ast_module = (fn.ast or {}).get("module_path")
        if isinstance(ast_module, str) and ast_module:
            module_path = ast_module
        else:
            module_path = module_key_from_rustdoc_path(fn.owner or fn.path)
        ensure(module_path)["public_functions"].append(fn)

    for entry in internal:
        module_path = entry.get("module_path")
        key = module_path if isinstance(module_path, str) and module_path else "crate"
        ensure(key)["internal_functions"].append(entry)

    for interface in interfaces:
        ensure(module_key_from_rustdoc_path(interface["path"]))["interfaces"].append(interface)

    for structure in structures:
        module_path = structure.get("module_path")
        key = module_path if isinstance(module_path, str) and module_path else "crate"
        ensure(key)["data_structures"].append(structure)

    for bundle in modules.values():
        bundle["public_functions"].sort(key=lambda fn: (fn.path, fn.line))
        bundle["internal_functions"].sort(
            key=lambda entry: (
                str(entry.get("file") or ""),
                _as_int(entry.get("line")),
                str(entry.get("name") or ""),
            )
        )
        bundle["interfaces"].sort(key=lambda entry: entry["path"])
        bundle["data_structures"].sort(
            key=lambda entry: (
                str(entry.get("file") or ""),
                _as_int(entry.get("line")),
                str(entry.get("name") or ""),
            )
        )
    return modules


def summary_line(text: str) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return "—"


def doc_line_summary(lines: list) -> str:
    for line in lines or []:
        if str(line).strip():
            return str(line).strip()
    return "—"


def render_fn_params(params: list[Param]) -> str:
    rendered = [f"`{param.name}: {param.ty}`" for param in params]
    return "、".join(rendered) if rendered else "—"


def render_ast_params(params: list) -> str:
    rendered: list[str] = []
    for param in params or []:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name") or "")
        if not name:
            continue
        rendered.append(f"`{name}: {param.get('ty') or ''}`")
    return "、".join(rendered) if rendered else "—"


def field_text(field: dict, with_visibility: bool) -> str:
    name = str(field.get("name") or "")
    ty = str(field.get("ty") or "")
    visibility = str(field.get("visibility") or "")
    prefix = ""
    if with_visibility:
        if visibility == "public":
            prefix = "pub "
        elif visibility.startswith("pub("):
            prefix = f"{visibility} "
    if name.isdigit():
        return f"{prefix}{ty}".strip()
    return f"{prefix}{name}: {ty}".strip()


def render_field_list(fields: list, with_visibility: bool) -> str:
    rendered = [field_text(field, with_visibility) for field in fields or [] if isinstance(field, dict)]
    return "、".join(rendered)


def render_structure_fields(item: dict) -> str:
    kind = str(item.get("kind") or "")
    if kind == "enum":
        rendered: list[str] = []
        for variant in item.get("variants") or []:
            if not isinstance(variant, dict):
                continue
            name = str(variant.get("name") or "")
            variant_kind = str(variant.get("kind") or "")
            fields = render_field_list(variant.get("fields") or [], False)
            if variant_kind == "unit" or not fields:
                rendered.append(name)
            elif variant_kind == "tuple":
                rendered.append(f"{name}({fields})")
            else:
                rendered.append(f"{name} {{ {fields} }}")
        return "、".join(f"`{entry}`" for entry in rendered) if rendered else "—"
    if kind == "type_alias":
        alias = str(item.get("alias") or "")
        return f"`= {alias}`" if alias else "—"
    fields = render_field_list(item.get("fields") or [], True)
    return f"`{fields}`" if fields else "—"


def location_text(file: str, line: int) -> str:
    normalized = normalize_source_path(str(file or ""))
    if not normalized:
        return "—"
    return f"{normalized}:{line}" if line else normalized


def render_module_doc_file(kind: str, module_path: str, items: list) -> str:
    title = MODULE_DOC_TITLES[kind]
    lines = [
        f"# 模块 {module_path} · {title}",
        "",
        "> 由 project-doc-sync 依据 rustdoc JSON 与 syn AST 生成：公有接口与公有函数取自 rustdoc JSON，",
        "> 私有函数与数据结构取自 AST。不推断语义，无法证实的说明记为「—」。",
        "",
    ]

    if kind == "interfaces":
        if items:
            lines.append("| 接口 | 定义位置 | 可见性 | 方法 | 说明 |")
            lines.append("| --- | --- | --- | --- | --- |")
            for interface in items:
                methods = "、".join(f"`{name}`" for name in interface["methods"]) or "—"
                lines.append(
                    f"| `{md_cell(display_path(interface['path']))}` | "
                    f"`{md_cell(location_text(interface.get('file'), _as_int(interface.get('line'))))}` | "
                    f"public | {methods} | {md_cell(summary_line(interface['summary']))} |"
                )
        else:
            lines.append("（无）")
    elif kind == "public_functions":
        if items:
            lines.append("| 函数 | 定义位置 | 签名 | 入参 | 返回值 | 说明 |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for fn in items:
                signature, from_ast = display_signature(fn)
                note = "（签名取自 AST，待复核）" if from_ast else ""
                lines.append(
                    f"| `{md_cell(display_path(fn.path))}` | "
                    f"`{md_cell(location_text(fn.file, fn.line))}` | "
                    f"`{md_cell(signature)}`{note} | {render_fn_params(fn.params)} | "
                    f"`{md_cell(fn.returns)}` | "
                    f"{md_cell(summary_line(fn.sections.get('summary') or ''))} |"
                )
        else:
            lines.append("（无）")
    elif kind == "internal_functions":
        if items:
            lines.append("| 函数 | 定义位置 | 签名 | 入参 | 返回值 | 说明 |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for entry in items:
                lines.append(
                    f"| `{md_cell(str(entry.get('name') or ''))}` | "
                    f"`{md_cell(location_text(entry.get('file'), _as_int(entry.get('line'))))}` | "
                    f"`{md_cell(str(entry.get('signature') or ''))}` | "
                    f"{render_ast_params(entry.get('params') or [])} | "
                    f"`{md_cell(str(entry.get('return_type') or '()'))}` | "
                    f"{md_cell(doc_line_summary(entry.get('doc_lines') or []))} |"
                )
        else:
            lines.append("（无）")
    elif kind == "data_structures":
        if items:
            lines.append("| 名称 | 定义位置 | 类型 | 可见性 | 字段 / 变体 | 说明 |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for item in items:
                lines.append(
                    f"| `{md_cell(str(item.get('name') or ''))}` | "
                    f"`{md_cell(location_text(item.get('file'), _as_int(item.get('line'))))}` | "
                    f"{md_cell(str(item.get('kind') or ''))} | "
                    f"{md_cell(str(item.get('visibility') or ''))} | "
                    f"{render_structure_fields(item)} | "
                    f"{md_cell(doc_line_summary(item.get('doc_lines') or []))} |"
                )
        else:
            lines.append("（无）")
    else:
        raise SystemExit(f"未知的模块文档类型：{kind}")

    return "\n".join(lines) + "\n"


def write_module_docs(docs_root: Path, modules: dict[str, dict]) -> list[Path]:
    written: list[Path] = []
    for module_path in sorted(modules):
        bundle = modules[module_path]
        if not has_module_content(bundle):
            continue
        target_dir = docs_root / module_dir_name(module_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        for kind, filename in MODULE_DOC_FILES.items():
            target = target_dir / filename
            target.write_text(
                render_module_doc_file(kind, module_path, bundle[kind]),
                encoding="utf-8",
            )
            written.append(target)
            print(f"模块文档：{target}")
    return written


def has_module_content(bundle: dict) -> bool:
    return any(bundle[key] for key in MODULE_DOC_FILES)


def verify_module_docs(docs_root: Path, modules: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    for module_path in sorted(modules):
        bundle = modules[module_path]
        if not has_module_content(bundle):
            continue
        target_dir = docs_root / module_dir_name(module_path)
        texts: dict[str, str] = {}
        for kind, filename in MODULE_DOC_FILES.items():
            target = target_dir / filename
            if not target.is_file():
                errors.append(f"模块 `{module_path}`：缺少模块文档 `{target}`")
                continue
            texts[kind] = target.read_text(encoding="utf-8")

        for fn in bundle["public_functions"]:
            text = texts.get("public_functions", "")
            if f"`{display_path(fn.path)}`" not in text:
                errors.append(f"模块 `{module_path}`：公有函数文档未收录 `{fn.path}`")
            if fn.file and location_text(fn.file, fn.line) not in text:
                errors.append(f"模块 `{module_path}`：公有函数文档未标注 `{fn.path}` 的定义位置")
        for entry in bundle["internal_functions"]:
            name = str(entry.get("name") or "")
            text = texts.get("internal_functions", "")
            if f"`{name}`" not in text:
                errors.append(f"模块 `{module_path}`：私有函数文档未收录 `{name}`")
            location = location_text(entry.get("file"), _as_int(entry.get("line")))
            if entry.get("file") and location not in text:
                errors.append(f"模块 `{module_path}`：私有函数文档未标注 `{name}` 的定义位置")
        for interface in bundle["interfaces"]:
            text = texts.get("interfaces", "")
            if f"`{display_path(interface['path'])}`" not in text:
                errors.append(f"模块 `{module_path}`：公有接口文档未收录 `{interface['path']}`")
            location = location_text(interface.get("file"), _as_int(interface.get("line")))
            if interface.get("file") and location not in text:
                errors.append(
                    f"模块 `{module_path}`：公有接口文档未标注 `{interface['path']}` 的定义位置"
                )
        for item in bundle["data_structures"]:
            name = str(item.get("name") or "")
            text = texts.get("data_structures", "")
            if f"`{name}`" not in text:
                errors.append(f"模块 `{module_path}`：数据结构文档未收录 `{name}`")
            location = location_text(item.get("file"), _as_int(item.get("line")))
            if item.get("file") and location not in text:
                errors.append(f"模块 `{module_path}`：数据结构文档未标注 `{name}` 的定义位置")
    return errors


def collect_gaps(fn: FunctionDoc) -> list[Gap]:
    gaps: list[Gap] = []
    location = f"{fn.file}:{fn.line}" if fn.file else fn.path

    if not (fn.sections.get("summary") or "").strip():
        gaps.append(
            Gap(fn.path, "文档摘要", "缺少函数职责说明", "用一句话描述函数职责", location)
        )

    params = [param for param in fn.params if not param.is_self]
    arguments = fn.sections.get("arguments") or ""
    if params:
        if not arguments.strip():
            gaps.append(
                Gap(
                    fn.path,
                    "参数含义",
                    "doc 注释缺少 # Arguments",
                    "逐个说明参数含义与取值约束",
                    location,
                )
            )
        else:
            for param in params:
                if f"`{param.name}`" not in arguments:
                    gaps.append(
                        Gap(
                            fn.path,
                            f"参数 `{param.name}` 的含义",
                            "doc 注释未说明该参数",
                            "补充该参数含义与取值约束",
                            location,
                        )
                    )

    if not is_unit(fn.returns) and not (fn.sections.get("returns") or "").strip():
        gaps.append(
            Gap(
                fn.path,
                "返回值语义",
                "doc 注释缺少 # Returns",
                "说明返回值的语义与可能的取值",
                location,
            )
        )

    if is_result(fn.returns) and not (fn.sections.get("errors") or "").strip():
        gaps.append(
            Gap(
                fn.path,
                "错误场景 / 错误码",
                "返回 Result 但 doc 注释缺少 # Errors",
                "说明每个错误分支的触发条件与错误码",
                location,
            )
        )

    if not (fn.sections.get("examples") or "").strip():
        gaps.append(
            Gap(
                fn.path,
                "# Examples",
                "doc 注释缺少示例",
                "提供可编译并验证的示例",
                location,
            )
        )

    if fn.ast is None:
        gaps.append(
            Gap(
                fn.path,
                "AST 事实",
                "未匹配到 AST 函数",
                "确认源码路径与 AST 提取范围后重新运行 ast_inspect.rs",
                location,
            )
        )

    for note in fn.notes:
        if "签名含未解析片段" in note or "where 子句" in note:
            gaps.append(Gap(fn.path, "类型 / 泛型", note, "依据源码补全类型与泛型约束", location))

    return gaps


def display_signature(fn: FunctionDoc) -> tuple[str, bool]:
    if UNRESOLVED in fn.signature and fn.ast and fn.ast.get("signature"):
        return str(fn.ast["signature"]), True
    return fn.signature, False


def render_facts(functions: list[FunctionDoc], gaps: dict[str, list[Gap]]) -> str:
    lines = [
        "# 函数文档事实包",
        "",
        "> 来源：rustdoc JSON（签名、可见性、doc 原文字）+ syn AST（函数体分支、错误分支、调用关系）。",
        "> LLM 只能使用本文件中的事实合成 `///` 注释，不得补充参数含义、错误码或返回值语义。",
        "",
    ]
    for fn in functions:
        lines.append(f"## {fn.path}")
        lines.append("")
        lines.append(f"- 源位置：`{fn.file}:{fn.line}`")
        lines.append(f"- 可见性：`{fn.visibility}`")
        lines.append(f"- 签名（rustdoc JSON）：`{fn.signature}`")
        ast = fn.ast
        if ast:
            ast_signature = ast.get("signature")
            if ast_signature and ast_signature != fn.signature:
                lines.append(
                    f"- 签名（AST 参考，权威签名以上一行 rustdoc JSON 为准）：`{ast_signature}`"
                )
            has_body = "有" if ast.get("has_body") else "无（trait 声明）"
            lines.append(f"- 函数体：{has_body}")
        docs = fn.docs.strip()
        if docs:
            lines.append("- doc 原文：")
            lines.append("")
            for line in docs.splitlines():
                lines.append(f"  > {line}" if line.strip() else "  >")
            lines.append("")
        else:
            lines.append("- doc 原文：（空）")

        if fn.params:
            lines.append("- 参数（类型来自 rustdoc JSON）：")
            for param in fn.params:
                suffix = "（self）" if param.is_self else ""
                lines.append(f"  - `{param.name}`：`{param.ty}`{suffix}")
        lines.append(f"- 返回类型：`{fn.returns}`")

        branches = (ast or {}).get("branches") or []
        if branches:
            lines.append("- 函数体分支（AST）：")
            for branch in branches[:20]:
                condition = str(branch.get("condition") or "")
                lines.append(
                    f"  - `{branch.get('kind')}` @ L{branch.get('line')}：`{condition}`"
                )

        error_returns = (ast or {}).get("error_returns") or []
        if error_returns:
            lines.append("- 错误分支（AST，仅位置，不含语义）：")
            for item in error_returns[:20]:
                lines.append(
                    f"  - `{item.get('kind')}` @ L{item.get('line')}：`{item.get('expression')}`"
                )
        elif is_result(fn.returns):
            lines.append("- 错误分支（AST）：未发现 `?` / `Err(...)`，错误来源需人工确认")

        panics = (ast or {}).get("panics") or []
        if panics:
            lines.append("- panic 风险（AST）：")
            for item in panics[:10]:
                lines.append(f"  - `{item.get('kind')}` @ L{item.get('line')}")

        calls = (ast or {}).get("calls") or []
        if calls:
            calls_text = "、".join(f"`{call}`" for call in calls[:20])
            lines.append(f"- 调用（AST）：{calls_text}")

        if fn.notes:
            lines.append("- 一致性提示：")
            for note in fn.notes:
                lines.append(f"  - {note}")

        fn_gaps = gaps.get(fn.path) or []
        if fn_gaps:
            lines.append("- 未确认字段：")
            for gap in fn_gaps:
                lines.append(f"  - {gap.field_name}：{gap.reason}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_skeleton(functions: list[FunctionDoc]) -> str:
    lines = [
        "# 函数文档骨架（Rustdoc Markdown 固定格式）",
        "",
        "> 依据 `assets/fn_doc.md` 的固定格式生成。`<!-- 未确认：... -->` 必须由人类确认后",
        "> 替换为事实或删除，禁止把占位标记留在源码中。",
        "",
    ]
    for fn in functions:
        signature, from_ast = display_signature(fn)
        lines.append(f"## {fn.path}")
        lines.append("")
        lines.append(f"源位置：`{fn.file}:{fn.line}`")
        lines.append("")
        lines.append("````rust")
        if from_ast:
            lines.append("// 注意：rustdoc JSON 类型渲染不完整，以下签名取自 AST，需人工复核。")
        summary_lines = (fn.sections.get("summary") or "").strip().splitlines()
        if not summary_lines:
            summary_lines = ["<!-- 未确认：函数职责 -->"]
        for line in summary_lines:
            lines.append(f"/// {line}" if line.strip() else "///")

        params = [param for param in fn.params if not param.is_self]
        if params:
            lines.append("///")
            lines.append("/// # Arguments")
            for param in params:
                lines.append(f"/// * `{param.name}` - <!-- 未确认：参数含义 -->")

        if not is_unit(fn.returns):
            lines.append("///")
            lines.append("/// # Returns")
            lines.append("/// <!-- 未确认：返回值语义 -->")

        if is_result(fn.returns):
            lines.append("///")
            lines.append("/// # Errors")
            error_returns = (fn.ast or {}).get("error_returns") or []
            if error_returns:
                for item in error_returns[:10]:
                    lines.append(
                        f"/// <!-- 未确认：L{item.get('line')} `{item.get('kind')}` 的错误场景与错误码 -->"
                    )
            else:
                lines.append("/// <!-- 未确认：错误场景与错误码 -->")

        lines.append("///")
        lines.append("/// # Examples")
        lines.append("/// ```")
        lines.append("/// <!-- 未确认：示例需依据真实签名编写并编译验证 -->")
        lines.append("/// ```")

        lines.append(signature)
        if UNRESOLVED in signature:
            lines.append("// 未解析类型需人工补齐后再写文档")
        lines.append("````")
        lines.append("")
    return "\n".join(lines) + "\n"


def md_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_gap_report(gaps: dict[str, list[Gap]]) -> str:
    lines = [
        "# 未确认字段清单",
        "",
        "> 只列出无法从 rustdoc JSON 或 AST 证实的内容。确认后请同步更新源码 `///` 注释，",
        "> 再重新运行 `generate_fn_docs.py --verify`。",
        "",
    ]
    rows: list[str] = []
    for path in sorted(gaps):
        for gap in gaps[path]:
            rows.append(
                "| `{}` | {} | {} | {} | `{}` |".format(
                    md_cell(gap.function),
                    md_cell(gap.field_name),
                    md_cell(gap.reason),
                    md_cell(gap.needs),
                    md_cell(gap.location),
                )
            )
    if not rows:
        lines.append("（无未确认字段）")
        return "\n".join(lines) + "\n"
    lines.append("| 函数 | 字段 | 原因 | 需人类确认的内容 | 位置 |")
    lines.append("| --- | --- | --- | --- | --- |")
    lines.extend(rows)
    return "\n".join(lines) + "\n"


def write_outputs(
    out_dir: Path, functions: list[FunctionDoc], gaps: dict[str, list[Gap]]
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    facts_path = out_dir / "facts.md"
    skeleton_path = out_dir / "skeleton.md"
    gaps_path = out_dir / "unconfirmed-fields.md"
    facts_path.write_text(render_facts(functions, gaps), encoding="utf-8")
    skeleton_path.write_text(render_skeleton(functions), encoding="utf-8")
    gaps_path.write_text(render_gap_report(gaps), encoding="utf-8")
    print(f"事实包：{facts_path}")
    print(f"骨架：{skeleton_path}")
    print(f"未确认字段清单：{gaps_path}")


def run_verify(
    functions: list[FunctionDoc], modules: dict[str, dict], docs_root: Path
) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for fn in functions:
        location = f"{fn.file}:{fn.line}" if fn.file else fn.path
        prefix = f"{fn.path}（{location}）"

        if not (fn.sections.get("summary") or "").strip():
            errors.append(f"{prefix}：缺少文档摘要")

        params = [param for param in fn.params if not param.is_self]
        arguments = fn.sections.get("arguments") or ""
        if params:
            if not arguments.strip():
                errors.append(f"{prefix}：有参数但缺少 # Arguments")
            else:
                for param in params:
                    if f"`{param.name}`" not in arguments:
                        errors.append(f"{prefix}：# Arguments 未说明参数 `{param.name}`")

        if not is_unit(fn.returns) and not (fn.sections.get("returns") or "").strip():
            errors.append(f"{prefix}：返回值非 () 但缺少 # Returns")

        if is_result(fn.returns) and not (fn.sections.get("errors") or "").strip():
            errors.append(f"{prefix}：返回 Result 但缺少 # Errors")

        if "未确认：" in (fn.docs or "") or "<!-- 未确认" in (fn.docs or ""):
            errors.append(f"{prefix}：源码 doc 中残留「未确认」占位")

        for note in fn.notes:
            if "签名含未解析片段" in note or "where 子句" in note or "可能已过期" in note:
                errors.append(f"{prefix}：{note}")
            else:
                warnings.append(f"{prefix}：{note}")

        if not (fn.sections.get("examples") or "").strip():
            warnings.append(f"{prefix}：缺少 # Examples（建议补充并编译验证）")

    errors.extend(verify_module_docs(docs_root, modules))

    print(
        f"覆盖率校验：{len(functions)} 个公有函数，{len(modules)} 个模块"
        f"（模块文档根目录：{docs_root}）"
    )
    if errors:
        print(f"\n错误 {len(errors)} 项：")
        for item in errors:
            print(f"  - {item}")
    if warnings:
        print(f"\n警告 {len(warnings)} 项：")
        for item in warnings:
            print(f"  - {item}")
    if errors:
        print("\n校验未通过：补全必需章节并重新生成 rustdoc JSON 后再校验。")
        return 1
    print("\n校验通过。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="合并 rustdoc JSON 与 syn AST 事实，生成函数文档骨架并校验覆盖率。"
    )
    parser.add_argument("--rustdoc", required=True, help="rustdoc JSON 路径")
    parser.add_argument("--ast", help="ast_inspect.rs 输出的 AST 事实 JSON 路径")
    parser.add_argument("-o", "--out", help="事实包 / 骨架 / 未确认清单的输出目录")
    parser.add_argument(
        "--docs-root",
        default="docs/data-struct-and-interface",
        help="按模块分类的接口与数据结构文档根目录（默认 docs/data-struct-and-interface）",
    )
    parser.add_argument(
        "--no-module-docs",
        action="store_true",
        help="只生成事实包与骨架，不写按模块分类的接口与数据结构文档",
    )
    parser.add_argument("--verify", action="store_true", help="只校验覆盖率，不写文件")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    rustdoc_data = load_json(Path(args.rustdoc))
    ast_data = load_json(Path(args.ast)) if args.ast else {}
    ast_functions = ast_data.get("functions") or []
    if not isinstance(ast_functions, list):
        raise SystemExit("AST JSON 的 functions 字段必须是数组")

    functions = collect_functions(rustdoc_data)
    ast_entries = [entry for entry in ast_functions if isinstance(entry, dict)]
    attach_ast(functions, ast_entries)

    modules = build_modules(
        functions,
        collect_internal_functions(ast_entries, functions),
        collect_interfaces(rustdoc_data),
        collect_data_structures(ast_data),
    )
    docs_root = Path(args.docs_root)

    if args.verify:
        return run_verify(functions, modules, docs_root)

    if not args.out:
        print("非校验模式必须指定 -o/--out", file=sys.stderr)
        return 2

    gaps: dict[str, list[Gap]] = {}
    for fn in functions:
        fn_gaps = collect_gaps(fn)
        if fn_gaps:
            gaps[fn.path] = fn_gaps

    write_outputs(Path(args.out), functions, gaps)
    if not args.no_module_docs:
        write_module_docs(docs_root, modules)
    unresolved = sum(len(items) for items in gaps.values())
    print(
        f"完成：{len(functions)} 个公有函数，{len(modules)} 个模块，{unresolved} 项未确认字段。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
