#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""广告文案极限词合规体检 —— 确定性扫描器（骨架版）。

定位：扫描归扫描、判定归判定。本脚本只做确定性扫描：
输入文案纯文本 → 按 references/wordlists/ 的生效词条做左到右、长词优先、非重叠匹配
→ stdout 输出命中集合 JSON 数组（字段固定：word, category, risk, line, col, context, suggestion）。
不调用任何 LLM、不联网、无第三方依赖。

确定性纪律：
- 同一输入 → 同一命中集合与同一位置（无随机、无时间、无环境依赖）；
- 命中位置可在原文逐字定位（行号/列号均 1 起、按 Unicode 码点；CRLF/CR 归一为 LF 后计数）；
- 词条门控：仅 status=="verified" 且锚点可解析（法条冻结件含该条款；basis=="literal" 时
  词面必须逐字出现于该条款正文）的词条生效；被拒条目在 stderr 显式列出（未启用清单）；
- suggestion 只来自词表内置字段，不做自由生成。

退出码：0 = 扫描完成且零命中；1 = 扫描完成且有条目命中；2 = 用法或输入错误。

匹配引擎为前缀树（M2 DFA 化）：语义严格保持左→右、长词优先、非重叠、
同词多类别各记一条；新旧实现等价对拍见 tests/test_scan_dfa.py。
契约见 SKILL.md 与 plan/04-模块详设.md。
"""

import argparse
import json
import re
import sys
from pathlib import Path

TOOL_NAME = "ad-copy-compliance-check"
__version__ = "0.0.1"

# 输出契约字段（顺序即 JSON 字段序；SKILL.md 契约块须与此完全一致，M5 一致性测试锁定）
HIT_FIELDS = ("word", "category", "risk", "line", "col", "context", "suggestion")

DEFAULT_CONTEXT = 10
VALID_RISKS = ("high", "medium", "low")
STATUS_VERIFIED = "verified"

_REPO_ROOT = Path(__file__).resolve().parent.parent

# 条号只认行首定义位（交叉引用不参与切分）；支持“第X条”“第X条之一”形态
_CLAUSE_RE = re.compile(r"^第[一二三四五六七八九十百零〇两]+条(?:之[一二三四五六七八九十]+)?")


class InputError(Exception):
    """用法或输入错误（对应退出码 2）。"""


def _ensure_utf8_stdio(streams=None):
    """按 stream.encoding 探针，把无法编码中文的流 reconfigure 为 utf-8。

    中文控制台（如 cp936）可正常编码，保持不动；CI/cp1252 等管道编码会被修复。
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


def _normalize_text(raw):
    """剥离 UTF-8 BOM、归一换行（CRLF/CR → LF）。"""
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    return raw.replace("\r\n", "\n").replace("\r", "\n")


def _read_input(path):
    """读取输入文本。path 为 None 或 '-' 时读 stdin。失败抛 InputError。"""
    if path is None or path == "-":
        buffer = getattr(sys.stdin, "buffer", None)
        data = buffer.read() if buffer is not None else sys.stdin.read().encode("utf-8")
    else:
        p = Path(path)
        if not p.exists():
            raise InputError("输入文件不存在：%s" % path)
        if not p.is_file():
            raise InputError("输入路径不是文件：%s" % path)
        data = p.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("输入不可用：非 UTF-8 编码的文本")
    return _normalize_text(text)


def _extract_clause(statute_text, clause):
    """从法条冻结文本中提取条款块；条号只认行首定义位。返回块文本或 None。"""
    lines = statute_text.split("\n")
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = _CLAUSE_RE.match(stripped)
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


def _resolve_anchor(anchor, statutes_dir, word):
    """锚点解析：返回 (条款块 or None, 原因)。

    校验顺序：字段完整 → 锚点文件存在 → 条款可抽取 → literal 词面逐字包含。
    """
    if not isinstance(anchor, dict):
        return None, "缺锚点"
    doc = str(anchor.get("doc", "")).strip()
    clause = str(anchor.get("clause", "")).strip()
    basis = str(anchor.get("basis", "")).strip()
    if not doc or not clause or basis not in ("literal", "variant"):
        return None, "锚点字段不完整"
    path = Path(statutes_dir) / (doc + ".txt")
    if not path.is_file():
        return None, "锚点文件缺失（%s）" % path.name
    try:
        statute_text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None, "锚点文件不可读（%s）" % path.name
    block = _extract_clause(statute_text, clause)
    if block is None:
        return None, "条款解析不到（%s）" % clause
    if basis == "literal" and word not in block:
        return None, "literal 词面未见于条款"
    return block, None


