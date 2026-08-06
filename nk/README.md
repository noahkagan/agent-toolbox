# nk

`nk` owns durable task lifecycle and coordination in an initialized workspace.
It does not manage the workspace's repositories; use `meta` for that.

## Workspace data

Run `nk workspace init` at a Git control-repository root. It creates the
`.nk/workspace` marker, `TODO.md`, and `scratch/`. Resolve the owning workspace
from any descendant with `nk workspace root`.

`TODO.md` is the task index. Each entry links to one
`scratch/<slug>/README.md`. `scratch/<slug>/` contains the task specification,
journal, optional manifest, and lifecycle evidence. Create a task with
`nk task create <slug>` rather than creating those files manually.

## Slugs

Task slugs have this form:

```
YYYY-MM-DD[-gh-N|-lin-N|-PROJECT-N]-lowercase-kebab-description
```

The date and nonempty lowercase kebab-case description are required. The
optional tracker segment is a GitHub issue (`gh-N`), Linear issue (`lin-N`), or
uppercase project key and number (`PROJECT-N`).

## Lifecycle

`TODO.md` has these state buckets: `Blocked`, `Authoring`, `Review`, `Ready`,
`Done`, `Backlog`, and `Cancelled`. Use `nk task` commands to create, validate,
move, claim, submit, review, and complete tasks. Do not edit lifecycle-managed
files directly.

Run `nk task --help` for commands and `nk task <command> --help` for required
arguments. Run `nk task check --workspace <root> <slug>` to verify a task is
ready for authoring.

## Candidate targets

`nk task submit` targets each candidate pull request at its repository's remote
default branch unless told otherwise. Pass `--target REPOSITORY=BRANCH` once
per repository that needs another target. The branch must already exist on that
repository's `origin`; `nk` records it as `refs/heads/BRANCH` in
`candidate.json` and uses that recorded reference during review publication.

```sh
nk task submit --slug 2026-08-04-example --repository group/project \
  --target group/project=integration
```
