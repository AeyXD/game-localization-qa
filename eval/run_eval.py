#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eval Harness ของสกิล game-localization-qa — วัดผลว่าสกิล/เครื่องมือได้ผลจริงไหม

ชุดเคสอยู่ที่ eval/cases.json (48 เคส ครบ 7 เสาหลัก) โดยแต่ละเคสมี:
  source    = ต้นฉบับ (อังกฤษ หรือไทยที่มี typo สำหรับเสาหลัก 6)
  bad_mt    = คำแปลแบบ MT ที่ตกกับดัก
  accept    = รูปแปลที่ถือว่าถูก (มีอย่างน้อยหนึ่งรูป = ผ่านเกณฑ์นี้)
  reject    = สตริงกับดัก (ปรากฏแม้แต่รูปเดียว = ไม่ผ่าน)

คำสั่ง:
  python3 eval/run_eval.py selftest                      # ตรวจความถูกต้องของชุดเคสเอง
  python3 eval/run_eval.py checker [--min-coverage 95]   # วัด coverage ของ checker/thai_qa.py (regression net)
  python3 eval/run_eval.py template out.csv              # สร้างไฟล์เปล่าให้ AI/นักแปลกรอกคำแปล
  python3 eval/run_eval.py translations out.csv           # ให้คะแนนคำแปลที่กรอกแล้ว (รองรับ .json/.csv)
  python3 eval/run_eval.py list [--pillar 4]             # แสดงรายการเคส

วิธีวัดผล AI "มีสกิล vs ไม่มีสกิล" (A/B):
  1. สร้าง template 2 ชุด -> ให้ AI ชุด A แปลโดยไม่ให้อ่านสกิล / ชุด B ให้อ่าน SKILL.md + references + data ก่อน
  2. นำไฟล์ทั้งสองมาให้คะแนนด้วยคำสั่ง translations -> เทียบคะแนนรวม

