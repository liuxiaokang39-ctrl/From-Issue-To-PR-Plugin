#!/usr/bin/env python3
"""把本插件的命令与 Agent 安装到 Codex 的约定目录。

commands/  → ~/.codex/prompts/*.md，Codex 以 /prompts:xxx 暴露为入口
agents/    → ~/.codex/agents/（用户级）或 <项目>/.codex/agents/（项目级），
             并在 config.toml 注册 [agents.<role>] 与 features.multi_agent = true。

用法：
    python scripts/install_codex.py                      # 用户级：prompts + ~/.codex/agents + ~/.codex/config.toml
    python scripts/install_codex.py --scope project --project .   # 项目级：prompts + <项目>/.codex/agents
    python scripts/install_codex.py --dry-run            # 只打印将要执行的复制与配置改动
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DESCRIPTION = "按 8 个阶段（含 spec-manager 管理角色）把需求推进到 PR 的编排 Agent"
EXPECTED_COMMAND_COUNT = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="安装 Codex 命令提示词与 Agent 角色配置")
    parser.add_argument("--scope", choices=("user", "project"), default="user",
                        help="user：写入 ~/.codex；project：Agent 与 config 写入项目 .codex")
    parser.add_argument("--project", default=".", help="项目根目录，--scope project 时使用")
    parser.add_argument("--prompts-dir", help="覆盖 prompts 目录（默认 ~/.codex/prompts）")
    parser.add_argument("--agents-dir", help="覆盖 agents 目录（默认随 scope）")
    parser.add_argument("--config", help="覆盖 config.toml 路径（默认随 scope）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不写入")
    return parser.parse_args()


def resolve_targets(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """返回 (prompts 目录, agents 目录, config.toml 路径)。"""
    home_codex = Path.home() / ".codex"
    project_codex = Path(args.project).resolve() / ".codex"

    prompts_dir = Path(args.prompts_dir).expanduser() if args.prompts_dir else home_codex / "prompts"
    if args.agents_dir:
        agents_dir = Path(args.agents_dir).expanduser()
    else:
        agents_dir = (home_codex if args.scope == "user" else project_codex) / "agents"
    config_path = Path(args.config).expanduser() if args.config else (
        home_codex if args.scope == "user" else project_codex
    ) / "config.toml"
    return prompts_dir, agents_dir, config_path


def description_from_md(md_path: Path) -> str:
    """读取 Agent Markdown 角色定义的 frontmatter description。"""
    if not md_path.is_file():
        return DEFAULT_DESCRIPTION
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"(?ms)^---\s*\n(.*?)\n---", text)
    if not match:
        return DEFAULT_DESCRIPTION
    for line in match.group(1).splitlines():
        if line.strip().startswith("description:"):
            return line.split("description:", 1)[1].strip() or DEFAULT_DESCRIPTION
    return DEFAULT_DESCRIPTION


def copy_files(files: list[Path], target: Path, dry_run: bool) -> list[Path]:
    copied: list[Path] = []
    for src in files:
        dest = target / src.name
        copied.append(dest)
        if dry_run:
            continue
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return copied


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ensure_multi_agent(text: str) -> tuple[str, bool]:
    """确保 features.multi_agent = true，返回 (新文本, 是否有改动)。"""
    header = re.search(r"(?m)^\[features\][ \t]*$", text)
    if header:
        rest = text[header.end():]
        next_header = re.search(r"(?m)^\[", rest)
        block = rest[: next_header.start()] if next_header else rest
        if re.search(r"(?m)^[ \t]*multi_agent[ \t]*=", block):
            return text, False
        return text[: header.end()] + "\nmulti_agent = true" + text[header.end():], True

    body = "\n[features]\nmulti_agent = true\n"
    if text and not text.endswith("\n"):
        text += "\n"
    return text + body, True


def ensure_agent_table(text: str, role: str, description: str, config_file: str) -> tuple[str, bool]:
    """确保存在 [agents.<role>] 表，返回 (新文本, 是否有改动)。"""
    pattern = r"(?m)^[ \t]*\[agents\." + re.escape(role) + r"\][ \t]*$"
    if re.search(pattern, text):
        return text, False

    if text and not text.endswith("\n"):
        text += "\n"
    block = (
        f"\n[agents.{role}]\n"
        f"description = {_toml_string(description)}\n"
        f"config_file = {_toml_string(config_file)}\n"
    )
    return text + block, True


def validate_toml(text: str) -> str | None:
    """用 tomllib 校验；不可用或通过时返回 None，失败时返回错误信息。"""
    try:
        import tomllib
    except ImportError:
        return None
    try:
        tomllib.loads(text)
    except Exception as exc:  # noqa: BLE001 - 只用于回滚前的语法校验
        return str(exc)
    return None


def rel_config_file(config_path: Path, agent_toml: Path) -> str:
    relative = os.path.relpath(agent_toml.resolve(), config_path.parent.resolve())
    return Path(relative).as_posix()


def main() -> int:
    args = parse_args()
    prompts_dir, agents_dir, config_path = resolve_targets(args)

    command_files = sorted((PLUGIN_ROOT / "commands").glob("*.md"))
    agent_tomls = sorted((PLUGIN_ROOT / "agents").glob("*.toml"))

    if len(command_files) != EXPECTED_COMMAND_COUNT:
        print(
            f"commands/ 下命令数为 {len(command_files)}，期望 {EXPECTED_COMMAND_COUNT}"
            "（fitp-workflow、fitp-issueWriter）；请检查命令文件后重试。",
            file=sys.stderr,
        )
        return 1

    print(f"插件目录：{PLUGIN_ROOT}")
    print(f"prompts 目录：{prompts_dir}")
    print(f"agents 目录：{agents_dir}")
    print(f"config 文件：{config_path}")

    copied_commands = copy_files(command_files, prompts_dir, args.dry_run)
    copied_agents = copy_files(agent_tomls, agents_dir, args.dry_run)

    original_config = config_path.read_text(encoding="utf-8-sig") if config_path.is_file() else ""
    updated = original_config
    changes: list[str] = []

    updated, changed = ensure_multi_agent(updated)
    if changed:
        changes.append("features.multi_agent = true")

    for toml_path in agent_tomls:
        role = toml_path.stem
        description = description_from_md(PLUGIN_ROOT / "agents" / f"{role}.md")
        config_file = rel_config_file(config_path, agents_dir / toml_path.name)
        updated, changed = ensure_agent_table(updated, role, description, config_file)
        if changed:
            changes.append(f"[agents.{role}]")

    if changes:
        error = validate_toml(updated)
        if error:
            print(f"配置校验失败，未写入：{error}", file=sys.stderr)
            return 1
        if not args.dry_run:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(updated, encoding="utf-8")

    print("\n安装结果：")
    print(f"- 命令提示词 {len(copied_commands)} 个（期望 {EXPECTED_COMMAND_COUNT}）：")
    for dest in copied_commands:
        print(f"    {dest}")
    print(f"- Agent 角色 {len(copied_agents)} 个：")
    for dest in copied_agents:
        print(f"    {dest}")
    print("- config.toml 改动：")
    if changes:
        for item in changes:
            print(f"    {item}")
    else:
        print("    无需改动（相关条目已存在）")

    if args.dry_run:
        print("\n[dry-run] 未写入任何文件")
    else:
        print("\n完成。重启 Codex 后生效：命令用 /prompts:xxx 调用。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
