"""ตัวตัดคำไทยสำหรับ checker — พอร์ตจาก ThaiW3Setup/core/thai_wrap.py (MIT · stdlib ล้วน)

ต้นทาง: ThaiW3Setup https://github.com/AeyXD/ThaiW3Setup (MIT License)
เป็นบรรพบุรุษตรงของ ThaiSegmenter.cs ใน thaiwrap ซึ่งพอร์ตต่อและพิสูจน์ parity ไว้แล้ว
คงอัลกอริทึมเดิมทั้งหมด ไม่คิดใหม่: DP หาการตัดคำที่เหลือ "ชิ้นที่ไม่ใช่คำ" น้อยที่สุด
+ กฎห้ามตัด (สระจ่อย/สระบน-ล่าง/วรรณยุกต์/ไม้ยมก ห้ามขึ้นต้นชิ้น · สระหน้าเกาะพยัญชนะถัดไป)
+ merge pass รวม unknown ติดกันเป็นชิ้นเดียว (ท|ริ|สส์ ➔ ทริสส์)
สิ่งที่ดัดจากต้นฉบับ: โหลดพจนานุกรมจาก data/words_th.txt ของ repo นี้ (ต้นฉบับอ่าน .gz
จาก assets) และไม่พกฟังก์ชันแทรก hair space ของ Scaleform ซึ่ง checker ไม่ใช้

พจนานุกรม: data/words_th.txt — union ของ pythainlp corpus (Apache-2.0)
+ ICU thaidict (Unicode License) — เครดิตเต็มดู NOTICE ที่ root ของ repo

การใช้งานจาก checker: เช็ค available() ก่อนเสมอ แล้วจึง tokenize()/is_known()
โหลดแบบ lazy ครั้งเดียวต่อการรัน — dict หาย = available() คืน False พร้อมบันทึก stderr
ครั้งเดียว และทุก API ยังเรียกได้โดยไม่ crash (โหมดจำกัดของกฎ word_split_rejoining)
"""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

WORDS_FILE = Path(__file__).resolve().parent.parent / "data" / "words_th.txt"

THAI_RUN = re.compile("[\u0e01-\u0e4e]+")
# ชิ้นคำห้ามเริ่มด้วย: สระจ่อย อึ-ื ุ-ู ั ำ ฯ ฯลฯ และวรรณยุกต์/การันต์/นิคหิต/ไม้ยมก
# (ตัวเกาะต้องอยู่กับพยัญชนะนำหน้าเสมอ)
NO_BREAK_BEFORE = frozenset("\u0e2f\u0e30\u0e31\u0e32\u0e33\u0e34\u0e35\u0e36\u0e37\u0e38\u0e39\u0e3a"
                            "\u0e45\u0e46\u0e47\u0e48\u0e49\u0e4a\u0e4b\u0e4c\u0e4d\u0e4e")
# สระหน้า เ แ โ ใ ไ เป็นของพยัญชนะที่ตามหลัง
NO_BREAK_AFTER = frozenset("\u0e40\u0e41\u0e42\u0e43\u0e44")
SHORT_WORD = 2
_END = ""

_wrapper = None
_load_attempted = False


class ThaiWrapper:
    """พอร์ตตรงจาก ThaiWrapper ของ ThaiW3Setup (เปลี่ยนเฉพาะชื่อ wrap→split_run)"""

    def __init__(self, words):
        self.trie = {}
        self._split = lru_cache(maxsize=200_000)(self._split_run)
        self.add_words(words)

    def add_words(self, words) -> None:
        for w in words:
            node = self.trie
            for c in w:
                node = node.setdefault(c, {})
            node[_END] = True
        self._split.cache_clear()

    def split_run(self, run):
        """ตัด "run" ไทยล้วนหนึ่งก้อน → ชิ้นคำ"""
        return list(self._split(run))

    def is_word(self, word) -> bool:
        node = self.trie
        for c in word:
            if c not in node:
                return False
            node = node[c]
        return _END in node

    def _split_run(self, run):
        n = len(run)
        ok = [i == 0 or i == n or (run[i] not in NO_BREAK_BEFORE and run[i - 1] not in NO_BREAK_AFTER)
              for i in range(n + 1)]
        # best[i] = (unknown chars, words) for run[:i]; prev[i] = (start, is_word)
        inf = (n + 1, n + 1)
        best = [inf] * (n + 1)
        prev = [(0, False)] * (n + 1)
        best[0] = (0, 0)
        for i in range(n):
            if best[i] == inf or not ok[i]:
                continue
            unknown, count = best[i]
            node, j = self.trie, i
            while j < n and run[j] in node:
                node = node[run[j]]
                j += 1
                if _END in node and ok[j] and (unknown, count + 1) < best[j]:
                    best[j], prev[j] = (unknown, count + 1), (i, True)
            j = i + 1
            while not ok[j]:
                j += 1
            if (unknown + j - i, count + 1) < best[j]:
                best[j], prev[j] = (unknown + j - i, count + 1), (i, False)
        parts = []
        j = n
        while j > 0:
            i, word = prev[j]
            parts.append((run[i:j], word))
            j = i
        parts.reverse()
        # unknown text stays in one piece, together with tiny words stuck to it (ท|ริ|สส์ -> ทริสส์)
        merged = []
        for k, (text, word) in enumerate(parts):
            near_unknown = (k > 0 and not parts[k - 1][1]) or (k + 1 < len(parts) and not parts[k + 1][1])
            unknown = not word or (len(text) <= SHORT_WORD and near_unknown)
            if merged and unknown and not merged[-1][1]:
                merged[-1][0] += text
            else:
                merged.append([text, not unknown])
        return tuple(text for text, _ in merged)


def _load():
    """โหลด dict ครั้งเดียว (lazy) — หาไม่เจอคืน None พร้อมบันทึก stderr ครั้งเดียว"""
    global _wrapper, _load_attempted
    if _load_attempted:
        return _wrapper
    _load_attempted = True
    try:
        with WORDS_FILE.open("r", encoding="utf-8") as fh:
            words = {w for w in (line.strip() for line in fh) if w and not w.startswith("#")}
        _wrapper = ThaiWrapper(words)
    except OSError:
        print("⚠️ thai_segmenter: ไม่พบ %s — กฎ word_split_rejoining ทำงานแบบจำกัด "
              "(known_pairs เท่านั้น)" % WORDS_FILE, file=sys.stderr)
    return _wrapper


def available() -> bool:
    """dict โหลดได้ไหม — เรียกก่อนใช้ tokenize/is_known"""
    return _load() is not None


def tokenize(text):
    """ตัดคำทั้งสายข้อความ → list ชิ้นคำ (ส่วนที่ไม่ใช่ไทยคืนเป็นชิ้นเดียวทั้งก้อน)

    dict ไม่พร้อม → คืนทั้งสายเป็นชิ้นเดียว (fallback ไม่ crash)
    """
    w = _load()
    if w is None:
        return [text]
    out, pos = [], 0
    for m in THAI_RUN.finditer(text):
        if m.start() > pos:
            out.append(text[pos:m.start()])
        out.extend(w.split_run(m.group()))
        pos = m.end()
    if pos < len(text):
        out.append(text[pos:])
    return out


def is_known(word) -> bool:
    """word เป็นคำในพจนานุกรมไหม — dict ไม่พร้อมตอบ False"""
    w = _load()
    return bool(w and w.is_word(word))


def reset_cache():
    """ล้างสถานะ lazy-load (สำหรับ unit tests เท่านั้น)"""
    global _wrapper, _load_attempted
    _wrapper = None
    _load_attempted = False