Exit codes: 0 = ผ่านเกณฑ์, 1 = ไม่ผ่านเกณฑ์ (ใช้ต่อใน CI ได้)
"""

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_DIR / "checker"))
import thai_qa as q  # noqa: E402

CASES = json.loads((SCRIPT_DIR / "cases.json").read_text(encoding="utf-8"))["cases"]
DATA = q.QAData(REPO_DIR / "data")

PILLAR_NAMES = {
    1: "Persona & Pronouns", 2: "Context & Tone", 3: "Skills & Spells",
    4: "Items & Firearms", 5: "Quest Consistency", 6: "Leak & Typography",
    7: "Codex & Readables",
}


def grade_translation(text, case):
    """คืน list ปัญหา — ว่าง = ผ่าน (มี accept อย่างน้อยหนึ่ง และไม่มี reject เลย)"""
    problems = []
    if not text or not text.strip():
        return ["ไม่มีคำแปล"]
    if case.get("accept") and not any(a in text for a in case["accept"]):
        problems.append("ขาดรูปแปลที่ถูก (ต้องมี: %s)" % " หรือ ".join(case["accept"]))
    hits = [r for r in case.get("reject", []) if r in text]
    if hits:
        problems.append("ยังติดกับดัก MT: %s" % ", ".join(hits))
    return problems


def load_translations(path):
    p = Path(path)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        return {str(k): v for k, v in data.items()}
    out = {}
    with p.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("id"):
                out[row["id"]] = (row.get("translation") or "").strip()
    return out


def cmd_list(args):
    for c in CASES:
        if args.pillar and c["pillar"] != args.pillar:
            continue
        print("[%d|%s] %-24s %s" % (c["pillar"], c["category"], c["id"], c["source"]))
    return 0


def cmd_template(args):
    out = Path(args.out)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "pillar", "source", "context", "translation"])
        for c in CASES:
            w.writerow([c["id"], c["pillar"], c["source"], c["context"], ""])
    print("📄 สร้างเทมเพลต %d เคส: %s (กรอกคอลัมน์ translation แล้วเอามาให้คะแนน)" % (len(CASES), out))
    return 0


def cmd_translations(args):
    trans = load_translations(args.file)
    per_pillar = {p: [0, 0] for p in PILLAR_NAMES}  # pillar: [pass, total]
    failures, missing = [], []
    for c in CASES:
        text = trans.get(c["id"])
        problems = grade_translation(text, c)
        per_pillar[c["pillar"]][1] += 1
        if problems:
            if text is None:
                missing.append(c["id"])
            failures.append((c, text, problems))
        else:
            per_pillar[c["pillar"]][0] += 1

    print("%-22s %8s %8s" % ("เสาหลัก", "ผ่าน", "ทั้งหมด"))
    for p in sorted(PILLAR_NAMES):
        ok, total = per_pillar[p]
        print("%-22s %6d %8d   (%.0f%%)" % (PILLAR_NAMES[p], ok, total, ok * 100.0 / total))
    passed = sum(v[0] for v in per_pillar.values())
    score = passed * 100.0 / len(CASES)
    print("─" * 50)
    print("คะแนนรวม: %d/%d (%.1f%%)%s" % (passed, len(CASES), score,
          ("  |  ไม่พบคำแปล %d เคส: %s" % (len(missing), ", ".join(missing))) if missing else ""))
    if args.verbose or score < 100:
        print("\nรายละเอียดเคสที่ไม่ผ่าน:")
        for c, text, problems in failures:
            print("  ❌ [%d] %s" % (c["pillar"], c["id"]))
            if text:
                print("     คำแปล: %s" % text)
            for p in problems:
                print("     - %s" % p)
    ok = score >= args.min_score
    print("\n%s เกณฑ์ขั้นต่ำ %.0f%%" % ("✅ ผ่าน" if ok else "❌ ไม่ผ่าน", args.min_score))
    return 0 if ok else 1


def cmd_checker(args):
    """วัดว่า checker จับกับดักใน bad_mt ได้กี่ % — safety net กัน regression เมื่ออัปเกรดกฎ"""
    per_pillar = {p: [0, 0] for p in PILLAR_NAMES}  # [caught, testable]
    missed = []
    n_fixed = n_flag = 0
    for c in CASES:
        if not c.get("checker_testable"):
            continue
        text = c["bad_mt"]
        source = c.get("source", "")
        # ส่ง source เป็น source_text ให้ context-dependent traps ทำงานได้
        # (source ของ pillar 6 เป็นไทย — context_keywords เป็นอังกฤษจะไม่ match จึงไม่เกิดผลข้างเคียง)
        fixed, issues = q.check_line(text, DATA, set(), source_text=source)
        caught = bool(issues)
        per_pillar[c["pillar"]][1] += 1
        if caught:
            per_pillar[c["pillar"]][0] += 1
            n_fixed += sum(1 for i in issues if i["fixed"])
            n_flag += sum(1 for i in issues if not i["fixed"])
        else:
            missed.append(c["id"])

    testable = sum(v[1] for v in per_pillar.values())
    caught = sum(v[0] for v in per_pillar.values())
    print("🔍 Checker trap-coverage (จับกับดักจาก bad_mt ได้กี่เคส)")
    print("%-22s %8s %12s" % ("เสาหลัก", "จับได้", "ทดสอบได้*"))
    for p in sorted(PILLAR_NAMES):
        ok, total = per_pillar[p]
        if total:
            print("%-22s %6d %12d" % (PILLAR_NAMES[p], ok, total))
    print("─" * 50)
    coverage = caught * 100.0 / testable if testable else 0.0
    print("รวม: จับได้ %d/%d เคสที่ทดสอบได้ = %.1f%% (แก้อัตโนมัติ %d จุด, แจ้งเตือน %d จุด)"
          % (caught, testable, coverage, n_fixed, n_flag))
    print("* อีก %d เคส (สรรพนาม/บริบท) ต้องใช้ AI/คนตัดสิน — วัดด้วยคำสั่ง translations"
          % sum(1 for c in CASES if not c.get("checker_testable")))
    if missed:
        print("⚠️  เคสที่ checker พลาด: %s" % ", ".join(missed))
    ok = coverage >= args.min_coverage
    print("%s เกณฑ์ขั้นต่ำ %.0f%%" % ("✅" if ok else "❌", args.min_coverage))
    return 0 if ok else 1


def cmd_selftest(args):
    """ตรวจความถูกต้องของชุดเคสเอง: คำตอบอ้างอิงต้องผ่าน 100% และ bad_mt ต้องไม่ผ่าน 0%"""
    errors = []
    for c in CASES:
        ref = c["accept"][0]
        if grade_translation(ref, c):
            errors.append("คำตอบอ้างอิงไม่ผ่านเกณฑ์ตัวเอง: %s (accept=%r ชน reject?)" % (c["id"], ref))
        if not grade_translation(c["bad_mt"], c):
            errors.append("bad_mt ผ่านเกณฑ์ (กับดักไม่ทำงาน): %s" % c["id"])
    if errors:
        print("❌ ชุดเคสมีปัญหา %d จุด:" % len(errors))
        for e in errors:
            print("  - %s" % e)
        return 1
    print("✅ Selftest ผ่าน: %d เคส (อ้างอิงผ่าน 100%%, bad_mt ตกกับดัก 100%%) — เกณฑ์ accept/reject สอดคล้อง" % len(CASES))
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Eval harness ของ game-localization-qa")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selftest", help="ตรวจความถูกต้องของชุดเคสเอง")
    sub.add_parser("list", help="แสดงรายการเคส").add_argument("--pillar", type=int, default=None)

    sp = sub.add_parser("template", help="สร้างไฟล์เทมเพลตให้กรอกคำแปล")
    sp.add_argument("out")

    sp = sub.add_parser("translations", help="ให้คะแนนไฟล์คำแปล (.json หรือ .csv)")
    sp.add_argument("file")
    sp.add_argument("--min-score", type=float, default=0.0, help="คะแนนขั้นต่ำที่ถือว่าผ่าน (default 0)")
    sp.add_argument("-v", "--verbose", action="store_true", help="แสดงรายละเอียดทุกเคสที่ไม่ผ่านเสมอ")

    sp = sub.add_parser("checker", help="วัด coverage ของ checker เทียบ bad_mt")
    sp.add_argument("--min-coverage", type=float, default=95.0)

    args = p.parse_args(argv)
    return {"selftest": cmd_selftest, "list": cmd_list, "template": cmd_template,
            "translations": cmd_translations, "checker": cmd_checker}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
