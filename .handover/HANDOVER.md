# HANDOVER — game-localization-qa

**snapshot:** 2026-10-31 (อัปเดตโดย agent session หลัง commit AGENTS.md + .handover/)
**สถานะ git:** `main` สะอาด sync origin · v1.2.0 · `AGENTS.md` + `.handover/` track ใน repo แล้ว (fork-only)

## งานค้าง (สำคัญที่สุดของ repo นี้)

1. **รอคำสั่งเจ้าของก่อนเริ่ม PR กลับ upstream — ห้าม agent เริ่มเอง** (กฎ ⛔ ใน AGENTS.md ข้อ 5)
   - แผนพร้อมแล้วแบ่งเป็น 4 PR ตามลำดับ dependency ใน `UPSTREAM-PR-PLAN.md`
   - ฉบับที่เสนอให้ upstream อ่านอยู่ที่ `ISSUE-DRAFT.md` (ภาษาไทย)
   - สถานะปัจจุบัน (ตรวจ 2026-10-31): **เปิด issue ถาม upstream แล้ว** —
     [upstream issue #1](https://github.com/memolyviza2012-max/game-localization-qa/issues/1)
     "ถามเรื่องการส่ง PR กลับมาครับ..." (เปิด 30/10/2026 08:09 โดย AeyXD) · **OPEN, ยังไม่มีคอมเมนต์ตอบ**
     → แม้ upstream ตอบตกลง ก็ยังต้องรอคำสั่งเจ้าของอีกชั้นก่อนเริ่ม PR แรก
     (สร้าง branch จาก `upstream/main` ตามคำสั่งในแผน ไม่ใช่จาก main ของ fork ·
     `AGENTS.md` + `.handover/` เป็นไฟล์เฉพาะ fork ห้ามรวมใน PR กลับ upstream เด็ดขาด)
   - สถานะ remote + divergence (ตรวจ 2026-10-30): เพิ่ม remote `upstream`
     (https://github.com/memolyviza2012-max/game-localization-qa) แล้ว ·
     **fork นำหน้า 33 commits / ตามหลัง 0** — upstream นิ่งตั้งแต่จุด fork
   - โครงสร้างเราต่างจาก upstream โดยตั้งใจ: upstream = `SKILL.md` เดี่ยว 429 บรรทัด ·
     เรา = `SKILL.md` 120 บรรทัด (router) + `references/` + `data/` รวม ~2,793 บรรทัด →
     ทุก PR ต้อง "แปลงกลับ" เนื้อหาเข้ารูปแบบไฟล์เดียวของ upstream (แผนกำหนดไว้แล้ว)
2. **งานเสริมจากสเปก QA bridge: เสร็จทั้งชุด 31/10** ✅
   - exit-code convention: พบว่า behavior จริงไม่ตรงสเปก (error paths เดิมออกรหัส 1 ปนกับ
     "พบจุดเตือน") จึงแก้ checker ให้ออก 2 + README + CHANGELOG — ผลพลอยได้ฝั่ง TStudio:
     checker พังจะถูก bridge ตีเป็น "รันไม่สำเร็จ" ถูกต้อง (เดิม exit 1 ทำให้เข้าใจว่ารันผ่าน)
   - flag `--json`: พิมพ์สรุป structured (สรุปรวม/รายไฟล์/issues รายจุด/unknown_rules)
     แทนข้อความคนอ่าน — ฝั่ง TStudio bridge สลับจาก parse บรรทัด "รวม:" มาใช้ได้ (optional
     ไม่บังคับ ระบบเดิมก็ยังใช้ได้) · tests 64/64 · eval ผ่านครบ

## 📨 แจ้งต่อ workspace task → โปรดส่งต่อ THub-Launcher task (พบ 31/10 ค่ำ)

**Bug: dialog ผล QA เปิดไม่ได้ — `QHBoxLayout` ไม่ถูก import (NameError ตอน runtime)**

- **ไฟล์/จุด:** `THub-Launcher/tools/flagship/TStudio/tstudio_qa_bridge.py:125`
  (`btn_row = QHBoxLayout()`) แต่รายการ import `PyQt6.QtWidgets` (บรรทัด 15–18)
  ไม่มี `QHBoxLayout` — grep ทั้งไฟล์ยืนยัน คำนี้ปรากฏจุดเดียวคือจุดใช้งาน
- **อาการ:** กดเมนู Tools → ตรวจ QA คำแปล (dry-run) → `QaResultDialog` สร้างไม่ผ่าน
  (จุดเรียก `tstudio_app.py:5361` ไม่มี try/except ครอบ) → หน้าต่างผลไม่ขึ้น
- **ยังทำงานปกติ:** checker subprocess · เส้นทาง `--fix` (ไม่สร้าง dialog) ·
  QA gate ก่อน deploy (เรียก `run_checker` ตรง ๆ)
- **วิธีแก้ (บรรทัดเดียว):** เพิ่ม `QHBoxLayout` เข้ารายการ import บรรทัด 15–18
- **ผลกระทบต่อ acceptance:** ข้อ 1 ของ `docs/spec-qa-bridge.md`
  (โหลด `development/tests/tstudio_test.csv` → เห็นสรุป 3 จุด) จะไม่ผ่าน —
  แปลว่ายังไม่เคยรัน acceptance หลังแก้โค้ดรอบสุดท้าย ควรรันให้ครบ 4 ข้อหลังแก้
- **ที่มา:** GLQA task ทวน bridge ตามบทบาท "ยืนยัน contract" ในสเปก —
  ไม่แตะ working tree ของ THub-Launcher ตามกฎ hub-and-spoke จึงรายงานช่องทางนี้

## สิ่งที่ทำล่าสุด (ก่อน snapshot นี้)

- **2026-10-31 ค่ำ:** ทวน QA bridge หลัง THub-Launcher integrate เสร็จ (`2b2d8c6`) —
  contract ใช้ถูกต้องตามสเปกทั้งหมด แต่พบ bug dialog → รายงานไว้หัวข้อ "แจ้งต่อ" ข้างบน
- **2026-10-31:** เจ้าของสั่ง commit `AGENTS.md` + `.handover/` เข้า repo (แบบเดียวกับ THub-Launcher)
  พร้อมเสริมกฎ ⛔ ลง AGENTS.md ข้อ 5 (รอคำสั่งเจ้าของเท่านั้น + ไฟล์ fork-only) — push origin แล้ว
- ทยอยขัดเกลาเอกสาร upstream-PR จนครบชุด: แปล issue draft เป็นไทย → ลดความยาว →
  จัดโครง 4 PR → เพิ่มตัวอย่างจริงทุกหัวข้อ → fix typo ถ่ายทอบ→ถ่ายทอด
- CI ครบชุด: tests + eval + JSON validation ทุก push/PR

## วิธีทดสอบ (ตรงกับ CI)

```bash
python3 -m unittest discover -s checker -v
python3 eval/run_eval.py selftest
python3 eval/run_eval.py checker --min-coverage 95
```
