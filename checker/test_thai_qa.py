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
        self.assertEqual(fixed, "เร็ว ๆ ไปเถอะ")
        self.assertTrue(any(i["rule"] == "mai-yamok-no-space" and i["fixed"] for i in issues))

    def test_stacked_yamok_is_valid(self):
        """ๆๆ ซ้อนกันสื่อการซ้ำหลายครั้ง — ถูกต้อง ห้ามแจ้งเตือนหรือแก้"""
        text = "รีบ ๆๆ"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertFalse([i for i in issues if i["rule"].startswith("mai-yamok")])

    def test_spaced_yamok_joined(self):
        """ๆ ๆ คั่นวรรคต้องรวมเป็น ๆๆ (แนวทาง ThaiW3Setup — join ไม่ใช่ flag)"""
        fixed, issues = fix("มาก ๆ ๆ")
        self.assertEqual(fixed, "มาก ๆๆ")
        self.assertTrue(any(i["rule"] == "mai-yamok-join" and i["fixed"] for i in issues))

    def test_laughter_full_word(self):
        """เสียงหัวเราะเขียนซ้ำเต็มคำ: ฮ่า ๆๆ! ➔ ฮ่า ฮ่า ฮ่า!"""
        fixed, issues = fix("ฮ่า ๆๆ!")
        self.assertEqual(fixed, "ฮ่า ฮ่า ฮ่า!")
        self.assertTrue(any(i["rule"] == "mai-yamok-laughter" and i["fixed"] for i in issues))

    def test_laughter_spaced_yamok(self):
        fixed, _ = fix("ฮ่า ๆ ๆ!")
        self.assertEqual(fixed, "ฮ่า ฮ่า ฮ่า!")

    def test_laughter_single_yamok(self):
        fixed, _ = fix("ฮา ๆ")
        self.assertEqual(fixed, "ฮา ฮา")

    def test_non_laughter_not_expanded(self):
        """คำปกติที่ใช้ ๆ ต้องไม่ถูกขยายเป็นคำซ้ำเต็ม"""
        for text in ("เดินเร็ว ๆ ไป", "ซื้อของเยอะ ๆๆ"):
            fixed, _ = fix(text)
            self.assertEqual(fixed, text)

    def test_compound_word_not_laughter(self):
        """ฮา ที่เป็นส่วนของคำประสม (เฮฮา) ต้องไม่ถูกขยาย"""
        text = "งานเฮฮา ๆๆ"
        fixed, _ = fix(text)
        self.assertEqual(fixed, text)

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


class TestCommonMisspellings(unittest.TestCase):
    """คำทับศัพท์สะกดผิดตามหลักเกณฑ์ราชบัณฑิตยสภา 2561 (data/thai-orthography.json)"""

    def test_gam_karan_excess(self):
        fixed, issues = fix("เปิดเกมม์ใหม่อีกครั้ง")
        self.assertEqual(fixed, "เปิดเกมใหม่อีกครั้ง")
        self.assertTrue(any(i["rule"] == "common-misspelling" for i in issues))

    def test_tion_chan(self):
        fixed, _ = fix("อัปเดตเวอร์ชั่นใหม่ของเกม")
        self.assertEqual(fixed, "อัปเดตเวอร์ชันใหม่ของเกม")

    def test_correct_karan_not_overfixed(self):
        text = "โหมดแอ็กชันของเกมเวอร์ชันล่าสุด"
        fixed, issues = fix(text)
        self.assertEqual(fixed, text)
        self.assertFalse([i for i in issues if i["fixed"]])


