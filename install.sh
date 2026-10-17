#!/usr/bin/env bash
# One-command installer for Claude Code / other agents.
set -euo pipefail

REPO="${BEAD_REPO:-https://github.com/yhsun060421/--picture2pdf-skill.git}"
DEST="${1:-$HOME/.claude/skills/bead-pattern}"

command -v git >/dev/null 2>&1 || { echo "git is required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required"; exit 1; }

mkdir -p "$(dirname "$DEST")"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  git clone --depth 1 "$REPO" "$DEST"
fi

python3 -m pip install --user -r "$DEST/requirements.txt"
python3 "$DEST/scripts/doctor.py"

echo
echo "[OK] Installed to $DEST"
echo "Restart Claude Code, then say:"
echo "   把这张图做成拼豆交互 PDF（附图片）"
