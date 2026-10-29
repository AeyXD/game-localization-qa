# แผนการ Pull Request กลับไป Upstream

> สถานะ: **ยังไม่ตัดสินใจ** — เอกสารนี้เป็นคู่มือปฏิบัติสำหรับเมื่อ upstream ตอบตกลง
> ฉบับที่ส่งให้ upstream อ่าน: `ISSUE-DRAFT.md`
> Upstream: `memolyviza2012-max/game-localization-qa`
> Fork: `AeyXD/game-localization-qa`

## หลักการ

ส่งเป็น 4 PR แยกกัน ทีละอัน (รอ merge แล้วค่อยส่งถัดไป) เพราะทุก PR แก้ไฟล์ SKILL.md ไฟล์เดียวกัน ส่งพร้อมกันจะ conflict

---

## ภาพรวม 4 PR

| PR | หัวข้อ | Dependency | สามารถสลับลำดับ? |
| :--- | :--- | :--- | :--- |
| 1 | Bug fixes + กฎตรวจคำสะกดผิด | ไม่มี | สลับกับ PR 2 ได้ |
| 2 | เนื้อหาใหม่ 4 เรื่อง | ไม่มี | สลับกับ PR 1 ได้ |
| 3 | หลักการแปล + System Voice | อ้าง PR 2 เล็กน้อย (soft) | ควรหลัง PR 2 |
| 4 | ตัวอย่างการแปลเชิงลึก | อ้าง PR 3 (แนวคิด transcreation) | ส่งหลังสุด |

---

## PR 1: Bug fixes + กฎตรวจคำสะกดผิด

### เนื้อหา
- Markdown เสีย 3 จุด (แบ็คทิกหลุด, ย่อหน้าบัญชีดำ, ตัวอย่างป้ายแนวตั้ง mismatch)
- พาธ Windows ส่วนตัว → พาธแบบพกพา
- ฎ/ฏ 14 คู่
- คำทับศัพท์สะกดผิด 19 คำ (ราชบัณฑิตยสภา 2561)
- กฎแก้แบบมีเงื่อนไข (ทึ่→ที่ ยกเว้น ทึ่ง/ทึ่ม)
- ๆ ครบชุด (เว้นวรรค, รวม "ๆ ๆ"→"ๆๆ", เสียงหัวเราะเต็มคำ, ลากเสียง า)
- คู่คำจากงานแปลจริง 7 คำ (ไฝ่→ใฝ่, เวทย์→เวท ฯลฯ)

### วิธีสร้าง branch
```bash
# สร้าง branch ใหม่จาก upstream/main
git checkout -b pr/1-typo-fixes-and-spelling upstream/main

# เนื้อหามาจาก (ใน fork ของเรา):
# - data/thai-orthography.json → ror_tor_confusion, common_misspellings, conditional_fixes, mai_yamok
# - แปลงกลับเป็นรูปแบบ SKILL.md เดียว (เพิ่มเข้าหัวข้อบัญชีดำของแต่ละเสาหลัก)
# - Bug fixes: แก้โดยตรงใน markdown ของ SKILL.md
```

---

## PR 2: เนื้อหาใหม่ 4 เรื่อง

### เนื้อหา
| เรื่อง | เพิ่มที่ไหน | แปลงจากไฟล์ไหนใน fork |
|---|---|---|
| Cultural & Sensitivity Review | เสาหลัก 2 (หัวข้อใหม่) | `references/pillar-2-context-tone.md` ส่วนที่ 3 |
| หลักเกณฑ์ทับศัพท์ราชบัณฑิตยสภา 2561 | เสาหลัก 3 (หัวข้อใหม่) | `references/pillar-3-skills-spells.md` ส่วนที่ 5 |
| UI Text Overflow | เสาหลัก 6 (หัวข้อใหม่) | `references/pillar-6-leak-typography.md` |
| Subtitle CPS | เสาหลัก 6 (หัวข้อใหม่) | `references/pillar-6-leak-typography.md` |

### วิธีสร้าง branch
```bash
git checkout -b pr/2-new-dimensions upstream/main
# คัดเนื้อหาจาก reference files → แปลงเป็นหัวข้อใหม่ใน SKILL.md
# ไม่แก้ของเดิม เพิ่ม section ใหม่ล้วน
```

