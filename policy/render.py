#!/usr/bin/env python3
"""Render or install the shared command allowlist for supported agent CLIs."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import runtime as runtime_policy


ROOT = Path(__file__).parent


def commands() -> list[str]:
    data = json.loads((ROOT / "commands.json").read_text())
    values = data["commands"]["allow"]
    if not values or values != sorted(set(values)) or not all(isinstance(value, str) and value for value in values):
        raise ValueError("commands.allow must be a non-empty, sorted list of unique strings")
    return values


def codex(values: list[str]) -> str:
    return "".join(
        f'prefix_rule(pattern = [{json.dumps(value)}], decision = "allow", '
        f'justification = "Approved by agent-toolbox")\n'
        for value in values
    )


def claude(values: list[str]) -> list[str]:
    return [f"Bash({value} *)" for value in values]


def gemini(values: list[str]) -> str:
    return "".join(
        "[[rule]]\n"
        'toolName = "run_shell_command"\n'
        f"commandPrefix = {json.dumps(value)}\n"
        'decision = "allow"\n'
        "priority = 100\n\n"
        for value in values
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def install(home: Path, values: list[str], runtime: dict[str, bool]) -> None:
    settings_path = home / ".claude/settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    if not isinstance(settings, dict) or not isinstance(settings.get("permissions", {}), dict):
        raise ValueError(f"Expected a JSON object with an optional permissions object: {settings_path}")
    permissions = settings.setdefault("permissions", {})
    allowed = permissions.setdefault("allow", [])
    if not isinstance(allowed, list):
        raise ValueError(f"Expected permissions.allow to be a list: {settings_path}")
    permissions["allow"] = list(dict.fromkeys([*allowed, *claude(values)]))

    codex_config_path = home / ".codex/config.toml"
    codex_config = (
        codex_config_path.read_text(encoding="utf-8")
        if codex_config_path.exists() else ""
    )
    rendered_codex = runtime_policy.codex(codex_config, runtime)

    write(home / ".codex/rules/agent-toolbox.rules", codex(values))
    write(codex_config_path, rendered_codex)
    write(home / ".gemini/policies/agent-toolbox.toml", gemini(values))
    write(settings_path, json.dumps(settings, indent=2) + "\n")


def check(values: list[str]) -> None:
    outputs = (codex(values), "\n".join(claude(values)), gemini(values))
    for value in values:
        assert all(value in output for output in outputs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="install policies under the selected home directory")
    parser.add_argument("--home", type=Path, default=Path.home(), help="installation home (default: current home)")
    args = parser.parse_args()
    values = commands()
    runtime = runtime_policy.policy(ROOT)
    check(values)
    if args.install:
        install(args.home, values, runtime)
    else:
        print("policy is valid")


if __name__ == "__main__":
    main()
