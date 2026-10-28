# Changelog

รูปแบบเวอร์ชัน: **MAJOR.MINOR.PATCH** — เพิ่มกฎ/ข้อมูลใน data = PATCH · เพิ่มความสามารถ/เอกสาร/เครื่องมือ = MINOR · เปลี่ยน schema หรือโครงสร้างที่ใช้งานไม่เข้ากัน = MAJOR

## [1.1.0] — 2026-10-28

### Added — สถาปัตยกรรมและเครื่องมือ
- **Data-driven architecture + Progressive Disclosure:** แยก SKILL.md (429 บรรทัด) เป็นแกนกลาง 115 บรรทัด + `references/` 7 ไฟล์รายเสาหลัก + `data/` 6 ไฟล์ JSON เป็น canonical ของการอัปเกรด (mt-traps 99 รายการ, transliteration, pronouns, thai-orthography, cjk-residue, sound-cues)
- **Thai QA Checker** (`checker/thai_qa.py`): สแกน/แก้ไฟล์แปลอัตโนมัติแบบไม่มี dependency (stdlib ล้วน) — วรรณยุกต์/สระลอย, ฎ/ฏ, ๆ, CJK, ผสานคำ, กับดัก MT, โหมด CSV ตรวจบทหลุด + ความปลอดภัยไฟล์ (BOM/newline/line-count/atomic write) พร้อมชุดทดสอบ 33 เคส
- **Eval Set & Harness** (`eval/`): 50 เคสครบ 7 เสาหลัก + เครื่องวัด coverage (regression net) และ A/B grading — baseline coverage 100%
- **เนื้อหา 4 มิติใหม่:** Cultural & Sensitivity Review (เสา 2), หลักเกณฑ์ทับศัพท์ราชบัณฑิตยสภา 2561 (เสา 3), UI Text Overflow + Subtitle Timing/CPS (เสา 6) พร้อมคู่คำแก้อัตโนมัติ (เกมม์→เกม, เวอร์ชั่น→เวอร์ชัน ฯลฯ)
- **Installer:** `install.sh` (macOS/Linux) และ `install.ps1` (Windows) ติดตั้งทั้งโฟลเดอร์สู่ Claude Code / Antigravity ด้วยคำสั่งเดียว

### Added — กฎภาษาไทยใหม่
- บัญชีดำ ฎ/ฏ (ปรากฎ→ปรากฏ, กฏ→กฎ พร้อม scan strings แบบ zero false positive)
- กฎไม้ยมก (ๆ): เว้นวรรคก่อน-หลัง, ห้ามซ้อน ๆๆ, ห้าม ๆ โดดเดี่ยวต้นบรรทัด

### Fixed
- ลบพาธส่วนตัวของผู้เขียนเดิม (C:\Users\..., E:\...) และเพิ่มคู่มือติดตั้ง macOS/Linux/Windows ครบ
- แก้ markdown เสีย (แบ็คทิกหลุด, ย่อหน้าบัญชีดำไม่สม่ำเสมอ, ตัวอย่างป้ายแนวตั้งก่อน-หลังไม่ใช่คำเดียวกัน)
- แก้ typo ในคลังข้อมูลเองที่ eval จับได้ (ประหลาย→ประหลาด) และกัน bug กฎแทนที่ทับซ้อน (ปรากฏโดนกฎ กฏ→กฎ ทำลายกลับ)

## [1.0.0] — 2026-10-16

- Initial release: Game Localization QA & Translation Polish Master Protocol (The 7 QA Pillars) — ไฟล์ SKILL.md เดี่ยว 429 บรรทัด + README + MIT License
