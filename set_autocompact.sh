#!/bin/sh
# Set a 500k-token auto-compact threshold for Claude Code and Codex on this computer.
# Needs jq. Copilot CLI (hardcoded 95%) and Antigravity have no setting for it.
set -eu
TOKENS=500000

# Back up $1, replace it with $2, then commit and push it in its config repo.
save() {
  if [ -f "$1" ]; then cp "$1" "$1.bak-autocompact"; fi
  mv "$2" "$1"
  dir=$(dirname "$1")
  if [ -d "$dir/.git" ]; then
    git -C "$dir" commit -qm "Set auto-compact threshold to $TOKENS tokens" -- "$(basename "$1")" || true
    git -C "$dir" push -q || true
  fi
  echo "set: $1"
}

mkdir -p ~/.claude ~/.codex

f=~/.claude/settings.json
if [ ! -f "$f" ]; then echo '{}' > "$f"; fi
jq --indent 2 ".autoCompactWindow = $TOKENS" "$f" > "$f.tmp"
save "$f" "$f.tmp"

# Drop any old value, then put the key first so it stays out of every [table].
f=~/.codex/config.toml
{
  echo "model_auto_compact_token_limit = $TOKENS"
  if [ -f "$f" ]; then grep -v '^model_auto_compact_token_limit[[:space:]]*=' "$f" || true; fi
} > "$f.tmp"
save "$f" "$f.tmp"

echo "blocked: Copilot CLI and Antigravity have no setting"
