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
    subprocess.run([root / "install.sh"], env=environment, check=True)
    subprocess.run([root / "install.sh"], env=environment, check=True)

    assert (home / ".codex/AGENTS.md").resolve() == root / "AGENTS.md"
    assert (home / ".claude/CLAUDE.md").resolve() == root / "AGENTS.md"
    assert (home / ".local/bin/nk").resolve() == root / "bin/nk"
    for skill in (root / "skills").iterdir():
        assert (home / ".agents/skills" / skill.name).resolve() == skill
        assert (home / ".claude/skills" / skill.name).resolve() == skill

    settings = json.loads((home / ".claude/settings.json").read_text())
    assert "Bash(git *)" in settings["permissions"]["allow"]
    subprocess.run([home / ".local/bin/nk", "--help"], env=environment, check=True)

print("installer is valid")
