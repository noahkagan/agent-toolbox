"""Render harness-specific runtime settings from the shared runtime policy."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


def policy(root: Path) -> dict[str, object]:
    data = json.loads((root / "runtime.json").read_text())
    if data != {"network_access": True, "writable_roots": ["/tmp"]}:
        raise ValueError("runtime policy must enable network_access and /tmp writes")
    return data


def codex(content: str, values: dict[str, object]) -> str:
    parsed = tomllib.loads(content)
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
    if headings:
        heading = headings[0]
    else:
        if lines and lines[-1]:
            lines.append("")
        lines.append("[sandbox_workspace_write]")
        heading = len(lines) - 1

    def upsert(key: str, value: str) -> None:
        start = heading + 1
        end = next(
            (index for index in range(start, len(lines)) if re.match(r"^\s*\[", lines[index])),
            len(lines),
        )
        rows = [
            index for index in range(start, end)
            if re.match(rf"^\s*{re.escape(key)}\s*=", lines[index])
        ]
        if len(rows) > 1:
            raise ValueError(f"Codex config contains duplicate {key} settings")
        if rows:
            lines[rows[0]] = f"{key} = {value}"
        else:
            lines.insert(start, f"{key} = {value}")

    sandbox = parsed.get("sandbox_workspace_write", {})
    existing_roots = sandbox.get("writable_roots", [])
    if not isinstance(existing_roots, list) or not all(isinstance(root, str) for root in existing_roots):
        raise ValueError("Codex writable_roots must be an array of strings")
    writable_roots = list(dict.fromkeys([*existing_roots, *values["writable_roots"]]))
    network_access = "true" if values["network_access"] else "false"
    upsert("network_access", network_access)
    upsert("writable_roots", json.dumps(writable_roots))
    result = "\n".join(lines) + "\n"
    tomllib.loads(result)
    return result
