#!/usr/bin/env python3
"""Manage durable tasks in an nk workspace."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from . import workspace as workspace_registry


ACTIVE_STATES = ("In Progress", "Ready", "Needs More Info")
ARCHIVE_STATES = ("Done", "Cancelled")
QUEUE_ORDER = (*ACTIVE_STATES, *ARCHIVE_STATES)
TASK_RE = re.compile(r"^- \[`([^`]+)`\]\((scratch/[^)]+/README\.md)\)$")
SLUG_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-"
    r"(?:(?:gh|lin)-\d+-|(?:[A-Z][A-Z0-9]+-\d+)-)?"
    r"[a-z0-9]+(?:-[a-z0-9]+)*$"
)


class TaskError(RuntimeError):
    pass


def parse_todo(text: str, workspace: Path | None = None) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "# TODO":
        raise TaskError("TODO.md must begin with '# TODO'")

    headings = [line[3:] for line in lines if line.startswith("## ")]
    if headings != list(QUEUE_ORDER):
        expected = ", ".join(QUEUE_ORDER)
        raise TaskError(f"TODO.md sections must appear exactly as: {expected}")

    buckets: dict[str, str] = {}
    current: str | None = None
    for line in lines[1:]:
        if not line:
            continue
        if line.startswith("## "):
            current = line[3:]
            continue
        if line.startswith("#"):
            raise TaskError(f"unsupported TODO.md heading: {line}")
        if current is None:
            raise TaskError(f"task entry appears before a state: {line}")
        match = TASK_RE.fullmatch(line)
        if match is None:
            raise TaskError(f"unsupported TODO.md content: {line}")
        slug, relative = match.groups()
        validate_slug(slug)
        expected_path = f"scratch/{slug}/README.md"
        if relative != expected_path:
            raise TaskError(f"task link does not match its slug: {line}")
        if slug in buckets:
            raise TaskError(f"duplicate task in TODO.md: {slug}")
        if workspace is not None:
            readme = workspace / relative
            task_root = readme.parent
            if task_root.is_symlink() or not task_root.is_dir():
                raise TaskError(f"task directory is unavailable: {task_root}")
            if readme.is_symlink() or not readme.is_file():
                raise TaskError(f"task definition is unavailable: {readme}")
        buckets[slug] = current
    return buckets


def render_todo(grouped: dict[str, list[str]]) -> str:
    lines = ["# TODO", ""]
    for state in QUEUE_ORDER:
        lines.append(f"## {state}")
        lines.append("")
        lines.extend(
            f"- [`{slug}`](scratch/{slug}/README.md)"
            for slug in grouped[state]
        )
        if grouped[state]:
            lines.append("")
    return "\n".join(lines)


def validate_slug(slug: str) -> None:
    match = SLUG_RE.fullmatch(slug)
    if match is None:
        raise TaskError(f"invalid task slug: {slug}")
    try:
        date.fromisoformat(match.group("date"))
    except ValueError as exc:
        raise TaskError(f"invalid task slug date: {slug}") from exc


def task_dir(workspace: Path, slug: str) -> Path:
    return workspace / "scratch" / slug


def tracker(workspace: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    buckets = parse_todo(
        (workspace / "TODO.md").read_text(encoding="utf-8"), workspace
    )
    grouped = {state: [] for state in QUEUE_ORDER}
    for slug, state in buckets.items():
        grouped[state].append(slug)
    return buckets, grouped


def write_tracker(workspace: Path, grouped: dict[str, list[str]]) -> None:
    (workspace / "TODO.md").write_text(render_todo(grouped), encoding="utf-8")


def validate_task(workspace: Path, slug: str) -> str:
    validate_slug(slug)
    buckets, _ = tracker(workspace)
    if slug not in buckets:
        raise TaskError(f"unknown task: {slug}")
    root = task_dir(workspace, slug)
    if root.is_symlink() or not root.is_dir():
        raise TaskError(f"task directory is unavailable: {root}")
    for name, heading in (("README.md", "# "), ("JOURNAL.md", "# Task updates")):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise TaskError(f"task file is unavailable: {path}")
        content = path.read_text(encoding="utf-8")
        if not content.strip() or not content.startswith(heading):
            raise TaskError(f"task file has an invalid heading: {path}")
    return buckets[slug]


def create(workspace: Path, slug: str) -> None:
    validate_slug(slug)
    buckets, grouped = tracker(workspace)
    root = task_dir(workspace, slug)
    if slug in buckets or root.exists() or root.is_symlink():
        raise TaskError(f"task already exists: {slug}")
    root.mkdir()
    try:
        (root / "README.md").write_text(
            f"# {slug}\n\n"
            "## Outcome\n\n"
            "??? Define the smallest observable outcome.\n\n"
            "## Context\n\n"
            "??? Link the canonical notes needed to understand this task.\n",
            encoding="utf-8",
        )
        (root / "JOURNAL.md").write_text("# Task updates\n", encoding="utf-8")
        grouped["Needs More Info"].append(slug)
        write_tracker(workspace, grouped)
    except Exception:
        for path in root.iterdir():
            path.unlink()
        root.rmdir()
        raise
    print(f"CREATED\t{slug}\tNeeds More Info")


def status(workspace: Path, slug: str) -> None:
    state = validate_task(workspace, slug)
    print(f"STATUS\t{slug}\t{state}")


def check(workspace: Path, slug: str) -> None:
    state = validate_task(workspace, slug)
    print(f"OK\t{slug}\t{state}")


def move(workspace: Path, slug: str, target: str) -> None:
    source = validate_task(workspace, slug)
    if source in ARCHIVE_STATES:
        raise TaskError(f"archived task must be reopened: {slug}")
    if target not in ACTIVE_STATES:
        raise TaskError(f"invalid active state: {target}")
    if source == target:
        print(f"MOVED\t{slug}\t{target}")
        return
    _, grouped = tracker(workspace)
    grouped[source].remove(slug)
    grouped[target].append(slug)
    write_tracker(workspace, grouped)
    print(f"MOVED\t{slug}\t{target}")


def archive(workspace: Path, slug: str, disposition: str) -> None:
    source = validate_task(workspace, slug)
    if source in ARCHIVE_STATES:
        raise TaskError(f"task is already archived: {slug}")
    if disposition not in ("done", "cancelled"):
        raise TaskError(f"invalid archive disposition: {disposition}")
    target = {"done": "Done", "cancelled": "Cancelled"}[disposition]
    _, grouped = tracker(workspace)
    grouped[source].remove(slug)
    grouped[target].append(slug)
    write_tracker(workspace, grouped)
    print(f"ARCHIVED\t{slug}\t{target}")


def reopen(workspace: Path, slug: str, target: str) -> None:
    source = validate_task(workspace, slug)
    if source not in ARCHIVE_STATES:
        raise TaskError(f"task is not archived: {slug}")
    if target not in ACTIVE_STATES:
        raise TaskError(f"invalid active state: {target}")
    _, grouped = tracker(workspace)
    grouped[source].remove(slug)
    grouped[target].append(slug)
    write_tracker(workspace, grouped)
    print(f"REOPENED\t{slug}\t{target}")


def reorder(workspace: Path, slug: str, peer: str, before: bool) -> None:
    if slug == peer:
        raise TaskError("task and reorder peer must differ")
    source = validate_task(workspace, slug)
    peer_state = validate_task(workspace, peer)
    if source != peer_state:
        raise TaskError("tasks can only be reordered within the same section")
    _, grouped = tracker(workspace)
    entries = grouped[source]
    entries.remove(slug)
    index = entries.index(peer)
    entries.insert(index if before else index + 1, slug)
    write_tracker(workspace, grouped)
    relation = "before" if before else "after"
    print(f"REORDERED\t{slug}\t{relation}\t{peer}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    command = subparsers.add_parser("create")
    command.add_argument("slug")
    command.add_argument("--workspace")

    for name in ("status", "check"):
        command = subparsers.add_parser(name)
        command.add_argument("slug")
        command.add_argument("--workspace")

    command = subparsers.add_parser("move")
    command.add_argument("slug")
    command.add_argument("--workspace")
    command.add_argument("--to", choices=ACTIVE_STATES, required=True)

    command = subparsers.add_parser("archive")
    command.add_argument("slug")
    command.add_argument("--workspace")
    command.add_argument("--as", dest="disposition", choices=("done", "cancelled"), required=True)

    command = subparsers.add_parser("reopen")
    command.add_argument("slug")
    command.add_argument("--workspace")
    command.add_argument("--to", choices=ACTIVE_STATES, required=True)

    command = subparsers.add_parser("reorder")
    command.add_argument("slug")
    command.add_argument("--workspace")
    order = command.add_mutually_exclusive_group(required=True)
    order.add_argument("--before")
    order.add_argument("--after")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        workspace = (
            workspace_registry.require_root(Path(args.workspace))
            if args.workspace is not None
            else workspace_registry.find_root(Path.cwd())
        )
        if args.command == "create":
            create(workspace, args.slug)
        elif args.command == "status":
            status(workspace, args.slug)
        elif args.command == "check":
            check(workspace, args.slug)
        elif args.command == "move":
            move(workspace, args.slug, args.to)
        elif args.command == "archive":
            archive(workspace, args.slug, args.disposition)
        elif args.command == "reopen":
            reopen(workspace, args.slug, args.to)
        else:
            reorder(
                workspace,
                args.slug,
                args.before or args.after,
                args.before is not None,
            )
    except (OSError, TaskError, workspace_registry.WorkspaceError) as exc:
        print(f"ERROR\t{exc}", file=sys.stderr)
        return 1
    return 0
