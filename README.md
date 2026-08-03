# agent-toolbox

Personal agent instructions, skills, and task coordination tools.
The repository keeps the same working conventions available to Codex, Claude Code,
and other agents that support the shared skills directory.

## Contents

- `AGENTS.md`: global development instructions.
- `skills/`: reusable skills for design, specifications, notes, workspaces, and task execution.
- `nk`: a CLI for workspace setup and Git-backed task coordination.

## Install

Requires a POSIX shell and Python 3.11 or later. Clone the repository, review
`AGENTS.md`, then run:

```sh
./install.sh
```

The installer links the instructions, skills, and `nk` command into your home
directory. Existing regular files at the instruction or command destinations
cause installation to stop. Existing `~/.agents/skills` and
`~/.claude/skills` paths are replaced by links to this checkout.

Ensure `~/.local/bin` is on `PATH`, then verify the installation:

```sh
nk --help
```

## Use `nk`

Initialize a Git control repository as an `nk` workspace:

```sh
cd /path/to/workspace
nk workspace init
nk workspace root
```

This creates the workspace marker, `TODO.md` task index, and `scratch/` task
artifacts directory. Run `nk task --help` for task lifecycle commands. Some task
coordination commands also require GitHub CLI access and a configured `origin`.

## Test

Run each test script directly from the repository root:

```sh
for test in tests/test_*.py; do python3 "$test"; done
```

See [Workspace conventions](skills/workspace-conventions/SKILL.md) for the
workspace and task model.
