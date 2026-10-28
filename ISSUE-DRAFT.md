# Issue Draft: ถาม upstream เรื่องความสนใจรับ content contributions

> สถานะ: ร่าง — ยังไม่ส่ง

## Title
```
Interest in content contributions? (ฎ/ฏ rules, cultural review, UI overflow, transliteration standard, translation principles)
```

## Body

---

Hi! I forked this repo and have been working on it extensively. Before submitting PRs, I wanted to check if you're interested in receiving content contributions.

**What I can contribute (as separate, focused PRs):**

1. **Thai orthography rules** — ฎ/ฏ misspelling blacklist (14 pairs with zero false-positive scan strings), common transliteration misspellings per Royal Institute 2561 (19 pairs), conditional-fix patterns (ทึ่→ที่ except ทึ่ง/ทึ่ม)

2. **Four missing QA dimensions:**
   - Cultural & Sensitivity Review (rating-aware language, flag topics for Thai market, LGBTQ+ handling)
   - Royal Institute transliteration reference (การันต์ rules, -tion→ชัน, final-consonant mapping)
   - UI Text Overflow (character budgets per UI element, meaning-preserving compression)
   - Subtitle Timing & Reading Speed (Thai CPS ~15-17, line structure)

3. **Universal translation principles** (from real project standards): sense-for-sense translation, modality preservation ("อาจ"≠"จะ"), intentional vs redundant repetition, dialogue choice fidelity, minimal-diff editing

4. **Bug fixes** — broken markdown (stray backtick, inconsistent indentation), personal hard-coded paths replaced with portable ones

**What I kept separate (not PR-ing):**
- Architecture restructuring (single file → multi-file data-driven)
- QA checker tool + eval harness
- Versioning/installer system

These are available at my fork if you're interested: https://github.com/AeyXD/game-localization-qa

Would you prefer I send the content additions as PRs to this repo, or keep them in the fork? Happy to discuss what format works best for you.

---

## หมายเหตุ (ไม่ได้เขียนใน issue แต่บันทึกไว้)
- ถามก่อนเพื่อไม่เสียเวลาทำ branch ถ้า upstream ไม่สนใจ
- ใช้ภาษาอังกฤษเพราะ upstream เขียน commit message ภาษาอังกฤษ
- เอ่ยถึง fork URL ให้ upstream เห็นภาพรวมได้ถ้าอยากดู
- ไม่กดดัน — ให้ upstream เลือกได้ว่าจะรับ ไม่รับ หรือดูก่อน
