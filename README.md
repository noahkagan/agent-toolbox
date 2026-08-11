# agent-toolbox

My opinionated toolbox for recurring needs in my agent workflows:

- Keep agent behavior consistent across tools and repositories.
- Apply repeatable methods to design, specifications, notes, and implementation.
- Preserve task context across sessions.
- Reduce review burden with clear definitions, sufficient specifications, and
  bounded structure.
- Keep durable knowledge maps current through automatic agent maintenance.

## Install

Requires a POSIX shell and Python 3.11 or later. The installer checks `PYTHON`,
then `python3` and versioned interpreters. Clone the repository, review
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
nk init
nk root
```

This creates the workspace marker, `TODO.md` task index, and `scratch/` task
directory. Run `nk task --help` for task commands.

## Test

Run each test script directly from the repository root:

```sh
for test in tests/test_*.py; do python3 "$test"; done
```

See [nk](nk/README.md) for durable tasks and
[Workspace conventions](skills/workspace-conventions/SKILL.md) for workspace
tool boundaries.
