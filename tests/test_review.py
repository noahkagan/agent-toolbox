#!/usr/bin/env python3
"""External review lifecycle integration checks; run directly with Python."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from nk import task


SLUG = "2026-08-01-review-flow"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Review Test",
        "GIT_AUTHOR_EMAIL": "review@example.invalid",
        "GIT_COMMITTER_NAME": "Review Test",
        "GIT_COMMITTER_EMAIL": "review@example.invalid",
        "NK_WORKSPACE_OWNER": "review-test@localhost",
    }
    result = subprocess.run(
        args, cwd=cwd, env=environment, text=True, capture_output=True
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result


def git(repo: Path, *args: str) -> str:
    return run("git", *args, cwd=repo).stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def bare_repo(directory: Path, name: str) -> tuple[Path, Path, str]:
    bare = directory / f"{name}.git"
    run("git", "init", "--bare", "--initial-branch=main", str(bare), cwd=directory)
    checkout = directory / name
    run("git", "clone", str(bare), str(checkout), cwd=directory)
    write(checkout / "README.md", f"# {name}\n")
    initial = commit(checkout, "Initial")
    git(checkout, "push", "-u", "origin", "main")
    run(
        "git", "--git-dir", str(bare), "symbolic-ref", "HEAD", "refs/heads/main",
        cwd=directory,
    )
    return bare, checkout, initial


def legacy_todo(bucket: str) -> str:
    lines = ["# TODO", ""]
    for name in task.LEGACY_QUEUE_ORDER:
        lines.extend([f"## {name}", ""])
        if name == bucket:
            lines.extend([f"- [`{SLUG}`](scratch/{SLUG}/README.md)", ""])
    return "\n".join(lines)


def validation(candidate: dict[str, object], revision: str, readme: Path) -> dict[str, object]:
    return {
        "slug": SLUG,
        "candidate_digest": task.digest(candidate),
        "definition": {
            "kind": "task_plan",
            "task_revision": revision,
            "task_path": f"scratch/{SLUG}/README.md",
            "task_digest": hashlib.sha256(readme.read_bytes()).hexdigest(),
        },
        "verdict": "pass",
        "checks": [
            {
                "name": "review test",
                "repository": "group/project",
                "argv": ["python3", "tests/test_review.py"],
                "exit_status": 0,
                "started_at": "2026-08-01T00:00:00Z",
                "ended_at": "2026-08-01T00:00:01Z",
                "artifacts": [],
            }
        ],
        "agent_reviews": [
            {"name": name, "verdict": "pass", "summary": "No blockers."}
            for name in sorted(task.AGENT_REVIEW_NAMES)
        ],
    }


def world(directory: Path) -> tuple[Path, Path, dict[str, object]]:
    control_bare, workspace, _ = bare_repo(directory, "workspace")
    child_bare, child, base = bare_repo(directory, "project")
    child_target = workspace / "group/project"
    child_target.parent.mkdir(parents=True)
    run("git", "clone", str(child_bare), str(child_target), cwd=directory)
    git(child_target, "switch", "-c", f"candidate/{SLUG}")
    write(child_target / "feature.txt", "candidate\n")
    candidate_sha = commit(child_target, "Candidate")
    git(child_target, "push", "-u", "origin", f"candidate/{SLUG}")

    readme = workspace / f"scratch/{SLUG}/README.md"
    write(workspace / "TODO.md", legacy_todo("Authoring"))
    write(readme, "# Require review\n")
    write(workspace / f"scratch/{SLUG}/JOURNAL.md", "# Task Journal\n")
    write(
        workspace / f"scratch/{SLUG}/task.json",
        json.dumps(
            {
                "dependencies": [], "capabilities": {}, "resources": {},
                "repositories": ["group/project"],
            }
        ),
    )
    candidate = {
        "slug": SLUG,
        "author_owner": "review-test@localhost",
        "spec_sha": "1" * 40,
        "allowed_repositories": ["group/project"],
        "repositories": [
            {
                "path": "group/project",
                "target_ref": "refs/heads/main",
                "base_sha": base,
                "candidate_sha": candidate_sha,
            }
        ],
    }
    write(
        workspace / f"scratch/{SLUG}/claim.json",
        json.dumps(
            {
                "owner": "review-test@localhost", "claim_id": "claim",
                "spec_sha": "1" * 40, "repositories": ["group/project"],
            }
        ),
    )
    write(workspace / f"scratch/{SLUG}/candidate.json", json.dumps(candidate))
    revision = commit(workspace, "Authoring task")
    write(
        workspace / f"scratch/{SLUG}/validation.json",
        json.dumps(validation(candidate, revision, readme)),
    )
    commit(workspace, "Validate candidate")
    git(workspace, "push", "-u", "origin", "main")
    run(
        "git", "--git-dir", str(control_bare), "symbolic-ref", "HEAD", "refs/heads/main",
        cwd=directory,
    )
    return workspace, child_target, candidate


def binding(candidate: dict[str, object]) -> dict[str, object]:
    entry = candidate["repositories"][0]
    return {
        "path": "group/project", "forge": "github", "owner": "example",
        "name": "project", "number": 7, "url": "https://github.com/example/project/pull/7",
        "target_branch": "main", "source_branch": f"candidate/{SLUG}",
        "candidate_sha": entry["candidate_sha"],
    }


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary).resolve()
    workspace, child, candidate = world(directory)
    original_pull = task.ensure_pull_request
    original_snapshot = task.github_snapshot
    task.ensure_pull_request = lambda _repo, _slug, _entry, _previous: binding(candidate)
    try:
        os.environ["NK_WORKSPACE_OWNER"] = "review-test@localhost"
        target_before = task.remote_sha(child, "refs/heads/main")
        task.complete(workspace, SLUG)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Review"
        assert not (workspace / f"scratch/{SLUG}/claim.json").exists()
        assert task.remote_sha(child, "refs/heads/main") == target_before
        review = task.load_review(workspace, SLUG)
        assert review["candidate_digest"] == task.digest(candidate)

        task.github_snapshot = lambda _repo, _binding: {
            "metadata": {
                "state": "OPEN", "headRefOid": candidate["repositories"][0]["candidate_sha"],
                "reviewDecision": None,
            },
            "reviews": [], "comments": [{"body": "current discussion"}],
            "review_comments": [], "threads": [{"isResolved": False}],
        }
        output = StringIO()
        with redirect_stdout(output):
            task.inspect_review(workspace, SLUG)
        assert "current discussion" in output.getvalue()
        assert '"isResolved": false' in output.getvalue()

        task.repair_review(workspace, SLUG)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Authoring"
        assert (workspace / f"scratch/{SLUG}/claim.json").exists()
        task.complete(workspace, SLUG)

        candidate_sha = candidate["repositories"][0]["candidate_sha"]
        task.github_snapshot = lambda _repo, _binding: {
            "metadata": {
                "state": "MERGED", "headRefOid": candidate_sha,
                "reviewDecision": "APPROVED",
            },
            "reviews": [
                {
                    "user": {"login": "human"}, "state": "APPROVED",
                    "commit_id": candidate_sha,
                }
            ],
            "comments": [], "review_comments": [], "threads": [],
        }
        git(child, "push", "origin", f"{candidate_sha}:refs/heads/main")
        task.reconcile_review(workspace, SLUG)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Done"
    finally:
        task.ensure_pull_request = original_pull
        task.github_snapshot = original_snapshot
        os.environ.pop("NK_WORKSPACE_OWNER", None)


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary).resolve()
    workspace, _child, _candidate = world(directory)
    original_pull = task.ensure_pull_request
    task.ensure_pull_request = lambda *_args: (_ for _ in ()).throw(
        task.RemoteAccessError("forge unavailable")
    )
    try:
        os.environ["NK_WORKSPACE_OWNER"] = "review-test@localhost"
        try:
            task.complete(workspace, SLUG)
        except task.RemoteAccessError:
            pass
        else:
            raise AssertionError("forge failure did not stop review publication")
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Authoring"
        assert (workspace / f"scratch/{SLUG}/claim.json").exists()
        assert not (workspace / f"scratch/{SLUG}/review.json").exists()
    finally:
        task.ensure_pull_request = original_pull
        os.environ.pop("NK_WORKSPACE_OWNER", None)


candidate_sha = "a" * 40
base_snapshot = {
    "metadata": {
        "state": "MERGED", "headRefOid": candidate_sha,
        "reviewDecision": "APPROVED",
    },
    "reviews": [
        {
            "user": {"login": "human"}, "state": "APPROVED",
            "commit_id": candidate_sha,
        }
    ],
}
assert task.review_complete(base_snapshot, candidate_sha)
for field, value in (
    ("state", "OPEN"), ("reviewDecision", "CHANGES_REQUESTED"),
    ("headRefOid", "b" * 40),
):
    changed = json.loads(json.dumps(base_snapshot))
    changed["metadata"][field] = value
    assert not task.review_complete(changed, candidate_sha)

changed = json.loads(json.dumps(base_snapshot))
changed["reviews"].append(
    {
        "user": {"login": "human"}, "state": "CHANGES_REQUESTED",
        "commit_id": candidate_sha,
    }
)
assert not task.review_complete(changed, candidate_sha)

print("external review lifecycle is valid")
