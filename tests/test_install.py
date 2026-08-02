#!/usr/bin/env python3
"""Minimal global installer check; run directly with Python."""

import json
import os
import subprocess
import tempfile
import tomllib
from pathlib import Path


root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    home = Path(directory)
    environment = {**os.environ, "HOME": str(home)}
    for discovery in (home / ".agents/skills", home / ".claude/skills"):
        discovery.mkdir(parents=True)
        (discovery / "stale-skill").mkdir()
    codex_config = home / ".codex/config.toml"
    codex_config.parent.mkdir(parents=True)
    codex_config.write_text(
        '[projects."/example"]\ntrust_level = "trusted"\n',
        encoding="utf-8",
    )
    subprocess.run([root / "install.sh"], env=environment, check=True)
    subprocess.run([root / "install.sh"], env=environment, check=True)

    assert (home / ".codex/AGENTS.md").resolve() == root / "AGENTS.md"
    assert (home / ".claude/CLAUDE.md").resolve() == root / "AGENTS.md"
    assert (home / ".local/bin/nk").resolve() == root / "bin/nk"
    assert (home / ".agents/skills").resolve() == root / "skills"
    assert (home / ".claude/skills").resolve() == root / "skills"
    assert not (home / ".agents/skills/stale-skill").exists()
    assert not (home / ".claude/skills/stale-skill").exists()

    settings = json.loads((home / ".claude/settings.json").read_text())
    assert "Bash(git *)" in settings["permissions"]["allow"]
    assert "Bash(./install.sh *)" in settings["permissions"]["allow"]
    assert "Bash(nk *)" in settings["permissions"]["allow"]
    installed_codex = tomllib.loads(codex_config.read_text(encoding="utf-8"))
    assert installed_codex["sandbox_mode"] == "workspace-write"
    assert installed_codex["sandbox_workspace_write"]["network_access"] is True
    assert installed_codex["projects"]["/example"]["trust_level"] == "trusted"
    subprocess.run([home / ".local/bin/nk", "--help"], env=environment, check=True)

print("installer is valid")
