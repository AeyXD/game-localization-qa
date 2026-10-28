#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thai Game Localization QA Checker (เครื่องตรวจอักขรวิธีไทยสำหรับงานแปลเกม)
ส่วนหนึ่งของสกิล game-localization-qa — เสาหลักที่ 6

Data-driven: โหลดกฎทั้งหมดจาก data/*.json
  - กฎแบบ "คู่คำ" (ฎ/ฏ, การผสานคำ, CJK, กับดัก MT) เพิ่มที่ data file ได้ทันที ไม่ต้องแก้โค้ด
  - กฎ regex โครงสร้างใหม่ ต้องเพิ่ม handler ใน HANDLERS ของไฟล์นี้ด้วย

การใช้งาน:
  python3 checker/thai_qa.py translation.txt                      # dry-run (สแกนอย่างเดียว)
  python3 checker/thai_qa.py translation.txt --fix                # สแกน + แก้อัตโนมัติ (atomic write)
  python3 checker/thai_qa.py strings.csv --csv --source-col 1 --target-col 3 --fix --report review.csv
  python3 checker/thai_qa.py file.txt --list-rules                # แสดงกฎทั้งหมดที่โหลดจาก data

ความปลอดภัยไฟล์ (ตามพิธีสาร SKILL.md):
  - รักษา BOM (utf-8-sig) และรูปแบบ newline เดิม
  - จำนวนบรรทัด/แถวคงเดิม 100% (การแก้ทุกชนิดเป็นการแทนที่ในบรรทัดเท่านั้น)
  - เขียนทับแบบ Atomic Write (tempfile + os.replace)
  - แท็กเอนจิ้นเกม ({0}, %s, <COLOR...>, <br>) ไม่ถูกแตะเพราะทุก fix จับเฉพาะลำดับอักขระไทย

Exit codes: 0 = สะอาด, 1 = พบปัญหา, 2 = ข้อผิดพลาดการใช้งาน/ไฟล์
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR.parent / "data"

# ---------------------------------------------------------------------------
# Unicode ranges ภาษาไทย
# วรรณยุกต์ 0E48-0E4B | ไม้ไต่คู้/การันต์/นิคหิต 0E47, 0E4C-0E4D
# สระบน ั 0E31, ิ-ื 0E34-0E37 | สระล่าง ุ-ู 0E38-0E39 | ำ 0E33
THAI_TONE = "\u0E48-\u0E4B"
THAI_MARK = "\u0E31\u0E33-\u0E3A\u0E47-\u0E4E"   # ทุกสระ/วรรณยุกต์ที่ต้องมีพยัญชนะนำ
THAI_VOWEL = "\u0E31\u0E34-\u0E39"

RE_SARA_E_DOUBLE = re.compile("\u0E40\u0E40")
RE_TONE_VOWEL_SWAP = re.compile("([%s])([%s])" % (THAI_TONE, THAI_VOWEL))
RE_SARA_AM_TONE = re.compile("(\u0E33)([%s])" % THAI_TONE)
RE_DUP_MARK = re.compile("([%s])\\1+" % THAI_MARK.replace("\\", "\\\\"))
RE_ORPHAN_MARK = re.compile("(^|\\s)([%s])" % THAI_MARK)
RE_HTML_SEP = re.compile(">([%s])" % THAI_MARK)
RE_CJK = re.compile("[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]")
RE_LAUGH_YAMOK = re.compile("(?<![ก-๙])(ฮ่า|ฮา|หึ|เหอ|อิฮิ|คิฮิ|555)(?:[ \\t]*ๆ)+")
RE_YAMOK_SPACED_JOIN = re.compile("ๆ(?:[ \\t]+ๆ)+")   # ๆ ๆ คั่นวรรค → รวมเป็น ๆๆ (การซ้อนถูกต้อง)
RE_YAMOK_NO_SPACE = re.compile("([^\\sๆ])ๆ")
RE_YAMOK_AFTER = re.compile("(ๆ+)(?=[^\\s.,!?…:;\"”'’)\\]}<ๆ])")  # เติมช่องว่างหลัง ๆ ยกเว้นเครื่องหมาย/แท็ก
RE_YAMOK_LINE_START = re.compile("^ๆ")
RE_HAS_LATIN_WORD = re.compile("[A-Za-z]{3}")


def _issue(rule, name, severity, fixed, before, after, note=""):
    return {
        "rule": rule, "name": name, "severity": severity,
        "fixed": fixed, "before": before, "after": after, "note": note,
    }


def _mk_fix(pattern, repl):
    """สร้าง handler ที่แก้อัตโนมัติและบันทึกทุกจุดที่แก้"""
    def handler(text, rule):
        issues = []

        def _repl(m):
            new = repl(m)
            if new != m.group(0):
                issues.append(_issue(
                    rule["id"], rule.get("name", rule["id"]), "error", True,
                    m.group(0), new, rule.get("fix", "")))
            return new

        return pattern.sub(_repl, text), issues
    return handler


def _mk_flag(pattern, note):
    """สร้าง handler ที่แจ้งเตือนอย่างเดียว (ไม่แก้ — ต้องให้ผู้ตรวจตัดสิน)"""
    def handler(text, rule):
        issues = []
        for m in pattern.finditer(text):
            issues.append(_issue(
                rule["id"], rule.get("name", rule["id"]), "warning", False,
                m.group(0), "", note(m) if callable(note) else note))
        return text, issues
    return handler


# id ของกฎ (ตาม data/thai-orthography.json → typography_engine) → handler
HANDLERS = {
    "sara-e-double": _mk_fix(RE_SARA_E_DOUBLE, lambda m: "\u0E41"),
    "tone-before-upper-vowel": _mk_fix(RE_TONE_VOWEL_SWAP, lambda m: m.group(2) + m.group(1)),
    "tone-before-lower-vowel": _mk_fix(RE_TONE_VOWEL_SWAP, lambda m: m.group(2) + m.group(1)),
    "tone-after-sara-am": _mk_fix(RE_SARA_AM_TONE, lambda m: m.group(2) + m.group(1)),
    "duplicate-mark": _mk_fix(RE_DUP_MARK, lambda m: m.group(1)),
    "orphan-mark": _mk_flag(RE_ORPHAN_MARK, "สระ/วรรณยุกต์โดดเดี่ยว — ตรวจการตัดคำ/ตัดบรรทัดแล้วผสานกลับเข้าคำเดิม"),
    "html-tag-separation": _mk_flag(RE_HTML_SEP, "แท็กตัดแยกพยัญชนะกับสระ — ย้ายแท็กให้ครอบทั้งพยางค์ เช่น <b>มึง</b>"),
}


class QAData:
    """โหลดกฎทั้งหมดจาก data/*.json ครั้งเดียว"""

    def __init__(self, data_dir):
        self.dir = Path(data_dir)
        self.ortho = self._load("thai-orthography.json")
        self.traps = self._load("mt-traps.json")
        self.cjk = self._load("cjk-residue.json")

        # กฎแบบคู่คำ: แทนที่ตรงตับได้อย่างปลอดภัย (auto-fix)
        # ใช้ regex รวมแบบ single-pass เรียง "ยาว→สั้น" เพื่อป้องกันการสแกนซ้ำข้อความ
        # ที่เพิ่งแก้ (เช่น ปรากฎ→ปรากฏ แล้วกฎ "กฏ→กฎ" มาจับ "กฏ" ในคำ ปรากฏ ที่ถูกต้องอยู่แล้ว)
        self.pair_fixes = []  # (wrong, right, rule, name, guard) — เรียงยาว→สั้น
        for m in self.ortho["ror_tor_confusion"]["misspellings"]:
            self.pair_fixes.append((m["wrong"], m["right"], "ror-tor-misspelling",
                                    "ฎ/ฏ สะกดผิด (%s ➔ %s)" % (m["wrong"], m["right"]),
                                    m.get("guard", "")))
        for p in self.ortho["word_split_rejoining"]["known_pairs"]:
            self.pair_fixes.append((p["wrong"], p["right"], "word-split-rejoining",
                                    "คำถูกวรรคคั่นกลางคำ (%s ➔ %s)" % (p["wrong"], p["right"]), ""))
        for p in self.ortho.get("common_misspellings", {}).get("pairs", []):
            self.pair_fixes.append((p["wrong"], p["right"], "common-misspelling",
                                    "คำทับศัพท์สะกดผิด (%s ➔ %s)" % (p["wrong"], p["right"]),
                                    p.get("guard", "")))
        # กฎแก้แบบมีข้อยกเว้น (negative-exception) เช่น ทึ่(?![งม]) ➔ ที่ (ทึ่ง/ทึ่ม เป็นคำจริง)
        self.conditional_fixes = [
            (re.compile(r["detect"]), r["replace"], r)
            for r in self.ortho.get("conditional_fixes", {}).get("fixes", [])
        ]
        self.pair_fixes.sort(key=lambda t: len(t[0]), reverse=True)
        self.pair_pattern = re.compile("|".join(
            g + re.escape(w) for w, _, _, _, g in self.pair_fixes))
        self.pair_map = {w: r for w, r, _, _, _ in self.pair_fixes}

        # คำแนะนำการแปลอักษร CJK (แจ้งเตือนอย่างเดียว)
        self.cjk_hints = {}
        for e in self.cjk["entries"]:
            for src in re.split(r"\s*/\s*", e["source"]):
                self.cjk_hints[src] = e["thai"]

        # กับดัก MT: สแกนหาคำแปลต้องห้าม (แจ้งเตือนอย่างเดียว — ต้องดูบริบทก่อนเสมอ)
        self.trap_scan = []  # (forbidden, entry)
        for e in self.traps["entries"]:
            for f in e.get("forbidden", []):
                if len(f) >= 2:
                    self.trap_scan.append((f, e))

    def _load(self, name):
        path = self.dir / name
        if not path.exists():
            sys.exit("❌ ไม่พบไฟล์ข้อมูลกฎ: %s (ใช้ --data-dir ระบุได้)" % path)
        return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# หัวใจ: ตรวจ + แก้ข้อความ "หนึ่งบรรทัด"