---

## PR 3: หลักการแปล + System Voice

### เนื้อหา
- หลักการแปลกลาง 6 ข้อ (เสาหลัก 2)
- Message-Type Register 8 ประเภท (เสาหลัก 2)
- System Voice: คุณ สำหรับ UI + ห้ามบุรุษที่ 1 (เสาหลัก 1)
- ความสม่ำเสมอระดับฉาก + persona exception (เสาหลัก 1)
- เฟรมเวิร์กตัดสินชื่อไอเท็มแฟนตาซี (เสาหลัก 4)
- `[DEBUG]` ไม่ต้องแปล + `ป.ล.` (เสาหลัก 6)
- Checklist ตรวจก่อนส่งมอบ 10 ข้อ (หัวข้อใหม่ท้ายไฟล์)

### วิธีสร้าง branch
```bash
git checkout -b pr/3-principles-and-system-voice upstream/main
# คัดจาก: references/pillar-2 (ส่วน 4-5), references/pillar-1 (ส่วน 3-4),
#          references/pillar-4 (ส่วน 5), references/qa-checklist.md
# อ้างถึง PR 2 เรื่องหลักเกณฑ์ทับศัพท์ (soft dependency)
```

---

## PR 4: ตัวอย่างการแปลเชิงลึก

### เนื้อหา
- ตัวอย่างขัดเกลาระดับประโยค 12 คู่ (จาก `data/transcreation.json`)
- ต้นแบบเสียงตัวละคร 6 ประเภท + บทพูด 24 บรรทัด (จาก `data/persona-archetypes.json`)
- ตัวอย่างร้อยเรียงย่อหน้า 5 ประเภท (จาก `data/codex-weaving.json`)
- แนบท้าย SKILL.md เป็น appendix หรือ section ใหม่

### วิธีสร้าง branch
```bash
git checkout -b pr/4-examples upstream/main
# แปลง JSON เป็นรูปแบบ markdown ตาราง ใส่ท้าย SKILL.md
# อ้างถึงแนวคิดจาก PR 3 (transcreation techniques)
```

---

## สิ่งที่ไม่ PR (เปลี่ยนโครงสร้าง / เป็นความเห็นส่วนตัว)

| สิ่งที่ | เหตุผล |
| :--- | :--- |
| Data-driven restructuring (references/ + data/) | เปลี่ยนจากไฟล์เดียวเป็นหลายไฟล์ — upstream อาจตั้งใจให้เป็นไฟล์เดียว |
| Thai QA Checker (checker/) | เพิ่ม codebase + dependency ที่ upstream ไม่ได้ขอ |
| Eval harness (eval/) | เป็นเครื่องมือภายในของ fork |
| Installers (install.sh/ps1) | เกี่ยวกับ distribution ของ fork |
| การเปลี่ยนนโยบาย ๆๆ (ห้าม→อนุญาต) | เป็นความเห็นเชิงส่วนตัวของผู้ดูแล fork |
| การเปลี่ยนชื่อ "กฎทหารเหมารวม" | การตั้งชื่อเป็นดุลยพินิจของเจ้าของเดิม |
| การ anonymize แหล่งที่มา | Upstream อาจต้องการระบุชัดเจน |
| CHANGELOG versioning | เป็นระบบของ fork |
| GitHub Actions CI | เป็น infrastructure ของ fork |

---

## ขั้นตอนเมื่อตัดสินใจส่ง

```bash
# 0. เพิ่ม upstream remote (ครั้งเดียว)
git remote add upstream https://github.com/memolyviza2012-max/game-localization-qa.git
git fetch upstream

# 1. สร้าง PR branch ตามหัวข้อด้านบน
# 2. Push branch ขึ้น fork
# 3. เปิด PR จาก AeyXD:pr/N-... → memolyviza2012-max:main
# 4. รอ merge แล้วค่อยสร้าง PR ถัดไป
```

หรือเปิด issue ก่อนด้วยข้อความจาก `ISSUE-DRAFT.md`
