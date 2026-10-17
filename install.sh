#!/usr/bin/env bash
# One-command installer for Claude Code / other agents.
set -euo pipefail

REPO="${BEAD_REPO:-https://github.com/yhsun060421/Pindou--picture2pdf-skill.git}"
DEST="${1:-$HOME/.claude/skills/bead-pattern}"

command -v git >/dev/null 2>&1 || { echo "git is required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required"; exit 1; }

mkdir -p "$(dirname "$DEST")"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  git clone --depth 1 "$REPO" "$DEST"
fi

# Only install when a dependency is actually missing.
if ! python3 -c "import PIL, numpy, fitz, requests" >/dev/null 2>&1; then
  if ! python3 -m pip install --user -r "$DEST/requirements.txt"; then
    echo
    echo "Automatic dependency install failed."
    echo "Create a venv and install manually:"
    echo "  python3 -m venv \"$DEST/.venv\""
    echo "  \"$DEST/.venv/bin/pip\" install -r \"$DEST/requirements.txt\""
    echo "  source \"$DEST/.venv/bin/activate\""
    exit 1
  fi
fi

python3 "$DEST/scripts/doctor.py"

echo
echo "[OK] Installed to $DEST"
echo "Restart Claude Code, then say:"
echo "   把这张图做成拼豆交互 PDF（附图片）"
