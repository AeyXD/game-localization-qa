#!/usr/bin/env bash
#
# ติดตั้งสกิล game-localization-qa ลงโฟลเดอร์ skills ของ AI agent (macOS / Linux)
#
# ใช้งาน:
#   ./install.sh                     ติดตั้งทุก agent ที่รองรับ (claude + gemini)
#   ./install.sh --agent claude      เฉพาะ Claude Code  (~/.claude/skills)
#   ./install.sh --agent gemini      เฉพาะ Antigravity/Gemini (~/.gemini/config/skills)
#   ./install.sh --dir /path/skills  ติดตั้งไปปลายทางกำหนดเอง
#
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="game-localization-qa"
CONTENT=(SKILL.md README.md LICENSE references data checker eval)

AGENT="all"
CUSTOM_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent) AGENT="$2"; shift 2 ;;
    --dir)   CUSTOM_DIR="$2"; shift 2 ;;
    -h|--help) sed -n '3,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "❌ อาร์กิวเมนต์ไม่รู้จัก: $1 (ดูวิธีใช้ด้วย -h)" >&2; exit 2 ;;
  esac
done

install_to() {
  local dest="$1"
  mkdir -p "$dest/$NAME"
  cp -R "${CONTENT[@]/#/$SRC/}" "$dest/$NAME/"
  echo "✅ ติดตั้งแล้ว: $dest/$NAME"
}

if [[ -n "$CUSTOM_DIR" ]]; then
  install_to "$CUSTOM_DIR"
else
  [[ "$AGENT" =~ ^(claude|gemini|all)$ ]] || { echo "❌ --agent รับค่า: claude | gemini | all" >&2; exit 2; }
  [[ "$AGENT" == "claude" || "$AGENT" == "all" ]] && install_to "$HOME/.claude/skills"
  [[ "$AGENT" == "gemini" || "$AGENT" == "all" ]] && install_to "$HOME/.gemini/config/skills"
fi

echo ""
echo "🔍 ตรวจสอบการติดตั้ง: python3 ~/.claude/skills/$NAME/checker/thai_qa.py --list-rules"
echo "🧪 รันชุดทดสอบ:       python3 -m unittest discover -s ~/.claude/skills/$NAME/checker"
