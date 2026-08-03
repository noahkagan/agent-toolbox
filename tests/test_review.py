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


def add_repository(
    directory: Path, workspace: Path, candidate: dict[str, object], name: str
) -> Path:
    _bare, _checkout, base = bare_repo(directory, name)
    child = workspace / f"group/{name}"
    run("git", "clone", str(directory / f"{name}.git"), str(child), cwd=directory)
    git(child, "switch", "-c", f"candidate/{SLUG}")
    write(child / "feature.txt", "candidate\n")
    candidate_sha = commit(child, "Candidate")
    git(child, "push", "-u", "origin", f"candidate/{SLUG}")
    path = f"group/{name}"
    candidate["allowed_repositories"].append(path)
    candidate["repositories"].append(
        {
            "path": path, "target_ref": "refs/heads/main",
            "base_sha": base, "candidate_sha": candidate_sha,
        }
    )
    task_path = workspace / f"scratch/{SLUG}"
    manifest = json.loads((task_path / "task.json").read_text())
    manifest["repositories"].append(path)
    write(task_path / "task.json", json.dumps(manifest))
    write(task_path / "candidate.json", json.dumps(candidate))
    (task_path / "validation.json").unlink()
    revision = commit(workspace, "Submit multiple candidates")
    write(
        task_path / "validation.json",
        json.dumps(validation(candidate, revision, task_path / "README.md")),
    )
    commit(workspace, "Validate multiple candidates")
    git(workspace, "push", "origin", "main")
    return child


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary).resolve()
    workspace, child, candidate = world(directory)
    original_pull = task.ensure_pull_request
    original_snapshot = task.github_snapshot
    original_push = task.push_control_ref
    previous_bindings = []

    def pull_request(
        _repo: Path, _slug: str, _entry: dict[str, str], previous: object
    ) -> dict[str, object]:
        previous_bindings.append(previous)
        return binding(candidate)

    task.ensure_pull_request = pull_request
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
                "number": 7, "url": "https://github.com/example/project/pull/7",
                "baseRefName": "main", "headRefName": f"candidate/{SLUG}",
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

        task.push_control_ref = lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="lease rejected"
        )
        try:
            task.repair_review(workspace, SLUG)
        except task.PublicationError:
            pass
        else:
            raise AssertionError("repair push failure changed lifecycle")
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Review"
        assert not (workspace / f"scratch/{SLUG}/claim.json").exists()
        task.push_control_ref = original_push
        task.repair_review(workspace, SLUG)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Authoring"
        assert (workspace / f"scratch/{SLUG}/claim.json").exists()
        write(child / "feature.txt", "repaired candidate\n")
        repaired_sha = commit(child, "Repair candidate")
        git(child, "push", "--force", "origin", f"candidate/{SLUG}")
        git(workspace, "add", "group/project")
        git(workspace, "commit", "-m", "Update repaired test checkout")
        git(workspace, "push", "origin", "main")
        task.submit(workspace, SLUG, ["group/project"])
        validation_path = workspace / f"scratch/{SLUG}/validation.json"
        assert not validation_path.exists()
        try:
            task.complete(workspace, SLUG)
        except task.CoordinationError as exc:
            assert "validation.json" in str(exc)
        else:
            raise AssertionError("changed candidate reused prior validation")
        candidate = json.loads(
            (workspace / f"scratch/{SLUG}/candidate.json").read_text()
        )
        assert candidate["repositories"][0]["candidate_sha"] == repaired_sha
        revision = git(workspace, "rev-parse", "HEAD")
        write(
            validation_path,
            json.dumps(
                validation(
                    candidate, revision,
                    workspace / f"scratch/{SLUG}/README.md",
                )
            ),
        )
        git(workspace, "add", f"scratch/{SLUG}/validation.json")
        git(workspace, "commit", "-m", "Validate repaired candidate")
        git(workspace, "push", "origin", "main")
        task.complete(workspace, SLUG)
        assert previous_bindings[-1]["number"] == 7

        candidate_sha = candidate["repositories"][0]["candidate_sha"]
        task.github_snapshot = lambda _repo, _binding: {
            "metadata": {
                "number": 7, "url": "https://github.com/example/project/pull/7",
                "baseRefName": "main", "headRefName": f"candidate/{SLUG}",
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
        task.push_control_ref = lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="lease rejected"
        )
        try:
            task.reconcile_review(workspace, SLUG)
        except task.PublicationError:
            pass
        else:
            raise AssertionError("reconciliation push failure changed lifecycle")
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Review"
        task.push_control_ref = original_push
        task.reconcile_review(workspace, SLUG)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Done"
    finally:
        task.ensure_pull_request = original_pull
        task.github_snapshot = original_snapshot
        task.push_control_ref = original_push
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


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary).resolve()
    workspace, _child, candidate = world(directory)
    add_repository(directory, workspace, candidate, "project-two")
    original_pull = task.ensure_pull_request
    failed = False

    def partial_pull(
        _repo: Path, _slug: str, entry: dict[str, str], _previous: object
    ) -> dict[str, object]:
        nonlocal_failed = entry["path"] == "group/project-two" and not failed
        if nonlocal_failed:
            raise task.RemoteAccessError("second forge unavailable")
        number = 7 if entry["path"] == "group/project" else 8
        name = entry["path"].split("/")[-1]
        return {
            "path": entry["path"], "forge": "github", "owner": "example",
            "name": name, "number": number,
            "url": f"https://github.com/example/{name}/pull/{number}",
            "target_branch": "main", "source_branch": f"candidate/{SLUG}",
            "candidate_sha": entry["candidate_sha"],
        }

    task.ensure_pull_request = partial_pull
    try:
        os.environ["NK_WORKSPACE_OWNER"] = "review-test@localhost"
        try:
            task.complete(workspace, SLUG)
        except task.RemoteAccessError:
            failed = True
        else:
            raise AssertionError("partial publication did not fail")
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Authoring"
        assert (workspace / f"scratch/{SLUG}/claim.json").exists()
        assert not (workspace / f"scratch/{SLUG}/review.json").exists()
        task.complete(workspace, SLUG)
        review = task.load_review(workspace, SLUG)
        assert len(review["repositories"]) == 2
    finally:
        task.ensure_pull_request = original_pull
        os.environ.pop("NK_WORKSPACE_OWNER", None)


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary).resolve()
    workspace, _child, candidate = world(directory)
    original_pull = task.ensure_pull_request
    original_push = task.push_control_ref
    task.ensure_pull_request = lambda _repo, _slug, _entry, _previous: binding(candidate)
    task.push_control_ref = lambda *_args, **_kwargs: subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="lease rejected"
    )
    try:
        os.environ["NK_WORKSPACE_OWNER"] = "review-test@localhost"
        before = git(workspace, "rev-parse", "HEAD")
        try:
            task.complete(workspace, SLUG)
        except task.PublicationError:
            pass
        else:
            raise AssertionError("control push failure did not stop publication")
        assert git(workspace, "rev-parse", "HEAD") == before
        assert not task.changed_paths(workspace)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Authoring"
        assert (workspace / f"scratch/{SLUG}/claim.json").exists()
        assert not (workspace / f"scratch/{SLUG}/review.json").exists()
    finally:
        task.ensure_pull_request = original_pull
        task.push_control_ref = original_push
        os.environ.pop("NK_WORKSPACE_OWNER", None)


