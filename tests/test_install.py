#!/usr/bin/env python3
"""Minimal global installer check; run directly with Python."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    home = Path(directory)
    environment = {**os.environ, "HOME": str(home)}
    for discovery in (home / ".agents/skills", home / ".claude/skills"):
        discovery.mkdir(parents=True)
        (discovery / "stale-skill").mkdir()
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
    assert "Bash(nk *)" in settings["permissions"]["allow"]
    subprocess.run([home / ".local/bin/nk", "--help"], env=environment, check=True)

print("installer is valid")