# ---------------------------------------------------------------------------

def check_line(text, data, unknown_rules):
    """คืน (ข้อความที่แก้แล้ว, รายการ issues) — ทุกการแก้เป็นการแทนที่ในบรรทัดเท่านั้น"""
    issues = []
    out = text

    # 1) Typography engine (regex โครงสร้าง) ตามลำดับใน data file
    for rule in data.ortho["typography_engine"]:
        handler = HANDLERS.get(rule["id"])
        if handler is None:
            unknown_rules.add(rule["id"])
            continue
        out, found = handler(out, rule)
        issues.extend(found)

    # 1.5) กฎแก้แบบมีข้อยกเว้น (conditional fixes — แนวทางจากโปรเจกต์ ThaiW3Setup)
    for rx, repl, rule in data.conditional_fixes:
        def _cond_repl(m, _rule=rule, _repl=repl):
            issues.append(_issue(_rule["id"], _rule.get("name", _rule["id"]), "error", True,
                                 m.group(0), _repl, _rule.get("note", "")))
            return _repl
        out = rx.sub(_cond_repl, out)

    # 2) กฎแบบคู่คำ (ฎ/ฏ, การผสานคำ) — single-pass ยาว→สั้น ไม่สแกนซ้ำข้อความที่เพิ่งแก้
    def _pair_repl(m):
        wrong = m.group(0)
        right = data.pair_map[wrong]
        rule, name = next((r, n) for w, rt, r, n, g in data.pair_fixes if w == wrong)
        issues.append(_issue(rule, name, "error", True, wrong, right,
                             "สะกด/เว้นวรรคผิด — แก้อัตโนมัติตาม data/thai-orthography.json"))
        return right

    out = data.pair_pattern.sub(_pair_repl, out)

    # 3) ไม้ยมก (ๆ) — แนวทางกฎครบชุดจากโปรเจกต์ ThaiW3Setup
    # 3.1) เสียงหัวเราะ/เลียนเสียง: เขียนซ้ำเต็มคำตามหลักภาษาไทยทั่วไป (ฮ่า ๆๆ ➔ ฮ่า ฮ่า ฮ่า)
    out, found = _mk_fix(
        RE_LAUGH_YAMOK,
        lambda m: " ".join([m.group(1)] * (m.group().count("ๆ") + 1)))(
        out, {"id": "mai-yamok-laughter", "name": "เสียงหัวเราะใช้ ๆ — เขียนเต็มคำ",
              "fix": "เลียนเสียงหัวเราะต้องเขียนซ้ำเต็มคำ เช่น ฮ่า ๆๆ ➔ ฮ่า ฮ่า ฮ่า"})
    issues.extend(found)
    # 3.2) ๆ ซ้อนสื่อการซ้ำหลายครั้ง — ถูกต้อง แต่ถ้าคั่นด้วยช่องว่างต้องรวมเป็น ๆๆ
    out, found = _mk_fix(RE_YAMOK_SPACED_JOIN, lambda m: "ๆ" * m.group().count("ๆ"))(
        out, {"id": "mai-yamok-join", "name": "ๆ ๆ คั่นวรรค",
              "fix": "รวมเป็น ๆๆ — การซ้อนสื่อการซ้ำหลายครั้ง (ไม่ใช่ข้อผิดพลาด)"})
    issues.extend(found)
    out, found = _mk_fix(RE_YAMOK_NO_SPACE, lambda m: m.group(1) + " ๆ")(
        out, {"id": "mai-yamok-no-space", "name": "ๆ ไร้ช่องว่างนำหน้า",
              "fix": "แทรกช่องว่างก่อน ๆ"})
    issues.extend(found)
    out, found = _mk_fix(RE_YAMOK_AFTER, lambda m: m.group(1) + " ")(
        out, {"id": "mai-yamok-after-space", "name": "ๆ ไม่มีช่องว่างท้ายเมื่อมีคำต่อ",
              "fix": "แทรกช่องว่างหลัง ๆ (ยกเว้นก่อนเครื่องหมายวรรคตอน/วงเล็บปิด/แท็ก)"})
    issues.extend(found)
    out, found = _mk_flag(RE_YAMOK_LINE_START, "ย้ายการตัดบรรทัดไปหลัง 'คำ ๆ'")(
        out, {"id": "mai-yamok-orphan", "name": "ๆ ขึ้นต้นบรรทัด"})
    issues.extend(found)

    # 4) อักษร CJK ตกค้าง
    for m in RE_CJK.finditer(out):
        hint = ""
        for src, thai in data.cjk_hints.items():
            if src in out:
                hint = " (แปลว่า: %s)" % thai
                break
        issues.append(_issue("cjk-residue", "อักษร CJK ตกค้าง", "error", False,
                             m.group(0), "", "บทหลุดจาก MT จีน→ไทย" + hint))

    # 5) กับดัก MT (คำแปลต้องห้ามปรากฏในบทแปล)
    for forbidden, entry in data.trap_scan:
        if forbidden in out:
            correct = entry["correct"]
            if isinstance(correct, list):
                correct = " หรือ ".join(correct)
            issues.append(_issue(
                "mt-trap:%s" % entry["id"], "กับดัก MT: %s" % entry["source"],
                "warning", False, forbidden, "",
                "ห้ามใช้ '%s' — แปลที่ถูกคือ: %s" % (forbidden, correct)))

    return out, issues


