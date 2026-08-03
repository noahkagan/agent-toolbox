#!/usr/bin/env python3
"""Workspace identity and task-root integration checks."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
nk_command = root / "bin/nk"
sys.path.insert(0, str(root))

from nk.workspace import MARKER, MARKER_CONTENT, TODO_CONTENT


def run(*args: object, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(nk_command), *(str(arg) for arg in args)],
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
    assert (workspace / MARKER).read_text() == MARKER_CONTENT
    assert (workspace / "TODO.md").read_text() == TODO_CONTENT
    assert (workspace / "scratch").is_dir()
    first = (
        (workspace / MARKER).read_bytes(),
        (workspace / "TODO.md").read_bytes(),
    )
    run("workspace", "init", workspace, cwd=temporary)
    assert first == (
        (workspace / MARKER).read_bytes(),
        (workspace / "TODO.md").read_bytes(),
    )

    task = workspace / "scratch/2026-08-01-example"
    task.mkdir()
    (task / "README.md").write_text("# Example\n")
    todo = TODO_CONTENT.replace(
        "## Ready\n",
        "## Ready\n\n- [`2026-08-01-example`](scratch/2026-08-01-example/README.md)\n",
    )
    (workspace / "TODO.md").write_text(todo)
    preserved = (workspace / "TODO.md").read_bytes()
    run("workspace", "init", workspace, cwd=temporary)
    assert (workspace / "TODO.md").read_bytes() == preserved

    child = workspace / "projects/example/child"
    child.mkdir(parents=True)
    assert run("workspace", "root", cwd=child).stdout.strip() == str(workspace.resolve())
    assert "STATUS\t2026-08-01-example\tReady" in run(
        "task", "status", "--slug", "2026-08-01-example", cwd=child
    ).stdout
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "commit", "-qm", "Initialize test workspace"],
        cwd=workspace,
        check=True,
    )
    remote = temporary / "workspace.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=workspace, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=workspace, check=True)
    subprocess.run(["git", "push", "-qu", "origin", "HEAD:main"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True,
    )
    run("task", "create", "2026-08-01-created-from-child", cwd=child)
    assert (workspace / "scratch/2026-08-01-created-from-child/README.md").is_file()
    explicit_child = run(
        "task", "status", "--workspace", child,
        "--slug", "2026-08-01-example", cwd=child, check=False,
    )
    assert explicit_child.returncode == 1
    assert "explicit workspace is not an initialized workspace root" in explicit_child.stderr

    nested = workspace / "projects/nested"
    repository(nested)
    run("workspace", "init", nested, cwd=temporary)
    nested_child = nested / "child"
    nested_child.mkdir()
    assert run("workspace", "root", cwd=nested_child).stdout.strip() == str(nested.resolve())

    other = workspace / "keep.txt"
    other.write_text("keep\n")
    run("workspace", "reset", child, cwd=temporary)
    assert other.read_text() == "keep\n"
    assert (workspace / MARKER).read_text() == MARKER_CONTENT
    assert (workspace / "TODO.md").read_text() == TODO_CONTENT
    assert not any((workspace / "scratch").iterdir())

    nested_dangling = workspace / "projects/dangling"
    nested_target = temporary / "nested-external-marker"
    repository(nested_dangling)
    (nested_dangling / MARKER.parent).mkdir()
    (nested_dangling / MARKER).symlink_to(nested_target)
    marker_before = (workspace / MARKER).read_bytes()
    todo_before = (workspace / "TODO.md").read_bytes()
    rejected = run("workspace", "reset", nested_dangling, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "unsupported workspace identity" in rejected.stderr
    assert (workspace / MARKER).read_bytes() == marker_before
    assert (workspace / "TODO.md").read_bytes() == todo_before
    assert not nested_target.exists()

    unsupported = temporary / "unsupported"
    repository(unsupported)
    (unsupported / ".nk").mkdir()
    (unsupported / MARKER).write_text("2\n")
    before = (unsupported / MARKER).read_bytes()
    rejected = run("workspace", "init", unsupported, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert (unsupported / MARKER).read_bytes() == before
    assert not (unsupported / "TODO.md").exists()
    assert not (unsupported / "scratch").exists()

    partial = temporary / "partial"
    repository(partial)
    (partial / "TODO.md").write_text(TODO_CONTENT)
    preserved = (partial / "TODO.md").read_bytes()
    run("workspace", "init", partial, cwd=temporary)
    assert (partial / "TODO.md").read_bytes() == preserved
    assert (partial / "scratch").is_dir()

    partial_scratch = temporary / "partial-scratch"
    repository(partial_scratch)
    (partial_scratch / "scratch").mkdir()
    run("workspace", "init", partial_scratch, cwd=temporary)
    assert (partial_scratch / "TODO.md").read_text() == TODO_CONTENT
    assert (partial_scratch / "scratch").is_dir()

    incomplete = temporary / "incomplete"
    repository(incomplete)
    (incomplete / MARKER.parent).mkdir()
    (incomplete / MARKER).write_text(MARKER_CONTENT)
    rejected = run("workspace", "root", incomplete, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "workspace registry is incomplete" in rejected.stderr
    run("workspace", "init", incomplete, cwd=temporary)
    assert run("workspace", "root", incomplete, cwd=temporary).stdout.strip() == str(incomplete.resolve())

    invalid = temporary / "invalid"
    repository(invalid)
    (invalid / "TODO.md").write_text("# not an nk tracker\n")
    before = (invalid / "TODO.md").read_bytes()
    rejected = run("workspace", "init", invalid, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert (invalid / "TODO.md").read_bytes() == before
    assert not (invalid / MARKER).exists()
    assert not (invalid / "scratch").exists()

    orphaned_tracker = temporary / "orphaned-tracker"
    repository(orphaned_tracker)
    (orphaned_tracker / "TODO.md").write_text(todo)
    before = (orphaned_tracker / "TODO.md").read_bytes()
    rejected = run("workspace", "init", orphaned_tracker, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "orphaned task entries" in rejected.stderr
    assert (orphaned_tracker / "TODO.md").read_bytes() == before
    assert not (orphaned_tracker / MARKER).exists()
    assert not (orphaned_tracker / "scratch").exists()

    orphaned = temporary / "orphaned"
    repository(orphaned)
    orphan = orphaned / "scratch/2026-08-01-orphan"
    orphan.mkdir(parents=True)
    (orphan / "README.md").write_text("# Orphan\n")
    rejected = run("workspace", "init", orphaned, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "orphaned task directories" in rejected.stderr
    assert not (orphaned / MARKER).exists()
    assert not (orphaned / "TODO.md").exists()

    symlinked = temporary / "symlinked"
    external = temporary / "external-scratch"
    repository(symlinked)
    external.mkdir()
    (external / "keep.txt").write_text("keep\n")
    (symlinked / MARKER.parent).mkdir()
    (symlinked / MARKER).write_text(MARKER_CONTENT)
    (symlinked / "TODO.md").write_text(TODO_CONTENT)
    (symlinked / "scratch").symlink_to(external, target_is_directory=True)
    rejected = run("workspace", "reset", symlinked, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "workspace scratch is not a directory" in rejected.stderr
    assert (symlinked / MARKER).read_text() == MARKER_CONTENT
    assert (symlinked / "TODO.md").read_text() == TODO_CONTENT
    assert (external / "keep.txt").read_text() == "keep\n"

    dangling_marker = temporary / "dangling-marker"
    marker_target = temporary / "external-marker"
    repository(dangling_marker)
    (dangling_marker / MARKER.parent).mkdir()
    (dangling_marker / MARKER).symlink_to(marker_target)
    rejected = run("workspace", "init", dangling_marker, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "unsupported workspace identity" in rejected.stderr
    assert (dangling_marker / MARKER).is_symlink()
    assert not marker_target.exists()
    assert not (dangling_marker / "TODO.md").exists()
    assert not (dangling_marker / "scratch").exists()

    dangling_todo = temporary / "dangling-todo"
    todo_target = temporary / "external-todo"
    repository(dangling_todo)
    (dangling_todo / "TODO.md").symlink_to(todo_target)
    rejected = run("workspace", "init", dangling_todo, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "workspace tracker is not a file" in rejected.stderr
    assert not todo_target.exists()
    assert not (dangling_todo / MARKER).exists()
    assert not (dangling_todo / "scratch").exists()

    dangling_scratch = temporary / "dangling-scratch"
    scratch_target = temporary / "external-scratch-target"
    repository(dangling_scratch)
    (dangling_scratch / "scratch").symlink_to(scratch_target, target_is_directory=True)
    rejected = run("workspace", "init", dangling_scratch, cwd=temporary, check=False)
    assert rejected.returncode == 1
    assert "workspace scratch is not a directory" in rejected.stderr
    assert not scratch_target.exists()
    assert not (dangling_scratch / MARKER).exists()
    assert not (dangling_scratch / "TODO.md").exists()

    outside = run("workspace", "root", temporary, cwd=temporary, check=False)
    assert outside.returncode == 1
    assert "no initialized nk workspace owns" in outside.stderr

print("workspace identity is valid")
