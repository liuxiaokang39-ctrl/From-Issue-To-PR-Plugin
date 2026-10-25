#!/usr/bin/env bash
# 生成并归档 rustdoc JSON，作为 project-doc-sync 的可信底座。
#
# 用法：
#   bash extract_rustdoc_json.sh -p <crate名> [--manifest-path <Cargo.toml>] [-o <输出目录>]
#
# 说明：
#   - rustdoc JSON 目前需要 nightly 工具链，脚本会检查 rustup 与 nightly；
#   - 生成失败时不降级改用其他来源，直接非零退出；
#   - 输出目录默认为 <target>/rust-fn-doc，文件名为 <crate名>.json。
set -euo pipefail

usage() {
  cat <<'EOF'
用法：bash extract_rustdoc_json.sh [选项]

选项：
  -p, --package <名称>        要生成文档的包名（工作区多包时建议显式指定）
  -o, --out <目录>            rustdoc JSON 的输出目录，默认 <target>/rust-fn-doc
      --manifest-path <路径>  Cargo.toml 路径，默认 ./Cargo.toml
      --toolchain <名称>      工具链名称，默认 nightly
      --all-features          为所有 feature 生成文档
      --features <列表>       为指定 feature 生成文档（逗号分隔）
  -h, --help                  显示本帮助

示例：
  bash extract_rustdoc_json.sh -p my-crate --manifest-path ./Cargo.toml -o target/rust-fn-doc
EOF
}

manifest="Cargo.toml"
package=""
out=""
toolchain="nightly"
feature_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--package)
      if [[ $# -lt 2 ]]; then
        echo "参数 $1 缺少取值" >&2
        exit 2
      fi
      package="$2"
      shift 2
      ;;
    -o|--out)
      if [[ $# -lt 2 ]]; then
        echo "参数 $1 缺少取值" >&2
        exit 2
      fi
      out="$2"
      shift 2
      ;;
    --manifest-path)
      if [[ $# -lt 2 ]]; then
        echo "参数 $1 缺少取值" >&2
        exit 2
      fi
      manifest="$2"
      shift 2
      ;;
    --toolchain)
      if [[ $# -lt 2 ]]; then
        echo "参数 $1 缺少取值" >&2
        exit 2
      fi
      toolchain="$2"
      shift 2
      ;;
    --all-features)
      feature_args+=(--all-features)
      shift
      ;;
    --features)
      if [[ $# -lt 2 ]]; then
        echo "参数 $1 缺少取值" >&2
        exit 2
      fi
      feature_args+=(--features "$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数：$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v cargo >/dev/null 2>&1; then
  echo "未找到 cargo，请先安装 Rust 工具链（https://rustup.rs）。" >&2
  exit 2
fi

if [[ ! -f "$manifest" ]]; then
  echo "找不到 Cargo.toml：$manifest" >&2
  exit 2
fi

cargo_cmd=(cargo)
if command -v rustup >/dev/null 2>&1; then
  if ! rustup toolchain list 2>/dev/null | grep -q "^${toolchain}"; then
    echo "未安装 ${toolchain} 工具链。请执行：rustup toolchain install ${toolchain}" >&2
    exit 2
  fi
  cargo_cmd=("cargo" "+${toolchain}")
else
  echo "未找到 rustup，将直接使用当前 cargo；若当前不是 ${toolchain}，请手动切换后再运行。" >&2
fi

echo "读取构建元数据：$manifest"
metadata="$("${cargo_cmd[@]}" metadata --no-deps --format-version 1 --manifest-path "$manifest")"

target_dir="$(printf '%s' "$metadata" | sed -n 's/.*"target_directory":"\([^"]*\)".*/\1/p' | sed 's/\\\\/\\/g')"
if [[ -z "$target_dir" ]]; then
  echo "无法从 cargo metadata 解析 target_directory，改用 Cargo.toml 同级的 target 目录。" >&2
  target_dir="$(cd "$(dirname "$manifest")" && pwd)/target"
fi

if [[ -z "$out" ]]; then
  out="$target_dir/rust-fn-doc"
fi

doc_args=(rustdoc --lib --manifest-path "$manifest")
if [[ -n "$package" ]]; then
  doc_args+=(--package "$package")
fi
if [[ ${#feature_args[@]} -gt 0 ]]; then
  doc_args+=("${feature_args[@]}")
fi

echo "生成 rustdoc JSON：${cargo_cmd[*]} ${doc_args[*]} -- -Z unstable-options --output-format json"
if ! "${cargo_cmd[@]}" "${doc_args[@]}" -- -Z unstable-options --output-format json; then
  echo "rustdoc JSON 生成失败：请检查编译错误，或确认 nightly 工具链可用。不得改用 AST 签名作为可信底座。" >&2
  exit 1
fi

doc_dir="$target_dir/doc"
candidate=""
if [[ -n "$package" ]]; then
  crate_file="${package//-/_}.json"
  if [[ -f "$doc_dir/$crate_file" ]]; then
    candidate="$doc_dir/$crate_file"
  fi
fi

if [[ -z "$candidate" ]]; then
  candidate="$(ls -t "$doc_dir"/*.json 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$candidate" || ! -f "$candidate" ]]; then
  echo "未找到生成的 rustdoc JSON，请检查 $doc_dir 下的输出。" >&2
  exit 1
fi

first_char="$(head -c 1 "$candidate" || true)"
if [[ "$first_char" != "{" ]]; then
  echo "生成的 JSON 格式异常：$candidate" >&2
  exit 1
fi

mkdir -p "$out"
dest="$out/$(basename "$candidate")"
cp "$candidate" "$dest"

format_version="$(sed -n 's/.*"format_version":\([0-9][0-9]*\).*/\1/p' "$dest" | head -n 1)"
if [[ -n "$format_version" ]]; then
  echo "rustdoc JSON format_version：$format_version（切换工具链后必须重新生成）"
fi
echo "rustdoc JSON：$dest"
