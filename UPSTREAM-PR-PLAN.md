# แผนการ Pull Request กลับไป Upstream

> สถานะ: **ยังไม่ตัดสินใจ** — เอกสารนี้เตรียมไว้สำหรับใช้ตัดสินใจในอนาคต
> Upstream: `memolyviza2012-max/game-localization-qa`
> Fork: `AeyXD/game-localization-qa`

## หลักการ

แยกส่งเป็น PR เล็ก ๆ (ไม่รวมก้อน) เฉพาะสิ่งที่ upstream "ต้องรับ" เพราะเป็นการเพิ่มคุณค่าโดยไม่เปลี่ยนวิสัยทัศน์เดิมของเจ้าของ

---

## PR ที่ควรส่ง (content additions — upstream รับได้ง่าย)

### PR 1: เพิ่มกฎ ฎ/ฏ + คำสะกดผิด + แก้ markdown เสีย
**สิ่งที่เพิ่ม:**
- บัญชีดำ ฎ/ฏ 14 คู่ (ปรากฎ→ปรากฏ, กฏ→กฎ ฯลฯ) พร้อม scan strings
- คำทับศัพท์สะกดผิด 19 คู่ (เกมม์→เกม, เวอร์ชั่น→เวอร์ชัน, ถิ่งฐาน→ถิ่นฐาน ฯลฯ)
- กฎแก้แบบมีเงื่อนไข (ทึ่→ที่ ยกเว้น ทึ่ง/ทึ่ม)
- แก้ markdown เสีย (แบ็คทิกหลุด, indent บัญชีดำไม่สม่ำเสมอ, ตัวอย่างป้ายแนวตั้ง mismatch)
- แก้พาธส่วนตัว (C:\Users\...) → พาธแบบพกพา

**เหตุผลที่ควรรับ:** เพิ่มเนื้อหาลง SKILL.md เดิมโดยตรง ไม่แตะโครงสร้าง แก้ bug จริง (markdown/paths)

**วิธีส่ง:** Cherry-pick เฉพาะส่วน content ใส่ branch ใหม่จาก upstream/main

---

### PR 2: เพิ่ม 4 มิติ QA ที่ยังขาด (Cultural + UI Overflow + RI Transliteration + Subtitle CPS)
**สิ่งที่เพิ่ม:**
- Cultural & Sensitivity Review (rating-aware register, flag topics, กฎเหล็กห้ามแก้เอง)
- หลักเกณฑ์ทับศัพท์ราชบัณฑิตยสภา 2561 (การันต์, -tion→ชัน, ตัวสะกดท้ายคำ)
- UI Text Overflow (งบตัวอักษร 5 ระดับ, เทคนิคย่อ, วรรณยุกต์โดนตัด)
- Subtitle Timing (CPS ~15-17, 2 บรรทัด/จอ, ระยะเวลาแสดง)

**เหตุผลที่ควรรับ:** เติมช่องว่างมิติที่ LQA มืออาชีพต้องเจอ — เพิ่ม section ใหม่ในเสาหลักเดิม ไม่ขัดอะไรเดิม

---

### PR 3: หลักการแปลกลาง + Message-Type Register + System Voice
**สิ่งที่เพิ่ม:**
- หลักการแปลกลาง 8 ข้อ (แปลความ, modality, การซ้ำที่ตั้งใจ, ตัวเลือกบทสนทนา, คงมุมมองผู้พูด, ประชาสัมพันธ์, minimal-diff)
- ตาราง Message-Type Register (8 ประเภทข้อความ)
- System Voice สำหรับ UI/บทช่วยสอน (ค่าเริ่มต้น "คุณ", ห้ามบุรุษที่ 1)
- กฎเสริมเสาหลัก 1 (scene consistency, persona exception, project pronoun sheet)

**เหตุผลที่ควรรับ:** เพิ่ม value ชัดเจน ยกระดับจาก "กฎประจำเสาหลัก" เป็น "หลักการแปล" — ไม่ขัดแนวคิดเดิม

---

### PR 4 (optional): ตัวอย่างการแปลเชิงลึก
**สิ่งที่เพิ่ม:**
- คลัง transcreation 12 ตัวอย่าง (ระดับประโยค)
- ต้นแบบตัวละคร 6 ประเภท (พร้อมบทพูดตัวอย่าง)
- ตัวอย่างร้อยเรียงย่อหน้า codex 5 ประเภท

**เหตุผล:** เพิ่มตัวอย่างการสอนที่เป็นรูปธรรม — upstream อาจสนใจหรือไม่ก็ได้

---

## สิ่งที่ไม่ควร PR (เปลี่ยน architecture / เป็นความเห็นส่วนตัว)

| สิ่งที่ | เหตุผลที่ไม่ควรส่ง |
| :--- | :--- |
| Data-driven restructuring (references/ + data/) | เปลี่ยนจากไฟล์เดียวเป็นหลายไฟล์ — upstream อาจตั้งใจให้เป็นไฟล์เดียว |
| Thai QA Checker (checker/) | เพิ่ม codebase + dependency ที่ upstream ไม่ได้ขอ |
| Eval harness (eval/) | เป็นเครื่องมือภายในของ fork |
| Installers (install.sh/ps1) | เกี่ยวกับ distribution ของ fork ไม่ใช่ content |
| การเปลี่ยนนโยบาย ๆๆ (ห้าม→อนุญาต) | เป็นความเห็นเชิงส่วนตัวของผู้ดูแล fork |
| การเปลี่ยนชื่อ "กฎทหารเหมารวม" → "กฎคำพูดทหารเหมารวม" | การตั้งชื่อเป็นดุลยพินิจของเจ้าของเดิม |
| การ anonymize แหล่งที่มา | Upstream อาจต้องการระบุชัดเจนกว่า |
| CHANGELOG versioning | เป็นระบบของ fork |

---

## ขั้นตอนเมื่อตัดสินใจส่ง

```bash
# 1. เพิ่ม upstream remote
git remote add upstream https://github.com/memolyviza2012-max/game-localization-qa.git
git fetch upstream

# 2. สร้าง branch ใหม่จาก upstream/main สำหรับแต่ละ PR
git checkout -b pr/1-ronym-tor-typo-fixes upstream/main
# ... cherry-pick หรือ manually apply เฉพาะส่วน content ...
git push origin pr/1-ronym-tor-typo-fixes

# 3. เปิด PR จาก AeyXD:pr/1-ronym-tor-typo-fixes → memolyviza2012-max:main
```

หรือเปิด issue ถามก่อน:

```
Title: Interest in content contributions?

Body: (ดู ISSUE-DRAFT.md)
```
