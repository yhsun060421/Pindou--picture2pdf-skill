# One-command installer for Claude Code on Windows.
$ErrorActionPreference = "Stop"

$Repo = if ($env:BEAD_REPO) { $env:BEAD_REPO } else { "https://github.com/yhsun060421/--picture2pdf-skill.git" }
$Dest = if ($args.Count -ge 1) { $args[0] } else { Join-Path $HOME ".claude\skills\bead-pattern" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git is required" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "python is required" }

New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
if (Test-Path (Join-Path $Dest ".git")) {
    git -C $Dest pull --ff-only
} else {
    git clone --depth 1 $Repo $Dest
}

# Only install when a dependency is actually missing.
python -c "import PIL, numpy, fitz, requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install --user -r (Join-Path $Dest "requirements.txt")
}

python (Join-Path $Dest "scripts\doctor.py")

Write-Host ""
Write-Host "[OK] Installed to $Dest"
Write-Host "Restart Claude Code, then say: 把这张图做成拼豆交互 PDF（附图片）"
