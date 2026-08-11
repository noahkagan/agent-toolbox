"""Initialize and resolve nk workspaces."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


MARKER = Path(".nk/workspace")
MARKER_CONTENT = "1\n"
TODO_CONTENT = """# TODO

## In Progress

## Ready

## Needs More Info

## Archived
"""


class WorkspaceError(RuntimeError):
    pass


def control_root(path: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise WorkspaceError("workspace must be a Git control repository")
    root = Path(result.stdout.strip()).resolve()
    if root != path:
        raise WorkspaceError(f"workspace must be the control repository root: {root}")
    return root


def marker_supported(root: Path) -> bool:
    identity = root / MARKER.parent
    marker = root / MARKER
    if identity.is_symlink() or (identity.exists() and not identity.is_dir()):
        raise WorkspaceError(f"unsupported workspace identity: {marker}")
    if marker.is_symlink():
        raise WorkspaceError(f"unsupported workspace identity: {marker}")
    if not marker.exists():
        return False
    if (
        not marker.is_file()
        or marker.read_text(encoding="utf-8") != MARKER_CONTENT
    ):
        raise WorkspaceError(f"unsupported workspace identity: {marker}")
    return True


def validate_registry(root: Path) -> tuple[bool, bool]:
    todo = root / "TODO.md"
    scratch = root / "scratch"
    todo_exists = todo.exists() or todo.is_symlink()
    scratch_exists = scratch.exists() or scratch.is_symlink()
    if todo_exists and (todo.is_symlink() or not todo.is_file()):
        raise WorkspaceError(f"workspace tracker is not a file: {todo}")
    if scratch_exists and (scratch.is_symlink() or not scratch.is_dir()):
        raise WorkspaceError(f"workspace scratch is not a directory: {scratch}")

    buckets: dict[str, str] = {}
    if todo_exists:
        from .task import parse_todo

        try:
            buckets = parse_todo(
                todo.read_text(encoding="utf-8"),
                root if scratch_exists else None,
            )
        except RuntimeError as exc:
            raise WorkspaceError(str(exc)) from exc
    entries = sorted(scratch.iterdir()) if scratch_exists else []
    if todo_exists and not scratch_exists and buckets:
        raise WorkspaceError("workspace tracker contains orphaned task entries")
    if scratch_exists and not todo_exists and entries:
        raise WorkspaceError("workspace scratch contains orphaned task directories")
    if todo_exists and scratch_exists:
        unexpected = [
            entry.name
            for entry in entries
            if entry.is_symlink() or not entry.is_dir() or entry.name not in buckets
        ]
        if unexpected:
            raise WorkspaceError(
                "workspace scratch contains orphaned entries: " + ", ".join(unexpected)
            )
    return todo_exists, scratch_exists


def initialize(path: Path) -> Path:
    root = control_root(path.expanduser().resolve())
    marker_supported(root)
    todo_exists, scratch_exists = validate_registry(root)
    created: list[Path] = []
    try:
        if not scratch_exists:
            scratch = root / "scratch"
            scratch.mkdir()
            created.append(scratch)
        if not todo_exists:
            todo = root / "TODO.md"
            todo.write_text(TODO_CONTENT, encoding="utf-8")
            created.append(todo)
        marker = root / MARKER
        if not marker.exists():
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(MARKER_CONTENT, encoding="utf-8")
            created.append(marker)
        validate_registry(root)
    except Exception:
        for item in reversed(created):
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink(missing_ok=True)
        marker_parent = root / MARKER.parent
        if marker_parent.exists() and not any(marker_parent.iterdir()):
            marker_parent.rmdir()
        raise
    return root


def find_root(path: Path) -> Path:
    current = path.expanduser().resolve()
    if not current.exists():
        raise WorkspaceError(f"workspace lookup path does not exist: {current}")
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if marker_supported(candidate):
            todo_exists, scratch_exists = validate_registry(candidate)
            if not todo_exists or not scratch_exists:
                raise WorkspaceError(f"workspace registry is incomplete: {candidate}")
            return candidate
    raise WorkspaceError(f"no initialized nk workspace owns: {current}")


def require_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if find_root(root) != root:
        raise WorkspaceError(f"explicit workspace is not an initialized workspace root: {root}")
    return root


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="nk workspace")
    subparsers = result.add_subparsers(dest="command", required=True)
    for name in ("init", "root"):
        command = subparsers.add_parser(name)
        command.add_argument("path", nargs="?", default=".")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    path = Path(args.path)
    try:
        if args.command == "init":
            root = initialize(path)
            print(f"INITIALIZED\t{root}")
        else:
            print(find_root(path))
    except (OSError, WorkspaceError) as exc:
        print(f"ERROR\t{exc}", file=sys.stderr)
        return 1
    return 0
