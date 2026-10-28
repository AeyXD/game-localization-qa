#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ชุดทดสอบ Thai QA Checker — รันด้วย: python3 -m unittest discover -s checker -v"""

import csv
import io
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import thai_qa as q

DATA = q.QAData(q.DEFAULT_DATA_DIR)


def fix(text):
    return q.check_line(text, DATA, set())


class TestTypographyEngine(unittest.TestCase):
    def test_sara_e_double(self):
        fixed, issues = fix("เเรกมาก")
        self.assertEqual(fixed, "แรกมาก")
        self.assertTrue(any(i["rule"] == "sara-e-double" and i["fixed"] for i in issues))

    def test_tone_before_upper_vowel(self):
        fixed, _ = fix("น่ิท")
        self.assertEqual(fixed, "นิ่ท")

    def test_tone_before_lower_vowel(self):
        fixed, _ = fix("ดุ่")
        self.assertEqual(fixed, "ดุ่")

    def test_tone_after_sara_am(self):
        fixed, _ = fix("ทำ่")
        self.assertEqual(fixed, "ท่ำ")

    def test_duplicate_mark(self):
        fixed, _ = fix("มิิง")
        self.assertEqual(fixed, "มิง")

    def test_correct_text_untouched(self):
        text = "ทดสอบข้อความที่ถูกต้องอยู่แล้ว เช่น ที่นี่ ก่อนทำงาน"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertFalse([i for i in issues if i["fixed"]])

    def test_orphan_mark_flagged_not_fixed(self):
        text = "ทดสอบ ัการเว้นวรรค"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertTrue(any(i["rule"] == "orphan-mark" and not i["fixed"] for i in issues))

    def test_html_tag_separation_flagged(self):
        text = "<b>ม</b>ึง"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertTrue(any(i["rule"] == "html-tag-separation" for i in issues))


class TestRorTor(unittest.TestCase):
    def test_pa_rak_kod(self):
        fixed, _ = fix("ปรากฎตัวขึ้นแล้ว")
        self.assertEqual(fixed, "ปรากฏตัวขึ้นแล้ว")

    def test_kot_mai(self):
        fixed, _ = fix("กฏหมายของเกม")
        self.assertEqual(fixed, "กฎหมายของเกม")

    def test_dutsadi(self):
        fixed, _ = fix("ดุษฏีบัณฑิต")
        self.assertEqual(fixed, "ดุษฎีบัณฑิต")

    def test_wat_chakorn(self):
        fixed, _ = fix("วัฎจักรแห่งเวลา")
        self.assertEqual(fixed, "วัฏจักรแห่งเวลา")

    def test_correct_pa_rak_kot_not_corrupted(self):
        """Regression: ปรากฏ (ถูกต้องแล้ว) ต้องไม่ถูกกฎ กฏ→กฎ ทำลายกลับเป็น ปรากฎ"""
        text = "ปรากฏการณ์ปรากฏตัวขึ้น"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertFalse([i for i in issues if i["fixed"]])

    def test_kot_and_pa_rak_kod_in_same_line(self):
        """Regression: สองกฎเกี่ยวพันในบรรทัดเดียวต้องไม่ทำล้างกันเอง"""
        fixed, _ = fix("กฏของเกมบอกว่าศัตรูปรากฎตัวแล้ว")
        self.assertEqual(fixed, "กฎของเกมบอกว่าศัตรูปรากฏตัวแล้ว")


class TestMaiYamok(unittest.TestCase):
    def test_space_inserted_before(self):
        fixed, issues = fix("เร็วๆไปเถอะ")
        self.assertEqual(fixed, "เร็ว ๆไปเถอะ")
        self.assertTrue(any(i["rule"] == "mai-yamok-no-space" and i["fixed"] for i in issues))

    def test_stacked_flagged_not_fixed(self):
        text = "รีบ ๆๆ"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertTrue(any(i["rule"] == "mai-yamok-stacked" and not i["fixed"] for i in issues))

    def test_orphan_line_start(self):
        fixed, issues = fix("ๆไป")
        self.assertTrue(any(i["rule"] == "mai-yamok-orphan" for i in issues))

    def test_correct_yamok_untouched(self):
        fixed, issues = fix("เขาเดินเร็ว ๆ")
        self.assertEqual(fixed, "เขาเดินเร็ว ๆ")
        self.assertFalse(issues)


class TestCjkResidue(unittest.TestCase):
    def test_cjk_flagged_with_hint(self):
        text = "เขา变成แล้ว"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)  # CJK แจ้งเตือนอย่างเดียว ไม่แก้อัตโนมัติ
        hit = [i for i in issues if i["rule"] == "cjk-residue"]
        self.assertTrue(hit)
        self.assertIn("กลายเป็น", hit[0]["note"])


class TestRejoining(unittest.TestCase):
    def test_split_word_rejoined(self):
        fixed, _ = fix("การลอบสัง หาร")
        self.assertEqual(fixed, "การลอบสังหาร")


