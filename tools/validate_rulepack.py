#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则包校验器（plan/04 §2.3，plan/05 §3）。

断言（--check 退出码 0/1/2）：
- schema/枚举：字段齐、risk/basis/status/source.type 合法；variant 必带 note；
- 文件↔类别映射：文件名 → 类别固定（见 FILE_CATEGORIES），逐条 category 与文件声明一致；
- 同文件同词唯一（跨文件同词 = 同词异类，允许）；
- 锚点解析：锚点文件存在（references/statutes/<doc>.txt）→ 条款可抽取（行首定义位）
  → literal 词面逐字见于条款块；
- suggestion 非空；
- 排序：entries 按 word 码点序；
- manifest（--write-manifest 时）：文件 sha256/字节/计数/版本派生，写入 references/MANIFEST.json。

零第三方依赖；不联网。
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TOOL_NAME = "validate_rulepack"
__version__ = "0.0.1"

_REPO_ROOT = Path(__file__).resolve().parent.parent
WORDLISTS_DIR = _REPO_ROOT / "references" / "wordlists"
STATUTES_DIR = _REPO_ROOT / "references" / "statutes"
MANIFEST_PATH = _REPO_ROOT / "references" / "MANIFEST.json"
BASE_DATE = "2026-10-15"

FILE_CATEGORIES = {
    "absolute-terms.json": "绝对化用语",
    "medical.json": "医疗违禁",
    "health-food.json": "保健食品违禁",
    "industry.json": "行业违禁",
}

VALID_RISKS = ("high", "medium", "low")
VALID_BASIS = ("literal", "variant")
VALID_STATUS = ("verified", "pending")

_CLAUSE_RE = re.compile(r"^第[一二三四五六七八九十百零〇两]+条(?:之[一二三四五六七八九十]+)?")

ERR_START = 0


class Report:
    def __init__(self):
        self.errors = []

    def err(self, fname, word, msg):
        self.errors.append("%s / %s / %s" % (fname, word, msg))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def extract_clause(statute_text, clause):
    lines = statute_text.split("\n")
    start = None
    for i, line in enumerate(lines):
        m = _CLAUSE_RE.match(line.strip())
        if m and m.group(0) == clause:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _CLAUSE_RE.match(lines[j].strip()):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def load_statutes(rep):
    texts = {}
    for path in sorted(STATUTES_DIR.glob("*.txt")):
        try:
            texts[path.stem] = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            rep.err("-", "-", "法条冻结件不可读：%s（%s）" % (path.name, exc))
    return texts


def validate(rep):
    statutes = load_statutes(rep)
    clause_cache = {}
    counts = {}
    total = 0

    if not WORDLISTS_DIR.is_dir():
        rep.err("-", "-", "词表目录不存在：%s" % WORDLISTS_DIR)
        return {}, 0

    for fname in sorted(FILE_CATEGORIES):
        path = WORDLISTS_DIR / fname
        if not path.is_file():
            rep.err(fname, "-", "词表文件缺失")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            rep.err(fname, "-", "JSON 不可解析（%s）" % exc)
            continue
        expect_cat = FILE_CATEGORIES[fname]
        if payload.get("category") != expect_cat:
            rep.err(fname, "-", "文件声明 category=%r 与映射不符（应 %r）" % (payload.get("category"), expect_cat))
        entries = payload.get("entries")
        if not isinstance(entries, list):
            rep.err(fname, "-", "entries 非数组")
            continue
        seen = set()
        words_sorted = []
        for e in entries:
            if not isinstance(e, dict):
                rep.err(fname, "-", "条目非对象")
                continue
            word = e.get("word")
            if not isinstance(word, str) or not word.strip():
                rep.err(fname, "-", "word 缺失或非字符串")
                continue
            word = word
            words_sorted.append(word)
            if word in seen:
                rep.err(fname, word, "同文件重复词条")
            seen.add(word)
            if e.get("category") != expect_cat:
                rep.err(fname, word, "category=%r 与文件类别不符" % e.get("category"))
            if e.get("risk") not in VALID_RISKS:
                rep.err(fname, word, "risk 非法：%r" % e.get("risk"))
            if e.get("status") not in VALID_STATUS:
                rep.err(fname, word, "status 非法：%r" % e.get("status"))
            if not str(e.get("suggestion", "")).strip():
                rep.err(fname, word, "suggestion 为空")
            src = e.get("source")
            if not isinstance(src, dict) or src.get("type") != "non_official":
                rep.err(fname, word, "source 缺失或 type 非 non_official")
            anchor = e.get("anchor")
            if not isinstance(anchor, dict):
                rep.err(fname, word, "锚点缺失")
                continue
            doc = anchor.get("doc")
            clause = anchor.get("clause")
            basis = anchor.get("basis")
            if basis not in VALID_BASIS:
                rep.err(fname, word, "basis 非法：%r" % basis)
                continue
            if basis == "variant" and not str(anchor.get("note", "")).strip():
                rep.err(fname, word, "variant 条目缺 note")
            if doc not in statutes:
                rep.err(fname, word, "锚点文件缺失：%s" % doc)
                continue
            key = (doc, clause)
            if key not in clause_cache:
                clause_cache[key] = extract_clause(statutes[doc], clause)
            block = clause_cache[key]
            if block is None:
                rep.err(fname, word, "条款解析不到：%s %s" % (doc, clause))
                continue
            if basis == "literal" and word not in block:
                rep.err(fname, word, "literal 词面未见于条款（%s %s）" % (doc, clause))
        if words_sorted != sorted(words_sorted):
            rep.err(fname, "-", "entries 未按 word 码点序排序")
        counts[expect_cat] = len(entries)
        total += len(entries)
    return counts, total


def derive_version(files_info):
    """版本从文件列表 sha256 派生（K14）：取各文件 sha256 串接后再哈希的前 12 位。"""
    joined = "".join(f["sha256"] for f in files_info)
    return hashlib.sha256(joined.encode("ascii")).hexdigest()[:12]


def write_manifest(counts, total):
    files_info = []
    for fname in sorted(FILE_CATEGORIES):
        path = WORDLISTS_DIR / fname
        data = path.read_bytes()
        files_info.append({
            "path": "references/wordlists/" + fname,
            "sha256": sha256_bytes(data),
            "bytes": len(data),
        })
    manifest = {
        "rulepack_version": derive_version(files_info),
        "base_date": BASE_DATE,
        "files": files_info,
        "counts": {
            "words_verified": total,
            "words_by_category": counts,
        },
    }
    MANIFEST_PATH.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(prog="validate_rulepack.py", description="规则包校验器")
    parser.add_argument("--check", action="store_true",
                        help="与默认行为一致（校验模式；保留该旗标使命令行与 plan/04 口径一致）")
    parser.add_argument("--write-manifest", action="store_true", help="写 references/MANIFEST.json")
    args = parser.parse_args(argv)

    rep = Report()
    counts, total = validate(rep)
    for e in rep.errors:
        print("校验错误：%s" % e, file=sys.stderr)
    if rep.errors:
        return 1

    if args.write_manifest:
        manifest = write_manifest(counts, total)
        print("MANIFEST_WRITTEN version=%s words=%d" % (manifest["rulepack_version"], total))
    else:
        print("RULEPACK_OK %s %s words=%d files=%d" % (TOOL_NAME, __version__, total, len(FILE_CATEGORIES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