# ---------------------------------------------------------------------------
# การตรวจ "วางคำแปลผิดแถว" เชิงสถิติ (Statistical Mispaste Detection)
# แนวทางจาก mispaste_report.py ของโปรเจกต์ ThaiW3Setup (ตัวติดตั้งภาษาไทย The Witcher 3)
# ---------------------------------------------------------------------------

def _norm_text(s):
    """ตัดแท็กและรวมช่องว่าง — เตรียมเทียบความยาว/ความคล้าย"""
    return re.sub(r"<[^>]+>|\s+", " ", s).strip()


def detect_mispaste(entries, ratio_band=(0.2, 3.5), dup_min_len=40, src_sim_max=0.6):
    """ตรวจแถวที่คำแปลน่าจะถูก copy มาวางผิดแถว โดยไม่ต้องเข้าใจความหมาย

    entries: [(row_number, source, target)]
    1. length-anomaly: อัตราส่วนความยาว ไทย/อังกฤษ ออกนอกช่วง ratio_band (ปกติ 0.2-3.5)
    2. mispaste-suspect: คำแปลยาว (>= dup_min_len) ซ้ำกันหลายแถว แต่ต้นฉบับอังกฤษต่างกันชัด
       (ความคล้าย < src_sim_max) -> แถวที่อัตราส่วนความยาวห่างจาก 1.0 มากที่สุดคือผู้ต้องสงสัย
    คืน list ของ dict — ทุกรายการเป็น "การแจ้งเตือน" เท่านั้น ต้องตรวจด้วยตาก่อนเสมอ
    """
    import difflib
    issues = []
    by_target = {}
    for row, src, tgt in entries:
        en, th = _norm_text(src), _norm_text(tgt)
        if len(en) >= 15 and len(th) >= 15 and re.search("[ก-๙]", th):
            ratio = len(th) / len(en)
            if not ratio_band[0] <= ratio <= ratio_band[1]:
                issues.append(dict(
                    row=row, rule="length-anomaly", name="อัตราส่วนความยาวผิดปกติ",
                    before="",
                    note="ไทย/อังกฤษ = %.2f (ปกติ %.1f-%.1f) — อาจวางผิดแถว แปลไม่ครบ หรือแปลเกินจำเป็น"
                    % (ratio, ratio_band[0], ratio_band[1])))
        if len(th) >= dup_min_len:
            by_target.setdefault(th, []).append((row, en))
    for th, rows in by_target.items():
        if len(rows) < 2:
            continue
        min_sim, pair = 1.0, None
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                sim = difflib.SequenceMatcher(None, rows[i][1].lower(), rows[j][1].lower()).ratio()
                if sim < min_sim:
                    min_sim, pair = sim, (rows[i], rows[j])
        if pair is None or min_sim > src_sim_max:
            continue
        bad = max(pair, key=lambda r: abs(len(th) / max(len(r[1]), 1) - 1.0))
        others = ", ".join(str(r[0]) for r in rows if r[0] != bad[0])
        issues.append(dict(
            row=bad[0], rule="mispaste-suspect", name="สงสัยวางคำแปลผิดแถว",
            before=th[:50],
            note="คำแปลยาวชุดนี้ซ้ำกับแถว %s แต่ต้นฉบับอังกฤษต่างกันชัด (ความคล้าย %.2f) — ตรวจด้วยตาก่อน"
            % (others, min_sim)))
    return issues


