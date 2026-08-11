#!/usr/bin/env python3
"""Workspace identity checks."""

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

    run("init", workspace, cwd=temporary)
    expected = """# TODO

## In Progress

## Ready

## Needs More Info

## Archived
"""
    assert (workspace / ".nk/workspace").read_text() == "1\n"
    assert (workspace / "TODO.md").read_text() == expected
    assert (workspace / "scratch").is_dir()

    before = (workspace / "TODO.md").read_bytes()
    run("init", workspace, cwd=temporary)
    assert (workspace / "TODO.md").read_bytes() == before

    child = workspace / "projects/example"
    child.mkdir(parents=True)
    assert run("root", cwd=child).stdout.strip() == str(workspace.resolve())

    help_result = run("--help", cwd=workspace)
    assert "{init,root,task}" in help_result.stdout
    assert "workspace" not in help_result.stdout

    malformed = temporary / "malformed"
    repository(malformed)
    malformed_todo = """# TODO

## Unexpected
"""
    (malformed / "TODO.md").write_text(malformed_todo)
    rejected = run("init", malformed, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "sections must appear exactly" in rejected.stderr
    assert (malformed / "TODO.md").read_text() == malformed_todo
    assert not (malformed / ".nk").exists()

    partial = temporary / "partial"
    repository(partial)
    (partial / "TODO.md").write_text(expected)
    run("init", partial, cwd=temporary)
    assert (partial / "TODO.md").read_text() == expected
    assert (partial / "scratch").is_dir()

    orphaned = temporary / "orphaned"
    repository(orphaned)
    (orphaned / "scratch/2026-08-10-orphan").mkdir(parents=True)
    rejected = run("init", orphaned, cwd=temporary, check=False)
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
    rejected = run("init", symlinked, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "workspace scratch is not a directory" in rejected.stderr
    assert (external / "keep.txt").read_text() == "keep\n"

print("workspace identity is valid")
