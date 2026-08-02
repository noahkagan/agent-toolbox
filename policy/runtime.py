"""Render harness-specific runtime settings from the shared runtime policy."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


def policy(root: Path) -> dict[str, bool]:
    import json

    data = json.loads((root / "runtime.json").read_text())
    if data != {"network_access": True}:
        raise ValueError("runtime policy must enable network_access")
    return data


def codex(content: str, values: dict[str, bool]) -> str:
    tomllib.loads(content)
    lines = content.splitlines()
    top_level_end = next(
        (index for index, line in enumerate(lines) if re.match(r"^\s*\[", line)),
        len(lines),
    )
    sandbox_rows = [
        index for index, line in enumerate(lines[:top_level_end])
        if re.match(r"^\s*sandbox_mode\s*=", line)
    ]
    if len(sandbox_rows) > 1:
        raise ValueError("Codex config contains duplicate sandbox_mode settings")
    if sandbox_rows:
        lines[sandbox_rows[0]] = 'sandbox_mode = "workspace-write"'
    else:
        lines.insert(0, 'sandbox_mode = "workspace-write"')

    headings = [
        index for index, line in enumerate(lines)
        if re.match(r"^\s*\[sandbox_workspace_write\]\s*(?:#.*)?$", line)
    ]
    if len(headings) > 1:
        raise ValueError("Codex config contains duplicate sandbox_workspace_write tables")
    value = "true" if values["network_access"] else "false"
    if headings:
        start = headings[0] + 1
        end = next(
            (index for index in range(start, len(lines)) if re.match(r"^\s*\[", lines[index])),
            len(lines),
        )
        rows = [
            index for index in range(start, end)
            if re.match(r"^\s*network_access\s*=", lines[index])
        ]
        if len(rows) > 1:
            raise ValueError("Codex config contains duplicate network_access settings")
        if rows:
            lines[rows[0]] = f"network_access = {value}"
        else:
            lines.insert(start, f"network_access = {value}")
    else:
        if lines and lines[-1]:
            lines.append("")
        lines.extend(["[sandbox_workspace_write]", f"network_access = {value}"])
    result = "\n".join(lines) + "\n"
    tomllib.loads(result)
    return result
