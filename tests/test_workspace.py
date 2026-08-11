#!/usr/bin/env python3
"""Workspace identity and destructive format-cutover checks."""

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


def repository(path: Path) -> None:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)


with tempfile.TemporaryDirectory() as directory:
    temporary = Path(directory)
    workspace = temporary / "workspace"
    repository(workspace)

    run("workspace", "init", workspace, cwd=temporary)
    expected = """# TODO

## In Progress

## Ready

## Needs More Info

## Done

## Cancelled
"""
    assert (workspace / ".nk/workspace").read_text() == "1\n"
    assert (workspace / "TODO.md").read_text() == expected
    assert (workspace / "scratch").is_dir()

    before = (workspace / "TODO.md").read_bytes()
    run("workspace", "init", workspace, cwd=temporary)
    assert (workspace / "TODO.md").read_bytes() == before

    child = workspace / "projects/example"
    child.mkdir(parents=True)
    assert run("workspace", "root", cwd=child).stdout.strip() == str(workspace.resolve())

    help_result = run("workspace", "--help", cwd=workspace)
    assert "reset" not in help_result.stdout

    legacy = temporary / "legacy"
    repository(legacy)
    legacy_todo = """# TODO

## Blocked

## Authoring

## Review

## Ready

## Done

## Backlog

## Cancelled
"""
    (legacy / "TODO.md").write_text(legacy_todo)
    rejected = run("workspace", "init", legacy, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "sections must appear exactly" in rejected.stderr
    assert (legacy / "TODO.md").read_text() == legacy_todo
    assert not (legacy / ".nk").exists()

    partial = temporary / "partial"
    repository(partial)
    (partial / "TODO.md").write_text(expected)
    run("workspace", "init", partial, cwd=temporary)
    assert (partial / "TODO.md").read_text() == expected
    assert (partial / "scratch").is_dir()

    orphaned = temporary / "orphaned"
    repository(orphaned)
    (orphaned / "scratch/2026-08-10-orphan").mkdir(parents=True)
    rejected = run("workspace", "init", orphaned, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "orphaned task directories" in rejected.stderr
    assert not (orphaned / "TODO.md").exists()

    symlinked = temporary / "symlinked"
    external = temporary / "external"
    repository(symlinked)
    external.mkdir()
    (external / "keep.txt").write_text("keep\n")
    (symlinked / "TODO.md").write_text(expected)
    (symlinked / "scratch").symlink_to(external, target_is_directory=True)
    rejected = run("workspace", "init", symlinked, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "workspace scratch is not a directory" in rejected.stderr
    assert (external / "keep.txt").read_text() == "keep\n"

print("workspace identity is valid")