def _load_entries(wordlists_dir, statutes_dir):
    """加载生效词条。返回 (entries, skipped)。

    skipped 为 [(文件名, 词, 原因)]；被拒条目必须显式列出（未启用清单）。
    wordlists_dir 不存在 → 抛 InputError（路径不存在要大声说，不静默空扫）。
    """
    wdir = Path(wordlists_dir)
    if not wdir.is_dir():
        raise InputError("词表目录不存在：%s" % wordlists_dir)
    entries = []
    skipped = []

    for jf in sorted(wdir.glob("*.json")):
        try:
            payload = json.loads(jf.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            skipped.append((jf.name, "-", "词表文件不可解析"))
            continue
        if not isinstance(payload, dict):
            skipped.append((jf.name, "-", "词表文件结构非法（顶层须为对象）"))
            continue
        file_category = str(payload.get("category", "")).strip()
        raw_entries = payload.get("entries", [])
        if not isinstance(raw_entries, list):
            skipped.append((jf.name, "-", "entries 字段非数组"))
            continue
        for entry in raw_entries:
            if not isinstance(entry, dict):
                skipped.append((jf.name, "-", "条目非对象"))
                continue
            word = str(entry.get("word", "")).strip()
            if not word:
                skipped.append((jf.name, "-", "缺 word"))
                continue
            category = str(entry.get("category", "")).strip()
            risk = str(entry.get("risk", "")).strip()
            suggestion = str(entry.get("suggestion", "")).strip()
            status = str(entry.get("status", "")).strip()
            if not category or (file_category and category != file_category):
                skipped.append((jf.name, word, "category 缺失或与文件声明不一致"))
                continue
            if risk not in VALID_RISKS:
                skipped.append((jf.name, word, "risk 非法（须为 %s）" % "/".join(VALID_RISKS)))
                continue
            if not suggestion:
                skipped.append((jf.name, word, "缺 suggestion"))
                continue
            if status != STATUS_VERIFIED:
                skipped.append((jf.name, word, "status 非 verified"))
                continue
            block, reason = _resolve_anchor(entry.get("anchor"), statutes_dir, word)
            if reason is not None:
                skipped.append((jf.name, word, reason))
                continue
            entries.append({"word": word, "category": category, "risk": risk, "suggestion": suggestion})
    return entries, skipped


def _make_hit(entry, line, col0, line_no, context_window):
    start = max(0, col0 - context_window)
    end = min(len(line), col0 + len(entry["word"]) + context_window)
    return {
        "word": entry["word"],
        "category": entry["category"],
        "risk": entry["risk"],
        "line": line_no,
        "col": col0 + 1,
        "context": line[start:end],
        "suggestion": entry["suggestion"],
    }


def build_dfa(entries):
    """把生效词条编译成前缀树（嵌套 dict），节点 = (children, terminal_states)。

    terminal_states 内为 (word, category, risk, suggestion) 元组：同词多类别各占
    一项，遍历顺序由编译方保证（构造期已按词长降序、(category, word) 升序排定，
    见 scan_text 契约）；树内不排序，命中序由编译期序决定。
    """
    root = ({}, [])
    for e in entries:
        node = root
        for ch in e["word"]:
            children = node[0]
            nxt = children.get(ch)
            if nxt is None:
                nxt = ({}, [])
                children[ch] = nxt
            node = nxt
        node[1].append((e["word"], e["category"], e["risk"], e["suggestion"]))
    return root


def scan_text(text, entries, context_window=DEFAULT_CONTEXT):
    """确定性扫描：左到右、长词优先、非重叠；返回命中列表（排序=扫描序）。

    匹配用前缀树（build_dfa 编译）：每个位置沿树下行，遇到终止节点即得该处
    可匹配的全部条目；取词面最长者（同长取编译序首个），命中段消费后从段尾
    继续（非重叠）。同一命中段、同词、多类别 → 各记一条（终止节点内按去重键
    消费，不重复输出）。
    排序稳定：先按 (line, col)，同位内按 (category, word) 码点序。
    """
    trie = build_dfa(entries)
    root_children = trie[0]
    hits = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        pos = 0
        n = len(line)
        while pos < n:
            node = None
            children = root_children
            # 沿树下行到最深可达节点，沿途最深的"有终止条目"的节点即最长匹配
            # （更深的节点若无终止条目，则该路径上不存在更长可命中词——词面必须终止于某节点）
            children = root_children
            depth = 0
            last = None
            while True:
                nxt = children.get(line[pos + depth]) if pos + depth < n else None
                if nxt is None:
                    break
                depth += 1
                if nxt[1]:
                    last = nxt
                children = nxt[0]
            # last = 沿途最深的"有终止条目"的节点：词面最长的匹配（超过它的
            # 更深节点若无终止条目，则不存在更长可命中词——词面必须终止于某节点）
            if last is None:
                pos += 1
                continue
            seen = set()
            for word, category, risk, suggestion in last[1]:
                key = (word, category)
                if key in seen:
                    continue
                seen.add(key)
                entry = {"word": word, "category": category, "risk": risk, "suggestion": suggestion}
                hits.append(_make_hit(entry, line, pos, line_no, context_window))
            pos += len(last[1][0][0])
    hits.sort(key=lambda h: (h["line"], h["col"], h["category"], h["word"]))
    return hits


def _emit_json(hits):
    sys.stdout.write(json.dumps(hits, ensure_ascii=False, indent=2) + "\n")


def _emit_text(hits):
    for h in hits:
        sys.stdout.write(
            "{line}:{col}\t{word}\t[{category}/{risk}]\t{context}\n".format(**h)
        )
    sys.stdout.write("共 {n} 条命中\n".format(n=len(hits)))


def _selftest():
    """内置合成数据自检（进 CI 冒烟）：位置语义 + 负例。

    自检词面为合成占位串，与真实词表无关，避免与“脚本源码不得内嵌词表词面”门禁冲突。
    """
    text = _normalize_text("自检占位词甲出现了两次：自检占位词甲。\n第二行也有自检占位词乙。")
    entries = [
        {
            "word": "自检占位词甲",
            "category": "绝对化用语",
            "risk": "high",
            "suggestion": "改为可核实的客观表述",
        },
        {
            "word": "自检占位词乙",
            "category": "绝对化用语",
            "risk": "medium",
            "suggestion": "删除或改为具体事实描述",
        },
    ]
    hits = scan_text(text, entries)
    expected = [("自检占位词甲", 1, 1), ("自检占位词甲", 1, 13), ("自检占位词乙", 2, 6)]
    got = [(h["word"], h["line"], h["col"]) for h in hits]
    negative_ok = scan_text("今天天气不错，正常的一句话。", entries) == []
    if got == expected and negative_ok:
        print("SELFTEST_OK %s %s" % (TOOL_NAME, __version__))
        return 0
    print("SELFTEST_FAIL：got=%r expected=%r negative_ok=%r" % (got, expected, negative_ok), file=sys.stderr)
    return 1


def main(argv=None):
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="check.py",
        description="广告文案极限词合规体检 · 确定性扫描器（骨架版）",
    )
    parser.add_argument("input", nargs="?", default=None,
                        help="文案文件路径（UTF-8）；省略或 - 表示从 stdin 读取")
    parser.add_argument("--wordlists-dir", default=None,
                        help="分类词表目录（默认：仓库 references/wordlists/）")
    parser.add_argument("--statutes-dir", default=None,
                        help="法条冻结目录（默认：仓库 references/statutes/）")
    parser.add_argument("--context", type=int, default=DEFAULT_CONTEXT,
                        help="上下文窗口：命中处左右各 N 字符（默认 %d）" % DEFAULT_CONTEXT)
    parser.add_argument("--format", choices=("json", "text"), default="json",
                        help="输出格式（text 为展示用，非机器契约）")
    parser.add_argument("--exit-zero", action="store_true",
                        help="有命中时仍以退出码 0 结束（纯报告用途）")
    parser.add_argument("--version", action="store_true", help="打印版本后退出")
    parser.add_argument("--selftest", action="store_true", help="内置合成数据自检")
    args = parser.parse_args(argv)

    if args.version:
        print("%s %s" % (TOOL_NAME, __version__))
        return 0
    if args.selftest:
        return _selftest()
    if args.context < 0:
        parser.error("--context 必须 >= 0")

    wdir = Path(args.wordlists_dir) if args.wordlists_dir else _REPO_ROOT / "references" / "wordlists"
    sdir = Path(args.statutes_dir) if args.statutes_dir else _REPO_ROOT / "references" / "statutes"

    try:
        text = _read_input(args.input)
        entries, skipped = _load_entries(wdir, sdir)
    except InputError as exc:
        print("输入错误：%s" % exc, file=sys.stderr)
        return 2

    for fname, word, reason in skipped:
        print("未启用条目：%s / %s / %s" % (fname, word, reason), file=sys.stderr)
    if not entries:
        print("提示：当前无生效词条（词表未落库或全部未通过核对）——本次扫描为零命中。", file=sys.stderr)

    hits = scan_text(text, entries, args.context)
    if args.format == "text":
        _emit_text(hits)
    else:
        _emit_json(hits)
    if hits and not args.exit_zero:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
