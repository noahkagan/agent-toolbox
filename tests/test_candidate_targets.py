#!/usr/bin/env python3
"""Candidate target branch checks; run directly with Python."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from nk import task


SLUG = "2026-08-05-candidate-target"


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Candidate Test",
            "GIT_AUTHOR_EMAIL": "candidate@example.invalid",
            "GIT_COMMITTER_NAME": "Candidate Test",
            "GIT_COMMITTER_EMAIL": "candidate@example.invalid",
        },
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def git(repo: Path, *args: str) -> str:
    return run("git", *args, cwd=repo)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def setup(directory: Path) -> tuple[Path, Path]:
    control_bare = directory / "control.git"
    run("git", "init", "--bare", "--initial-branch=main", str(control_bare), cwd=directory)
    workspace = directory / "workspace"
    run("git", "clone", str(control_bare), str(workspace), cwd=directory)

    project_bare = directory / "project.git"
    run("git", "init", "--bare", "--initial-branch=main", str(project_bare), cwd=directory)
    project_source = directory / "project-source"
    run("git", "clone", str(project_bare), str(project_source), cwd=directory)
    write(project_source / "README.md", "# Project\n")
    commit(project_source, "Initial")
    git(project_source, "push", "-u", "origin", "main")
    git(project_source, "switch", "-c", "integration")
    write(project_source / "integration.txt", "integration\n")
    commit(project_source, "Integration")
    git(project_source, "push", "-u", "origin", "integration")

    project = workspace / "group/project"
    project.parent.mkdir(parents=True)
    run("git", "clone", str(project_bare), str(project), cwd=directory)
    git(project, "switch", "-c", f"candidate/{SLUG}")
    write(project / "candidate.txt", "candidate\n")
    git(project, "add", "candidate.txt")
    git(project, "commit", "-m", "Candidate")
    git(project, "push", "-u", "origin", f"candidate/{SLUG}")

    write(workspace / "TODO.md", "\n".join([
        "# TODO", "", "## Blocked", "", "## Authoring", "",
        f"- [`{SLUG}`](scratch/{SLUG}/README.md)", "", "## Review", "",
        "## Ready", "", "## Done", "", "## Backlog", "", "## Cancelled", "",
    ]))
    task_dir = workspace / f"scratch/{SLUG}"
    write(task_dir / "README.md", "# Candidate target\n")
    write(task_dir / "JOURNAL.md", "# Task Journal\n")
    write(task_dir / "task.json", json.dumps({"dependencies": [], "repositories": ["group/project"]}))
    write(task_dir / "claim.json", json.dumps({
        "owner": f"{workspace.name}@localhost", "claim_id": "claim",
        "spec_sha": "1" * 40, "repositories": ["group/project"],
    }))
    commit(workspace, "Authoring task")
    git(workspace, "push", "-u", "origin", "main")
    return workspace, project


with tempfile.TemporaryDirectory() as temporary:
    workspace, project = setup(Path(temporary))
    task.submit(workspace, SLUG, ["group/project"])
    candidate = task.load_candidate(workspace, SLUG)
    assert candidate["repositories"][0]["target_ref"] == "refs/heads/main"


with tempfile.TemporaryDirectory() as temporary:
    workspace, project = setup(Path(temporary))
    task.submit(workspace, SLUG, ["group/project"], ["group/project=integration"])
    candidate = task.load_candidate(workspace, SLUG)
    entry = candidate["repositories"][0]
    assert entry["target_ref"] == "refs/heads/integration"

    commands: list[tuple[str, ...]] = []
    state = {"created": False}
    original_json = task.gh_json
    original_text = task.gh_text
    original_repository = task.github_repository

    def gh_json(_repo: Path, *args: str) -> object:
        commands.append(args)
        if args[:2] == ("pr", "list"):
            return [{"number": 7, "state": "OPEN"}] if state["created"] else []
        return {
            "number": 7, "url": "https://github.com/example/project/pull/7",
            "baseRefName": "integration", "headRefName": f"candidate/{SLUG}",
            "headRefOid": entry["candidate_sha"],
        }

    def gh_text(_repo: Path, *args: str) -> str:
        commands.append(args)
        if args[:2] == ("pr", "create"):
            state["created"] = True
        return ""

    task.gh_json = gh_json
    task.gh_text = gh_text
    task.github_repository = lambda _repo: ("example", "project")
    try:
        task.ensure_pull_request(project, SLUG, entry, None)
    finally:
        task.gh_json = original_json
        task.gh_text = original_text
        task.github_repository = original_repository
    assert any(
        command[:2] == ("pr", "create")
        and command[command.index("--base") + 1] == "integration"
        for command in commands
    )


with tempfile.TemporaryDirectory() as temporary:
    workspace, _project = setup(Path(temporary))
    try:
        task.submit(workspace, SLUG, ["group/project"], ["group/project=missing"])
    except task.CoordinationError as exc:
        assert "not a remote branch" in str(exc)
    else:
        raise AssertionError("missing target branch was accepted")
    assert not (workspace / f"scratch/{SLUG}/candidate.json").exists()


print("candidate targets are valid")