class TestThaiW3Rules(unittest.TestCase):
    """กฎที่ประยุกต์จากโปรเจกต์ ThaiW3Setup (ตัวติดตั้งภาษาไทย The Witcher 3)"""

    def test_thin_than(self):
        fixed, _ = fix("ชุมชนถิ่งฐานเดิม")
        self.assertEqual(fixed, "ชุมชนถิ่นฐานเดิม")

    def test_thue_pattern_with_exceptions(self):
        fixed, issues = fix("สถานทึ่นั้น")
        self.assertEqual(fixed, "สถานที่นั้น")
        self.assertTrue(any(i["rule"] == "thue-without-ng-m" and i["fixed"] for i in issues))
        for correct in ("น่าทึ่งมาก", "รสชาติทึ่มไปหน่อย"):
            fixed, issues = fix(correct)
            self.assertEqual(fixed, correct)
            self.assertFalse([i for i in issues if i["fixed"]])

    def test_pra_la_pattern(self):
        fixed, _ = fix("สัตว์ประหลาขนาดใหญ่")
        self.assertEqual(fixed, "สัตว์ประหลาดขนาดใหญ่")
        fixed, _ = fix("สัตว์ประหลาดโบราณ")
        self.assertEqual(fixed, "สัตว์ประหลาดโบราณ")

    def test_wet_ordering_longest_first(self):
        fixed, _ = fix("พลังเวทย์มนต์ของโรงเรียนเวทย์")
        self.assertEqual(fixed, "พลังเวทมนตร์ของโรงเรียนเวท")

    def test_fai_klai(self):
        fixed, _ = fix("ความไฝ่ฝันสูงสุด")
        self.assertEqual(fixed, "ความใฝ่ฝันสูงสุด")

    def test_beuang(self):
        fixed, _ = fix("เบื่องบนและเบื่องล่างของแม่น้ำ")
        self.assertEqual(fixed, "เบื้องบนและเบื้องล่างของแม่น้ำ")

    def test_yamok_spaced_stacked_flagged(self):
        """Regression v1.2.1: 'ๆ ๆ' คั่นวรรคต้องถูกรวมเป็น ๆๆ — ไม่ใช่แจ้งเตือน"""
        fixed, issues = fix("มาก ๆ ๆ")
        self.assertEqual(fixed, "มาก ๆๆ")
        self.assertTrue(any(i["rule"] == "mai-yamok-join" and i["fixed"] for i in issues))

    def test_yamok_after_space(self):
        fixed, issues = fix("เขาเดินเร็ว ๆแล้วหยุดพัก")
        self.assertEqual(fixed, "เขาเดินเร็ว ๆ แล้วหยุดพัก")
        self.assertTrue(any(i["rule"] == "mai-yamok-after-space" and i["fixed"] for i in issues))

    def test_yamok_after_space_exceptions(self):
        """ไม่แทรกช่องว่างหลัง ๆ เมื่อตามด้วยเครื่องหมายวรรคตอน/วงเล็บปิด/แท็ก"""
        for text in ("หยุดเดี๋ยวนี้เร็ว ๆ!", "รอแป๊บ ๆ…", "โจมตีเร็ว ๆ</COLOR>", "ซื้อของเยอะ ๆ)"):
            fixed, _ = fix(text)
            self.assertEqual(fixed, text)


class TestMispasteDetection(unittest.TestCase):
    """ตรวจวางคำแปลผิดแถวเชิงสถิติ (แนวทาง mispaste_report.py ของ ThaiW3Setup)"""

    def test_length_anomaly(self):
        issues = q.detect_mispaste([(
            1, "The ancient forest whispers secrets of the old world to those who listen carefully.",
            "ป่ากระซิบความลับ")])
        self.assertTrue(any(i["rule"] == "length-anomaly" and i["row"] == 1 for i in issues))

    def test_mispaste_suspect(self):
        th = "คำแปลยาวมากที่ถูกวางซ้ำกันสองแถวโดยไม่ได้ตั้งใจให้เหมือนกันเลยสักนิด"
        issues = q.detect_mispaste([
            (2, "Geralt drew his silver sword and prepared to fight the ghoul in the swamp.", th),
            (5, "OK", th)])
        hit = [i for i in issues if i["rule"] == "mispaste-suspect"]
        self.assertTrue(hit)
        self.assertEqual(hit[0]["row"], 5)

    def test_normal_rows_clean(self):
        issues = q.detect_mispaste([
            (1, "Hello traveler, welcome to our village.", "สวัสดีพ่อค้า ยินดีต้อนรับสู่หมู่บ้านของเรา"),
            (2, "Goodbye and safe travels, my friend.", "ลาก่อน ขอให้เดินทางปลอดภัยนะเพื่อน")])
        self.assertFalse(issues)


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
        self.assertIn("เร็ว ๆ มาก", fixed)
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


class TestListRules(unittest.TestCase):
    """--list-rules ต้องแสดงสิ่งที่ตรวจครบทั้ง 4 ชั้น — ผู้ใช้ใหม่รู้ขอบเขตก่อนรันจริง"""

    def test_inventory_covers_all_layers(self):
        import io as _io
        from contextlib import redirect_stdout
        buf = _io.StringIO()
        with redirect_stdout(buf):
            rc = q.main(["x", "--list-rules"])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        for section in ("ชั้นแก้อัตโนมัติ", "ชั้นแจ้งเตือน", "โหมด CSV", "ความปลอดภัยไฟล์",
                        "mai-yamok-laughter", "thue-without-ng-m", "ฎ/ฏ สะกดผิด",
                        "mispaste-suspect", "กับดัก MT"):
            self.assertIn(section, out)


if __name__ == "__main__":
    unittest.main()
