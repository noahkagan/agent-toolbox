#!/usr/bin/env python3
"""Durable task index and document checks."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NK = ROOT / "bin/nk"


def run(*args: object, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(NK), *(str(arg) for arg in args)],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result


def state(todo: str, slug: str) -> str:
    current = ""
    for line in todo.splitlines():
        if line.startswith("## "):
            current = line[3:]
        if line.startswith(f"- [`{slug}`]"):
            return current
    raise AssertionError(f"missing task: {slug}")


with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory) / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    run("workspace", "init", cwd=workspace)

    child = workspace / "project/src"
    child.mkdir(parents=True)
    slugs = (
        "2026-08-10-first-task",
        "2026-08-10-gh-42-second-task",
        "2026-08-10-OPS-7-third-task",
        "2026-08-10-lin-9-fourth-task",
    )
    for slug in slugs:
        result = run("task", "create", slug, cwd=child)
        assert f"CREATED\t{slug}\tNeeds More Info" in result.stdout
        task = workspace / "scratch" / slug
        assert sorted(path.name for path in task.iterdir()) == ["JOURNAL.md", "README.md"]
        assert (task / "JOURNAL.md").read_text() == "# Task updates\n"

    todo = (workspace / "TODO.md").read_text()
    assert [line[3:] for line in todo.splitlines() if line.startswith("## ")] == [
        "In Progress",
        "Ready",
        "Needs More Info",
        "Archived",
    ]
    assert all(state(todo, slug) == "Needs More Info" for slug in slugs)

    first, second, third, fourth = slugs
    run("task", "move", first, "--to", "Ready", cwd=child)
    run("task", "move", first, "--to", "In Progress", cwd=child)
    run("task", "move", second, "--to", "Ready", cwd=child)
    run("task", "move", third, "--to", "Ready", cwd=child)
    run("task", "reorder", third, "--before", second, cwd=child)
    ready_lines = (workspace / "TODO.md").read_text().split("## Ready\n\n", 1)[1]
    ready_lines = ready_lines.split("\n## Needs More Info", 1)[0]
    assert ready_lines.index(third) < ready_lines.index(second)

    rejected = run(
        "task", "reorder", first, "--before", second, cwd=child, check=False
    )
    assert rejected.returncode == 1
    assert "within the same section" in rejected.stderr

    run("task", "archive", first, cwd=child)
    assert state((workspace / "TODO.md").read_text(), first) == "Archived"
    rejected = run("task", "move", first, "--to", "Ready", cwd=child, check=False)
    assert rejected.returncode == 1
    assert "must be reopened" in rejected.stderr
    run("task", "reopen", first, "--to", "Ready", cwd=child)
    run("task", "archive", first, cwd=child)
    assert state((workspace / "TODO.md").read_text(), first) == "Archived"

    status = run("task", "status", second, cwd=child)
    assert f"STATUS\t{second}\tReady" in status.stdout
    checked = run("task", "check", second, cwd=child)
    assert f"OK\t{second}\tReady" in checked.stdout

    invalid = run("task", "create", "bad-slug", cwd=child, check=False)
    assert invalid.returncode == 1
    assert "invalid task slug" in invalid.stderr
    invalid_date = run(
        "task", "create", "2026-99-99-bad-date", cwd=child, check=False
    )
    assert invalid_date.returncode == 1
    assert "invalid task slug date" in invalid_date.stderr

    journal = workspace / "scratch" / fourth / "JOURNAL.md"
    journal.write_text("# Wrong\n")
    rejected = run("task", "check", fourth, cwd=child, check=False)
    assert rejected.returncode == 1
    assert "invalid heading" in rejected.stderr

    help_result = run("task", "--help", cwd=workspace)
    assert "{create,status,check,move,archive,reopen,reorder}" in help_result.stdout
    for obsolete in ("claim", "submit", "review", "checkpoint", "block"):
        assert obsolete not in help_result.stdout

print("durable tasks are valid")
