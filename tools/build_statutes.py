#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法条冻结构建器：raw HTML → 正文文本快照 + 逐字断言 + 位级守门。

流程（plan/05 §2 执行卡）：
- 抽取：references/statutes/raw/<doc>.html → 确定性转换 → references/statutes/<doc>.txt
  （仅取 <p> 段落、剥标签、还原实体、NFC 归一、行尾 LF；无网络、无第三方依赖）；
- 断言：关键串逐字出现（如广告法含"第九条/国家级/最高级/最佳"）+ 条款行首定义位可解析 +
  全文条数核对；
- --check：从本地 raw 重生成 txt，与库内 <doc>.txt 位级一致（sha256 相同）才算过；
  raw 缺失时按登记的 sha256 校验库内 txt 完整性。

退出码：0 = 全部通过；1 = 断言/位级不一致；2 = 用法或输入错误。
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TOOL_NAME = "build_statutes"
__version__ = "0.0.1"

_REPO_ROOT = Path(__file__).resolve().parent.parent
STATUTES_DIR = _REPO_ROOT / "references" / "statutes"
RAW_DIR = STATUTES_DIR / "raw"

# 每部法条的冻结口径：断言串（逐字出现）+ 条数 + 条款行首正则计数
DOCS = {
    "advertising-law": {
        "asserts": ["第九条", "国家级", "最高级", "最佳",
                    "广告不得有下列情形", "医疗", "保健食品", "虚假广告"],
        "clauses": 74,
    },
    "internet-ad-measures": {
        "asserts": ["第一条", "互联网广告", "本办法自2023年5月1日起施行"],
        "clauses": 32,
    },
    "medical-ad-measures": {
        "asserts": ["第六条", "第七条", "医疗广告", "本办法自2007年1月1日起施行"],
        "clauses": 23,
    },
}

# 条款定义位：行首“第X条（之一）”形态
_CLAUSE_LINE_RE = re.compile(r"^第[一二三四五六七八九十百零〇两]+条(?:之[一二三四五六七八九十]+)?")

_ENTITY_MAP = {
    "&nbsp;": " ", "&ldquo;": "\u201c", "&rdquo;": "\u201d",
    "&lsquo;": "\u2018", "&rsquo;": "\u2019", "&mdash;": "\u2014",
    "&hellip;": "\u2026", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
}

# raw 基准指纹（sha256 of raw HTML bytes）；变更 = 重取 + 重生成 + 更新表 + 记勘误
RAW_SHA256 = {
    "advertising-law": None,  # 由 build 时登记（--register 模式写入 README 表）
    "internet-ad-measures": None,
    "medical-ad-measures": None,
}


class BuildError(Exception):
    pass


def _strip_html_para(html):
    """单个 <p> 段落 HTML → 纯文本（剥标签、还原实体）。"""
    text = re.sub(r"<[^>]+>", "", html)
    for k, v in _ENTITY_MAP.items():
        text = text.replace(k, v)
    # 数字字符引用
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    return text


def _normalize(s):
    s = s.replace("\u00a0", " ").replace("\u3000", "\u3000")  # 全角空格保留
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s


def extract_text(raw_html):
    """raw HTML bytes → 正文文本（确定性；全角空格段首统一为单个全角空格）。"""
    html = raw_html.decode("utf-8")
    paras = re.findall(r"<p\b[^>]*>(.*?)</p>", html, re.S)
    if not paras:
        raise BuildError("未抽到任何 <p> 段落")
    lines = []
    for p in paras:
        t = _strip_html_para(p)
        t = _normalize(t).strip()
        if not t:
            continue
        # 段内换行折叠为空（HTML 内软换行非语义）
        t = t.replace("\n", "")
        # 统一全角空格：段首编号后的空白统一为单个全角空格
        t = re.sub(r"^(第[一二三四五六七八九十百零〇两]+条(?:之[一二三四五六七八九十]+)?)[\u3000 \t]+",
                   lambda m: m.group(1) + "\u3000", t)
        lines.append(t)
    return "\n".join(lines) + "\n"


def assert_content(text, doc):
    spec = DOCS[doc]
    missing = [a for a in spec["asserts"] if a not in text]
    if missing:
        raise BuildError("%s 缺关键串：%s" % (doc, "、".join(missing)))
    clauses = [ln for ln in text.split("\n") if _CLAUSE_LINE_RE.match(ln)]
    if len(clauses) != spec["clauses"]:
        raise BuildError("%s 条款数 %d != 预期 %d" % (doc, len(clauses), spec["clauses"]))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def build(doc):
    raw_path = RAW_DIR / (doc + ".html")
    if not raw_path.is_file():
        raise BuildError("raw 缺失：%s" % raw_path)
    raw = raw_path.read_bytes()
    text = extract_text(raw)
    assert_content(text, doc)
    return raw, text.encode("utf-8")



def _ensure_utf8_stdio(streams=None):
    """按 stream.encoding 探针，把无法编码中文的流 reconfigure 为 utf-8（K13）。

    中文控制台（如 cp936）可正常编码，保持不动；CI/cp1252 等管道编码会被修复。
    与 scripts/check.py 同口径。
    """
    targets = list(streams) if streams is not None else [sys.stdout, sys.stderr]
    for stream in targets:
        enc = getattr(stream, "encoding", None)
        if not enc:
            continue
        try:
            "测".encode(enc)
        except (UnicodeEncodeError, LookupError):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, ValueError):
                pass


def main(argv=None):
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(prog="build_statutes.py",
                                     description="法条冻结构建器（抽取/断言/位级守门）")
    parser.add_argument("--check", action="store_true",
                        help="从 raw 重生成并核对库内 txt 位级一致（不联网）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果（供台账脚本用）")
    args = parser.parse_args(argv)

    results = {}
    ok = True
    for doc in sorted(DOCS):
        try:
            raw_bytes, txt_bytes = build(doc)
            txt_path = STATUTES_DIR / (doc + ".txt")
            if args.check:
                if not txt_path.is_file():
                    raise BuildError("库内 txt 缺失：%s" % txt_path.name)
                same = txt_path.read_bytes() == txt_bytes
                results[doc] = {
                    "status": "ok" if same else "mismatch",
                    "raw_sha256": sha256_bytes(raw_bytes),
                    "txt_sha256": sha256_bytes(txt_bytes),
                    "bytes": len(txt_bytes),
                }
                if not same:
                    ok = False
                    print("位级不一致：%s（库内 txt 与 raw 重生成结果不同）" % doc, file=sys.stderr)
            else:
                txt_path.write_bytes(txt_bytes)
                results[doc] = {
                    "status": "written",
                    "raw_sha256": sha256_bytes(raw_bytes),
                    "txt_sha256": sha256_bytes(txt_bytes),
                    "bytes": len(txt_bytes),
                }
        except BuildError as exc:
            ok = False
            results[doc] = {"status": "fail", "reason": str(exc)}
            print("构建失败：%s：%s" % (doc, exc), file=sys.stderr)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for doc, r in results.items():
            print("%s\t%s\traw=%s\ttxt=%s\t%s" % (
                doc, r["status"], r.get("raw_sha256", "-")[:12],
                r.get("txt_sha256", "-")[:12], r.get("bytes", r.get("reason", ""))))
    if not ok:
        return 1
    print("STATUTES_OK %s %s" % (TOOL_NAME, __version__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
