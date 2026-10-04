"""Set the auto-compact threshold to 500,000 tokens for each AI on this computer.

Claude Code and Codex have a setting. Copilot CLI (hardcoded 95%) and
Antigravity (internal compactionThreshold, no user setting) do not.
Backs up each file, then commits it in its config repo and pushes.
"""

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

TOKENS = 500_000
HOME = Path.home()
STAMP = time.strftime("%Y%m%d%H%M%S")


def read(p: Path) -> tuple[str, str]:
    """Return the text with LF endings, and the file's original line ending."""
    raw = p.read_bytes().decode("utf-8-sig") if p.exists() else ""
    return raw.replace("\r\n", "\n"), "\r\n" if "\r\n" in raw else "\n"


def write(p: Path, text: str, eol: str) -> None:
    if p.exists():
        shutil.copy2(p, p.with_name(f"{p.name}.bak-autocompact-{STAMP}"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.replace("\n", eol).encode("utf-8"))


def commit(p: Path) -> str:
    repo = p.parent
    if not (repo / ".git").exists():
        return "no repo"
    msg = f"Set auto-compact threshold to {TOKENS} tokens"
    r = subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg, "--", p.name],
                       capture_output=True, text=True)
    if r.returncode:
        return "commit failed: " + (r.stdout + r.stderr).strip().splitlines()[-1]
    if not subprocess.run(["git", "-C", str(repo), "remote"], capture_output=True, text=True).stdout.strip():
        return "committed, no remote"
    push = subprocess.run(["git", "-C", str(repo), "push", "-q"], capture_output=True, text=True)
    return "committed, pushed" if push.returncode == 0 else "committed, push failed"


def claude() -> str:
    p = HOME / ".claude" / "settings.json"
    text, eol = read(p)
    settings = json.loads(text) if text.strip() else {}
    if settings.get("autoCompactWindow") == TOKENS:
        return "already set"
    settings["autoCompactWindow"] = TOKENS
    write(p, json.dumps(settings, indent=2, ensure_ascii=False) + "\n", eol)
    return "set; " + commit(p)


def codex() -> str:
    p = HOME / ".codex" / "config.toml"
    text, eol = read(p)
    line = f"model_auto_compact_token_limit = {TOKENS}"
    key = re.compile(r"(?m)^model_auto_compact_token_limit\s*=.*$")
    if re.search(rf"(?m)^{line}\s*$", text):
        return "already set"
    # Top of file keeps the key out of any [table].
    text = key.sub(line, text, count=1) if key.search(text) else f"{line}\n{text}"
    try:
        import tomllib
        tomllib.loads(text)
    except ImportError:
        pass
    write(p, text, eol)
    return "set; " + commit(p)


for name, fn in [("Claude Code", claude), ("Codex", codex)]:
    try:
        print(f"{name}: {fn()}")
    except Exception as e:  # report each AI, never stop at the first failure
        print(f"{name}: FAILED {type(e).__name__}: {e}")
print("Copilot CLI: blocked, no setting (hardcoded 95%)")
print("Antigravity: blocked, no user setting")
