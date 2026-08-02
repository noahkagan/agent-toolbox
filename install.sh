#!/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
  printf 'Usage: %s\n' "${0##*/}" >&2
  exit 2
fi

source_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)

check_link() {
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    printf 'Refusing to replace existing file or directory: %s\n' "$2" >&2
    exit 1
  fi
}

check_link "$source_root/AGENTS.md" "$HOME/.codex/AGENTS.md"
check_link "$source_root/AGENTS.md" "$HOME/.claude/CLAUDE.md"
check_link "$source_root/bin/nk" "$HOME/.local/bin/nk"
for skill in "$source_root"/skills/*; do
  name=${skill##*/}
  check_link "$skill" "$HOME/.agents/skills/$name"
  check_link "$skill" "$HOME/.claude/skills/$name"
done

# Install policies first because malformed existing settings must fail before links change.
python3 "$source_root/policy/render.py" --install --home "$HOME"

mkdir -p "$HOME/.local/bin" "$HOME/.agents/skills" "$HOME/.codex" "$HOME/.claude/skills"
ln -sfn "$source_root/AGENTS.md" "$HOME/.codex/AGENTS.md"
ln -sfn "$source_root/AGENTS.md" "$HOME/.claude/CLAUDE.md"
ln -sfn "$source_root/bin/nk" "$HOME/.local/bin/nk"
for skill in "$source_root"/skills/*; do
  name=${skill##*/}
  ln -sfn "$skill" "$HOME/.agents/skills/$name"
  ln -sfn "$skill" "$HOME/.claude/skills/$name"
done

printf 'Installed agent-toolbox from %s\n' "$source_root"
