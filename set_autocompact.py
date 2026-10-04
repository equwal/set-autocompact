"""Set a 500k-token auto-compact threshold for Claude Code and Codex on this computer.

Copilot CLI (hardcoded 95%) and Antigravity have no setting for it.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

TOKENS = 500_000
HOME = Path.home()


def save(p: Path, text: str) -> None:
    """Back up, write, then commit and push the file in its config repo."""
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        shutil.copy2(p, f"{p}.bak-autocompact")
    p.write_text(text, encoding="utf-8")
    if (p.parent / ".git").exists():
        git = ["git", "-C", str(p.parent)]
        subprocess.run([*git, "commit", "-qm", f"Set auto-compact threshold to {TOKENS} tokens", "--", p.name])
        subprocess.run([*git, "push", "-q"])
    print(f"set: {p}")


claude = HOME / ".claude" / "settings.json"
settings = json.loads(claude.read_text(encoding="utf-8")) if claude.exists() else {}
settings["autoCompactWindow"] = TOKENS
save(claude, json.dumps(settings, indent=2, ensure_ascii=False) + "\n")

# Drop any old value, then put the key first so it stays out of every [table].
codex = HOME / ".codex" / "config.toml"
toml = codex.read_text(encoding="utf-8") if codex.exists() else ""
toml = re.sub(r"(?m)^model_auto_compact_token_limit\s*=.*\n?", "", toml)
save(codex, f"model_auto_compact_token_limit = {TOKENS}\n{toml}")

print("blocked: Copilot CLI and Antigravity have no setting")
