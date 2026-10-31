# AGENTS.md — คู่มือสำหรับ AI agent ที่ทำงานใน repo นี้

> อ่านก่อนแตะเนื้อหาทุกครั้ง · สถานะงานล่าสุดดู `.handover/HANDOVER.md` · แผนที่ ecosystem ดู `../docs/architecture.md` (workspace "THub Studio")

## repo นี้คืออะไร

Agent Skill **"7 QA Pillars"** สำหรับขัดเกลาบทแปลเกมไทย + เครื่องมือเชิงโค้ด (ปัจจุบัน v1.2.0)

| ส่วน | หน้าที่ |
|---|---|
| `SKILL.md` | 📖 คู่มือหลัก — 7 เสาหลัก + ตาราง routing ไป `references/` และ `data/` · **อ่านก่อนแตะเนื้อหา QA ทุกครั้ง** |
| `checker/thai_qa.py` | CLI ตรวจคุณภาพเชิงโค้ด (+ `test_thai_qa.py`) |
| `data/*.json` | คลังกฎ canonical เชิงเครื่อง (เป้าหมายของ self-upgrade protocol) |
| `references/` | คู่มือเชิงลึกรายเสาหลัก (7 ไฟล์) |
| `eval/` | ชุดวัดคุณภาพ: `cases.json` + `run_eval.py` |
| `UPSTREAM-PR-PLAN.md`, `ISSUE-DRAFT.md` | แผนส่ง PR กลับ upstream (สถานะ: ยังไม่ตัดสินใจ) |

## กฎเหล็ก

1. **แก้เนื้อหา QA = แก้ให้สอดคล้องทั้ง 3 ชั้น** (SKILL.md / `references/` / `data/*.json`)
   ตามตาราง routing ใน SKILL.md — ห้ามแก้ชั้นเดียวทิ้งชั้นอื่นให้ขัดแย้งกัน
2. **`data/*.json` คือของเครื่องอ่าน** — schema ต้องตรงกับที่ `checker` ใช้ และต้องผ่าน JSON validation
3. **ทดสอบก่อนส่งมอบตามที่ CI ทำ** (`.github/workflows/ci.yml` รันทุก push/PR):
   ```bash
   python3 -m unittest discover -s checker -v     # unit tests
   python3 eval/run_eval.py selftest              # eval selftest
   python3 eval/run_eval.py checker --min-coverage 95   # trap-coverage ≥ 95%
   ```
   รองรับ Python 3.9 / 3.11 / 3.12 — อย่าใช้ syntax ที่เกิน 3.9
4. **commit ใช้ conventional style** (`fix:` `docs:` `ci:` `feat:`) ตามที่ repo ใช้อยู่ ·
   งานที่ผู้ใช้เห็นต้องอัปเดต `CHANGELOG.md` ด้วย
5. **fork ↔ upstream** — push ได้เฉพาะ origin (`AeyXD/game-localization-qa`) · ส่งกลับ
   `memolyviza2012-max/game-localization-qa` ด้วย PR เท่านั้น ตามแผนใน `UPSTREAM-PR-PLAN.md`
   **⛔ ต้องรอคำสั่งเจ้าของเท่านั้น — ห้าม agent สร้าง/ส่ง/เตรียม PR เองไม่ว่ากรณีใด**
   (แม้ upstream จะตอบตกลงใน issue #1 ก็ยังต้องรอคำสั่งเจ้าของก่อนเริ่ม PR แรก) ·
   `AGENTS.md` + `.handover/` เป็นไฟล์เฉพาะ fork — ห้ามรวมใน PR กลับ upstream เด็ดขาด
6. **ขอบเขตการทำงาน** — แตะเฉพาะไฟล์ใน repo นี้ (เอกสาร workspace เป็นของ workspace task) ·
   จบ session ที่กระทบงาน → อัปเดต `.handover/HANDOVER.md` ของ repo นี้

## บทบาทในภาพรวม workspace

มีแผน (ยังไม่ลงมือ) ให้ `checker/thai_qa.py` กลายเป็นขั้น QA ใน TStudio หลังแปลก่อน deploy —
ฝั่ง THub-Launcher เป็นผู้ integrate · repo นี้ดูแลให้ CLI เสถียรและใช้งานง่ายเพื่อรองรับจุดนั้น
