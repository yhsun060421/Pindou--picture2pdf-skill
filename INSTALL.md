# 安装（AI / 人类都适用）

## 给 AI 的安装指令（复制即可）

> 请把 `https://github.com/yhsun060421/--picture2pdf-skill` 克隆到
> `~/.claude/skills/bead-pattern`，执行 `pip install -r requirements.txt`，
> 运行 `python scripts/doctor.py` 确认环境，然后用 `examples/sample.png`
> 跑一遍 `--mode none` 的完整流程并校验。

## macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/yhsun060421/--picture2pdf-skill/main/install.sh | bash
```

## Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/yhsun060421/--picture2pdf-skill/main/install.ps1 | iex
```

## 手动

```bash
git clone https://github.com/yhsun060421/--picture2pdf-skill.git ~/.claude/skills/bead-pattern
pip install -r ~/.claude/skills/bead-pattern/requirements.txt
python ~/.claude/skills/bead-pattern/scripts/doctor.py
```

## 依赖

- Python 3.10+
- Chrome 或 Edge（生成 PDF）
- `Pillow`、`numpy`、`PyMuPDF`、`requests`
- 可选：图像模型 API（base URL + key）用于人物 Q 版 / 主体抠出

安装完成后重启 Claude Code，Skill 会自动被发现。