class TestMtTrapScan(unittest.TestCase):
    def test_strike_trap(self):
        _, issues = fix("การโจมตีแบบนัดหยุดงาน")
        hit = [i for i in issues if i["rule"] == "mt-trap:strike-mechanics"]
        self.assertTrue(hit)
        self.assertIn("ฟาดฟัน", hit[0]["note"])

    def test_cooldown_trap(self):
        _, issues = fix("สกิลกำลังเย็นลง")
        self.assertTrue(any(i["rule"] == "mt-trap:cooldown" for i in issues))

    def test_game_tags_never_touched(self):
        text = "{0} ปรากฎตัวที่ %s <COLOR FF0000>จุดเช็คพอยท์</COLOR>"
        fixed, _ = fix(text)
        self.assertIn("{0}", fixed)
        self.assertIn("%s", fixed)
        self.assertIn("<COLOR FF0000>", fixed)
        self.assertIn("</COLOR>", fixed)
        self.assertIn("ปรากฏตัว", fixed)


class TestFileSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, **kw):
        base = dict(fix=False, csv=False, source_col=None, target_col=2)
        base.update(kw)
        return Namespace(**base)

    def test_fix_preserves_line_count_and_content(self):
        f = self.dir / "t.txt"
        original = "บรรทัดเเรกปรากฎตัว\nเร็วๆมาก\nปกติดี\n"
        f.write_text(original, encoding="utf-8")
        report = []
        q.run_text_mode(f, self.args(fix=True), DATA, report, set())
        fixed = f.read_text(encoding="utf-8")
        self.assertEqual(len(fixed.splitlines()), 3)
        self.assertIn("บรรทัดแรกปรากฏตัว", fixed)
        self.assertIn("เร็ว ๆมาก", fixed)
        self.assertIn("ปกติดี", fixed)

    def test_bom_preserved(self):
        f = self.dir / "bom.txt"
        f.write_bytes("\ufeffปรากฎตัว\n".encode("utf-8-sig"))
        q.run_text_mode(f, self.args(fix=True), DATA, [], set())
        self.assertTrue(f.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertIn("ปรากฏตัว", f.read_text(encoding="utf-8-sig"))

    def test_crlf_preserved(self):
        f = self.dir / "crlf.txt"
        f.write_bytes("ปรากฎตัว\r\nok\r\n".encode("utf-8"))
        q.run_text_mode(f, self.args(fix=True), DATA, [], set())
        self.assertIn(b"\r\n", f.read_bytes())
        self.assertNotIn(b"\n\r", f.read_bytes())

    def test_dry_run_does_not_modify(self):
        f = self.dir / "dry.txt"
        original = "ปรากฎตัวเร็วๆ"
        f.write_text(original, encoding="utf-8")
        rc = q.main([str(f)])
        self.assertEqual(rc, 1)
        self.assertEqual(f.read_text(encoding="utf-8"), original)

    def test_clean_file_exit_zero(self):
        f = self.dir / "clean.txt"
        f.write_text("ข้อความถูกต้องสมบูรณ์\n", encoding="utf-8")
        rc = q.main([str(f), "--quiet"])
        self.assertEqual(rc, 0)

    def test_csv_mode_fix_and_leak_detection(self):
        f = self.dir / "t.csv"
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["source", "target"])
        w.writerow(["Checkpoint reached", "ถึงด่านตรวจแล้ว"])
        w.writerow(["Hello", ""])
        w.writerow(["Rage Quit", "Rage Quit"])
        w.writerow(["Burst fire", "ยิงระเบิด"])
        f.write_text(buf.getvalue(), encoding="utf-8")

        report = []
        rows, n_fixed, n_flag = q.run_csv_mode(
            f, self.args(fix=True, csv=True, source_col=1, target_col=2), DATA, report, set())

        rules = [i["rule"] for i in report]
        self.assertIn("empty-target", rules)            # row 3
        self.assertIn("untranslated-leak", rules)       # row 4
        self.assertTrue(any(r.startswith("mt-trap:") for r in rules))  # ด่านตรวจ/ยิงระเบิด
        # กับดัก MT เป็นการแจ้งเตือนเท่านั้น (ต้องดูบริบท) — ข้อความต้องยังคงเดิม
        content = f.read_text(encoding="utf-8")
        self.assertIn("ยิงระเบิด", content)
        self.assertIn("Rage Quit", content)
        # จำนวนแถวคงเดิม 100%
        self.assertEqual(len(list(csv.reader(io.StringIO(content)))), 5)

    def test_report_csv_written(self):
        f = self.dir / "r.txt"
        f.write_text("ปรากฎตัว\n", encoding="utf-8")
        rep = self.dir / "review.csv"
        q.main([str(f), "--report", str(rep), "--quiet"])
        rows = list(csv.reader(rep.read_text(encoding="utf-8-sig").splitlines()))
        self.assertEqual(rows[0][0], "File")
        self.assertEqual(rows[0][5], "Before")
        self.assertTrue(any("ปรากฎ" in r for r in rows[1:]))


if __name__ == "__main__":
    unittest.main()