with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary).resolve()
    workspace, _child, candidate = world(directory)
    original_pull = task.ensure_pull_request
    original_push = task.push_control_ref
    task.ensure_pull_request = lambda _repo, _slug, _entry, _previous: binding(candidate)

    def accepted_with_transport_error(
        repo: Path, control: task.ControlBranch, expected: str, source: str = "HEAD"
    ) -> subprocess.CompletedProcess[str]:
        result = original_push(repo, control, expected, source)
        assert result.returncode == 0
        return subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="transport closed"
        )

    task.push_control_ref = accepted_with_transport_error
    try:
        os.environ["NK_WORKSPACE_OWNER"] = "review-test@localhost"
        task.complete(workspace, SLUG)
        buckets, _ = task.parse_todo((workspace / "TODO.md").read_text())
        assert buckets[SLUG] == "Review"
        assert not (workspace / f"scratch/{SLUG}/claim.json").exists()
    finally:
        task.ensure_pull_request = original_pull
        task.push_control_ref = original_push
        os.environ.pop("NK_WORKSPACE_OWNER", None)


original_gh = task.gh


def paginated_gh(_repo: Path, *args: str) -> object:
    if args[:2] == ("pr", "view"):
        return {}
    if any("/issues/" in arg for arg in args):
        return [[{"body": "issue discussion"}]]
    if "graphql" not in args:
        return [[]]
    query = next(arg for arg in args if arg.startswith("query="))
    if "node(id:$id)" in query:
        return [
            {"data": {"node": {"comments": {"nodes": [{"body": "first"}]}}}},
            {"data": {"node": {"comments": {"nodes": [{"body": "second"}]}}}},
        ]
    return [
        {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "id": "thread", "isResolved": False,
                                    "comments": {
                                        "nodes": [],
                                        "pageInfo": {"hasNextPage": True},
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }
    ]


try:
    task.gh = paginated_gh
    snapshot = task.github_snapshot(
        Path("."),
        {"owner": "example", "name": "project", "number": 7},
    )
    assert [
        comment["body"] for comment in snapshot["threads"][0]["comments"]["nodes"]
    ] == ["first", "second"]
    assert snapshot["comments"] == [{"body": "issue discussion"}]
finally:
    task.gh = original_gh


original_gh = task.gh
original_gh_text = task.gh_text
original_repository = task.github_repository
forge_commands = []
created = False


def forge_gh(_repo: Path, *args: str) -> object:
    forge_commands.append(args)
    if args[:2] == ("pr", "list"):
        return [{"number": 7, "state": "OPEN"}] if created else []
    if args[:2] == ("pr", "view") and args[-1] == "state":
        return {"state": "OPEN"}
    return {
        "number": 7, "url": "https://github.com/example/project/pull/7",
        "baseRefName": "main", "headRefName": f"candidate/{SLUG}",
        "headRefOid": "a" * 40,
    }


def forge_text(_repo: Path, *args: str) -> str:
    global created
    forge_commands.append(args)
    if args[:2] == ("pr", "create"):
        created = True
    return ""


try:
    task.gh = forge_gh
    task.gh_text = forge_text
    task.github_repository = lambda _repo: ("example", "project")
    candidate_entry = {
        "path": "group/project", "target_ref": "refs/heads/main",
        "candidate_sha": "a" * 40,
    }
    created_binding = task.ensure_pull_request(
        Path("."), SLUG, candidate_entry, None
    )
    assert created_binding["number"] == 7
    task.ensure_pull_request(Path("."), SLUG, candidate_entry, created_binding)
    assert sum(command[:2] == ("pr", "create") for command in forge_commands) == 1
    assert any(command[:2] == ("pr", "edit") for command in forge_commands)
    assert not any(
        command[:2] in {("pr", "merge"), ("pr", "review")}
        for command in forge_commands
    )
finally:
    task.gh = original_gh
    task.gh_text = original_gh_text
    task.github_repository = original_repository


candidate_sha = "a" * 40
base_snapshot = {
    "metadata": {
        "number": 7, "url": "https://github.com/example/project/pull/7",
        "baseRefName": "main", "headRefName": f"candidate/{SLUG}",
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
review_binding = {
    "number": 7, "url": "https://github.com/example/project/pull/7",
    "target_branch": "main", "source_branch": f"candidate/{SLUG}",
}
assert task.review_complete(base_snapshot, review_binding, candidate_sha)
for field, value in (
    ("state", "OPEN"), ("state", "CLOSED"),
    ("reviewDecision", None), ("reviewDecision", "CHANGES_REQUESTED"),
    ("headRefOid", "b" * 40),
):
    changed = json.loads(json.dumps(base_snapshot))
    changed["metadata"][field] = value
    assert not task.review_complete(changed, review_binding, candidate_sha)

changed = json.loads(json.dumps(base_snapshot))
changed["reviews"].append(
    {
        "user": {"login": "human"}, "state": "CHANGES_REQUESTED",
        "commit_id": candidate_sha,
    }
)
changed["metadata"]["reviewDecision"] = "CHANGES_REQUESTED"
assert not task.review_complete(changed, review_binding, candidate_sha)

changed = json.loads(json.dumps(base_snapshot))
changed["reviews"].append(
    {
        "user": {"login": "human"}, "state": "COMMENTED",
        "commit_id": candidate_sha,
    }
)
assert task.review_complete(changed, review_binding, candidate_sha)

for field, value in (
    ("number", 8), ("url", "https://github.com/example/project/pull/8"),
    ("baseRefName", "other"), ("headRefName", "other"),
):
    changed = json.loads(json.dumps(base_snapshot))
    changed["metadata"][field] = value
    assert not task.review_complete(changed, review_binding, candidate_sha)

print("external review lifecycle is valid")