# ---------------------------------------------------------------------------
# การอ่าน/เขียนไฟล์แบบปลอดภัย
# ---------------------------------------------------------------------------

def read_text_safe(path):
    """อ่านไฟล์ — คืน (text, has_bom, newline) โดยตรวจ BOM และรูปแบบ newline"""
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if has_bom else "utf-8")
    except UnicodeDecodeError as e:
        sys.exit("❌ %s: ไม่ใช่ไฟล์ UTF-8 (%s) — ตรวจ encoding ของไฟล์ก่อนใช้เครื่องมือนี้" % (path, e))
    newline = "\r\n" if "\r\n" in text else "\n"
    return text, has_bom, newline


def atomic_write(path, content, has_bom, newline):
    """เขียนทับแบบ atomic — คง BOM และ newline เดิม"""
    data = content.encode("utf-8-sig" if has_bom else "utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def run_text_mode(path, args, data, report, unknown_rules):
    """โหมดไฟล์ข้อความทั่วไป (.txt/.json/...): ตรวจรายบรรทัด"""
    text, has_bom, newline = read_text_safe(path)
    lines = text.splitlines(keepends=True)
    n_lines_before = len(lines)

    out_lines, n_fixed, n_flag = [], 0, 0
    for i, raw_line in enumerate(lines, 1):
        ending = ""
        body = raw_line
        for e in ("\r\n", "\n"):
            if body.endswith(e):
                ending, body = e, body[: -len(e)]
                break
        fixed, issues = check_line(body, data, unknown_rules)
        for iss in issues:
            iss["location"] = "line %d" % i
            iss["file"] = str(path)
            report.append(iss)
            if iss["fixed"]:
                n_fixed += 1
            else:
                n_flag += 1
        out_lines.append(fixed + ending)

    assert len(out_lines) == n_lines_before, "Line count mismatch!"
    if args.fix and any(l != r for l, r in zip(lines, out_lines)):
        atomic_write(path, "".join(out_lines), has_bom, newline)
    return n_lines_before, n_fixed, n_flag


def run_csv_mode(path, args, data, report, unknown_rules):
    """โหมด CSV: ตรวจคอลัมน์คำแปล + ตรวจบทหลุด (ช่องว่าง/ไม่แปล) รายแถว"""
    text, has_bom, newline = read_text_safe(path)
    rows = list(csv.reader(io.StringIO(text)))
    n_rows = len(rows)

    sc = args.source_col - 1 if args.source_col else None
    tc = args.target_col - 1
    n_fixed = n_flag = 0
    mispaste_rows = []

    for idx, row in enumerate(rows, 1):
        if len(row) <= tc or not row[tc].strip():
            # ช่องคำแปลว่างเปล่าทั้งที่มีต้นฉบับ = บทหลุด
            if sc is not None and len(row) > sc and row[sc].strip():
                iss = _issue("empty-target", "ช่องคำแปลว่างเปล่า", "error", False, "", "",
                             "บทหลุดแปล — มีต้นฉบับแต่ไม่มีคำแปล")
                iss.update(location="row %d" % idx, file=str(path))
                report.append(iss)
                n_flag += 1
            continue

        target = row[tc]
        fixed, issues = check_line(target, data, unknown_rules)

        # บทพูดหลุดภาษาอังกฤษ 100% (คำแปลเหมือนต้นฉบับ)
        if sc is not None and len(row) > sc and fixed.strip() == row[sc].strip() \
                and RE_HAS_LATIN_WORD.search(row[sc]):
            iss = _issue("untranslated-leak", "บทพูดหลุดภาษาอังกฤษ 100%", "warning", False,
                         row[sc][:60], "", "คำแปลเหมือนต้นฉบับ — ยังไม่ได้แปล")
            iss.update(location="row %d" % idx, file=str(path))
            report.append(iss)
            n_flag += 1

        if args.fix and fixed != target:
            row[tc] = fixed
        for iss in issues:
            iss.update(location="row %d" % idx, file=str(path))
            report.append(iss)
            n_fixed += 1 if iss["fixed"] else 0
            n_flag += 0 if iss["fixed"] else 1
        if sc is not None and len(row) > sc and row[sc].strip():
            mispaste_rows.append((idx, row[sc], fixed))

    # ตรวจ "วางคำแปลผิดแถว" เชิงสถิติ (ต้องระบุ --source-col)
    if sc is not None:
        for m in detect_mispaste(mispaste_rows):
            iss = _issue(m["rule"], m["name"], "warning", False, m["before"], "", m["note"])
            iss.update(location="row %d" % m["row"], file=str(path))
            report.append(iss)
            n_flag += 1

    if args.fix:
        buf = io.StringIO()
        csv.writer(buf, lineterminator=newline).writerows(rows)
        atomic_write(path, buf.getvalue(), has_bom, newline)
    return n_rows, n_fixed, n_flag


def write_report(path, report):
    """เขียน Audit Trail CSV (utf-8-sig เปิดใน Excel ได้ทันที)"""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(["File", "Location", "Rule", "Severity", "AutoFixed", "Before", "After", "Note"])
    for iss in report:
        w.writerow([iss["file"], iss["location"], iss["rule"], iss["severity"],
                    "yes" if iss["fixed"] else "no", iss["before"], iss["after"], iss["note"]])
    Path(path).write_bytes(buf.getvalue().encode("utf-8-sig"))


def print_rule_inventory(data):
    """แสดงสิ่งที่ checker ตรวจทั้งหมด 4 ชั้น — ให้ผู้ใช้เห็นขอบเขตการตรวจก่อนรันจริง"""
    from collections import Counter

    print("📋 Thai QA Checker — สิ่งที่ตรวจทั้งหมด (โหลดจาก data/*.json อัตโนมัติ)")
    print("")
    print("🔧 ชั้นแก้อัตโนมัติ (auto-fix)")
    print("  ▸ อักขรวิธีไทย — %d กฎ:" % len(data.ortho["typography_engine"]))
    for r in data.ortho["typography_engine"]:
        if r["id"] not in HANDLERS:
            mark = "❌ ยังไม่มี handler"
        else:
            mark = "✅" if r.get("auto_fix", True) else "⚠️ แจ้งเตือนเท่านั้น"
        print("      %-24s %s %s" % (r["id"], mark, r["name"]))

    print("  ▸ ไม้ยมก (ๆ) — %d กฎ:" % len(data.ortho["mai_yamok"]["rules"]))
    for r in data.ortho["mai_yamok"]["rules"]:
        ex = r.get("examples", {})
        desc = ("%s ➔ %s" % (ex["wrong"][0], ex["right"][0])
                if ex.get("wrong") and ex.get("right") else r["fix"])
        print("      %-24s %s %s" % (r["id"], "✅" if r.get("auto_fix") else "⚠️ ", desc))

    print("  ▸ กฎมีข้อยกเว้น — %d กฎ:" % len(data.conditional_fixes))
    for _rx, repl, rule in data.conditional_fixes:
        print("      %-24s ✅ %s ➔ %s" % (rule["id"], rule["detect"], repl))

    groups = Counter(rule for _w, _r, rule, _n, _g in data.pair_fixes)
    labels = {"ror-tor-misspelling": "ฎ/ฏ สะกดผิด",
              "word-split-rejoining": "ผสานคำที่ถูกวรรคคั่น",
              "common-misspelling": "คำทับศัพท์สะกดผิด"}
    print("  ▸ คู่คำสะกดผิด — %d คู่ (แทนที่ single-pass ยาว→สั้น กันกฎทับซ้อน):" % len(data.pair_fixes))
    for rule, n in groups.most_common():
        exs = ["%s ➔ %s" % (w, r) for w, r, rl, _n, _g in data.pair_fixes if rl == rule][:2]
        print("      %-22s %2d คู่ — %s" % (labels.get(rule, rule), n, ", ".join(exs)))

    print("")
    print("⚠️  ชั้นแจ้งเตือน (flag — แจ้งเพื่อให้คน/AI ตัดสิน ไม่แก้อัตโนมัติ)")
    print("      (รวมกฎ ⚠️ ในกลุ่มอักขรวิธีข้างบน: orphan-mark, html-tag-separation, mai-yamok-orphan)")
    cjk_ex = next(iter(data.cjk_hints.items()))
    print("  ▸ อักษร CJK ตกค้าง — %d คำ พร้อมคำแปลแนะนำ (เช่น %s = %s)"
          % (len(data.cjk_hints), cjk_ex[0], cjk_ex[1]))
    cats = Counter(e["category"] for e in data.traps["entries"])
    print("  ▸ กับดัก MT — %d รายการ (%s)"
          % (len(data.traps["entries"]),
             " · ".join("%s %d" % (c, n) for c, n in sorted(cats.items()))))

    print("")
    print("📄 โหมด CSV (ใช้ --csv --source-col N --target-col M)")
    print("      empty-target        ช่องคำแปลว่างทั้งที่มีต้นฉบับ")
    print("      untranslated-leak   คำแปลเหมือนต้นฉบับอังกฤษ 100% (ยังไม่ได้แปล)")
    print("      length-anomaly      อัตราส่วนความยาว ไทย/อังกฤษ นอกช่วง 0.2-3.5")
    print("      mispaste-suspect    คำแปลยาวซ้ำกันแต่ต้นฉบับอังกฤษต่างกันชัด (สงสัยวางผิดแถว)")

    print("")
    print("🛡️  ความปลอดภัยไฟล์ (ทุกโหมด): รักษา BOM/newline เดิม · จำนวนบรรทัดคงเดิม 100% · "
          "atomic write · ไม่แตะแท็กเกม ({0}, %s, <COLOR>, <br>)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):  # กัน cp1252 บน Windows Terminal
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    p = argparse.ArgumentParser(
        description="Thai Game Localization QA Checker — data-driven จาก data/*.json")
    p.add_argument("files", nargs="+", help="ไฟล์แปลที่จะตรวจ (.txt/.json หรือ .csv เมื่อใช้ --csv)")
    p.add_argument("--fix", action="store_true", help="แก้อัตโนมัติและเขียนทับ (atomic write)")
    p.add_argument("--csv", action="store_true", help="โหมด CSV — ตรวจเฉพาะคอลัมน์เป้าหมาย")
    p.add_argument("--source-col", type=int, default=None, metavar="N",
                   help="หมายเลขคอลัมน์ต้นฉบับ (1-based) — เปิดการตรวจบทหลุดแปล")
    p.add_argument("--target-col", type=int, default=2, metavar="N",
                   help="หมายเลขคอลัมน์คำแปล (1-based, default: 2)")
    p.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="โฟลเดอร์ data/*.json")
    p.add_argument("--report", metavar="CSV", help="เขียนรายงาน Audit Trail เป็นไฟล์ CSV")
    p.add_argument("--list-rules", action="store_true",
                   help="แสดงสิ่งที่ตรวจทั้งหมด 4 ชั้น (auto-fix / แจ้งเตือน / โหมด CSV / ความปลอดภัยไฟล์)")
    p.add_argument("--quiet", action="store_true", help="พิมพ์แค่สรุปผล")
    args = p.parse_args(argv)

    data = QAData(args.data_dir)

    if args.list_rules:
        print_rule_inventory(data)
        return 0

    report, unknown_rules = [], set()
    total_fixed = total_flag = 0
    try:
        for f in args.files:
            path = Path(f)
            if not path.exists():
                sys.exit("❌ ไม่พบไฟล์: %s" % path)
            if args.csv:
                n, fixed, flag = run_csv_mode(path, args, data, report, unknown_rules)
                unit = "แถว"
            else:
                n, fixed, flag = run_text_mode(path, args, data, report, unknown_rules)
                unit = "บรรทัด"
            total_fixed += fixed
            total_flag += flag
            if not args.quiet:
                for iss in report:
                    if iss["file"] == str(path):
                        mark = "🔧" if iss["fixed"] else ("⚠️ " if iss["severity"] == "warning" else "❌")
                        print("  %s [%s] %s: %s%s" % (
                            mark, iss["location"], iss["rule"], iss["before"][:40],
                            (" ➔ " + iss["after"]) if iss["fixed"] else
                            ((" — " + iss["note"]) if iss["note"] else "")))
            print("%s: ตรวจ %d %s | แก้อัตโนมัติ %d จุด | แจ้งเตือน %d จุด%s"
                  % (path.name, n, unit, fixed, flag, " (เขียนทับแล้ว)" if args.fix else " (dry-run)"))
    except SystemExit:
        raise
    except Exception as e:
        sys.exit("❌ ข้อผิดพลาด: %s" % e)

    if unknown_rules:
        print("⚠️  กฎใน data ที่ยังไม่มี handler ใน checker (ต้องอัปเดตโค้ด): %s"
              % ", ".join(sorted(unknown_rules)))

    print("─" * 60)
    print("รวม: แก้อัตโนมัติ %d จุด | แจ้งเตือนอีก %d จุดที่ต้องตรวจด้วยคน/AI" % (total_fixed, total_flag))
    if args.report:
        write_report(args.report, report)
        print("📄 บันทึก Audit Trail: %s" % args.report)
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
