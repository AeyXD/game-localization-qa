# ติดตั้งสกิล game-localization-qa ลงโฟลเดอร์ skills ของ AI agent (Windows)
#
# ใช้งาน (จากโฟลเดอร์ repo):
#   powershell -File install.ps1                      ติดตั้งทุก agent ที่รองรับ
#   powershell -File install.ps1 -Agent claude        เฉพาะ Claude Code
#   powershell -File install.ps1 -Agent gemini        เฉพาะ Antigravity/Gemini
#   powershell -File install.ps1 -Dir "C:\skills"     ปลายทางกำหนดเอง
#
param(
  [ValidateSet("claude", "gemini", "all")]
  [string]$Agent = "all",
  [string]$Dir = ""
)

$Src = $PSScriptRoot
$Name = "game-localization-qa"
$Content = @("SKILL.md", "README.md", "LICENSE", "references", "data", "checker", "eval")

function Install-To($dest) {
  $target = Join-Path $dest $Name
  New-Item -ItemType Directory -Path $target -Force | Out-Null
  foreach ($item in $Content) {
    Copy-Item -Path (Join-Path $Src $item) -Destination $target -Recurse -Force
  }
  Write-Host "✅ ติดตั้งแล้ว: $target"
}

if ($Dir -ne "") {
  Install-To $Dir
} else {
  if ($Agent -in @("claude", "all")) { Install-To "$env:USERPROFILE\.claude\skills" }
  if ($Agent -in @("gemini", "all")) { Install-To "$env:USERPROFILE\.gemini\config\skills" }
}

Write-Host ""
Write-Host "🔍 ตรวจสอบการติดตั้ง: python3 $env:USERPROFILE\.claude\skills\$Name\checker\thai_qa.py --list-rules"
