# Command approvals

`commands.json` is the authoritative list of approved base commands. The
top-level installer installs equivalent rules for Codex, Claude Code, and
Gemini CLI. `runtime.json` defines cross-harness runtime capabilities. The
installer maps network access to Codex explicitly; Claude Code and Gemini CLI
already permit network access by default.

To install only the policies, run:

```sh
python policy/render.py --install
```

Use `--home PATH` to install into another home directory. Running the renderer
without `--install` validates the manifest and generated policies without
writing files.

These are base-command approvals, so every invocation beginning with a listed
command is approved. Review the list before installing it on another machine.
