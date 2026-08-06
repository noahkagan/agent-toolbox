#!/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
  printf 'Usage: %s\n' "${0##*/}" >&2
  exit 2
fi

source_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)

find_python() {
  if [ -n "${PYTHON:-}" ]; then
    if "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
      printf '%s\n' "$PYTHON"
      return
    fi
    printf 'PYTHON must name a Python 3.11 or later interpreter.\n' >&2
    exit 1
  fi
  old_ifs=$IFS
  IFS=:
  for directory in $PATH; do
    IFS=$old_ifs
    for candidate in "$directory"/python3 "$directory"/python3.[0-9]*; do
      [ -x "$candidate" ] || continue
      if "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
        printf '%s\n' "$candidate"
        return
      fi
    done
    IFS=:
  done
  IFS=$old_ifs
  printf 'Python 3.11 or later is required. Set PYTHON to a compatible interpreter.\n' >&2
  exit 1
}

check_link() {
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    printf 'Refusing to replace existing file or directory: %s\n' "$2" >&2
    exit 1
  fi
}

check_link "$source_root/AGENTS.md" "$HOME/.codex/AGENTS.md"
check_link "$source_root/AGENTS.md" "$HOME/.claude/CLAUDE.md"
check_link "$source_root/bin/nk" "$HOME/.local/bin/nk"

# Install policies first because malformed existing settings must fail before links change.
python=$(find_python)
"$python" "$source_root/policy/render.py" --install --home "$HOME"

mkdir -p "$HOME/.local/bin" "$HOME/.agents" "$HOME/.codex" "$HOME/.claude"
ln -sfn "$source_root/AGENTS.md" "$HOME/.codex/AGENTS.md"
ln -sfn "$source_root/AGENTS.md" "$HOME/.claude/CLAUDE.md"
ln -sfn "$source_root/bin/nk" "$HOME/.local/bin/nk"
rm -rf -- "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s "$source_root/skills" "$HOME/.agents/skills"
ln -s "$source_root/skills" "$HOME/.claude/skills"

printf 'Installed agent-toolbox from %s\n' "$source_root"
