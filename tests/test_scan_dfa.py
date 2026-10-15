# -*- coding: utf-8 -*-
"""M2 扫描引擎测试：DFA 化等价对拍、长词优先/非重叠/同词异类、位置边界。

对拍基线：文件内内嵌一份旧实现逐字拷贝（M0/M1 线上语义，见 git 历史
1167d4a 版 scan_text），对真实词表全量 133 词构造语料 + --context 边界
(0/3/10) 逐字节比对。真实词面只出现在对拍语料动态构造中（运行时从规则
包读入），脚本源码不内嵌词表词面（K6 门禁词面豁免路径见 conftest.py）。
"""
import glob
import importlib.util
import json
import random
from pathlib import Path

import pytest

from conftest import load_check_module

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check.py"

mod = load_check_module(CHECK)

# --- 旧实现逐字拷贝（M1 冻结语义，对拍基线；改动即失真） -------------------


def _baseline_scan(text, entries, context_window=10):
    by_first = {}
    for e in entries:
        by_first.setdefault(e["word"][0], []).append(e)
    for ch in by_first:
        by_first[ch].sort(key=lambda e: (-len(e["word"]), e["category"], e["word"]))
    hits = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        pos = 0
        n = len(line)
        while pos < n:
            bucket = by_first.get(line[pos])
            if not bucket:
                pos += 1
                continue
            matched_word = None
            for e in bucket:
                if line.startswith(e["word"], pos):
                    matched_word = e["word"]
                    break
            if matched_word is None:
                pos += 1
                continue
            seen = set()
            for e in bucket:
                if e["word"] != matched_word or not line.startswith(e["word"], pos):
                    continue
                key = (e["word"], e["category"])
                if key in seen:
                    continue
                seen.add(key)
                hits.append(mod._make_hit(e, line, pos, line_no, context_window))
            pos += len(matched_word)
    hits.sort(key=lambda h: (h["line"], h["col"], h["category"], h["word"]))
    return hits


# --- 真实词表全量夹具（运行时实算，不内嵌词面） ---------------------------


def _real_entries():
    entries = []
    for f in sorted(glob.glob(str(ROOT / "references" / "wordlists" / "*.json"))):
        payload = json.loads(Path(f).read_text(encoding="utf-8"))
        for e in payload["entries"]:
            entries.append(
                {"word": e["word"], "category": payload["category"],
                 "risk": e["risk"], "suggestion": e["suggestion"]}
            )
    return entries


@pytest.fixture(scope="module")
def real_entries():
    entries = _real_entries()
    assert len(entries) == 133  # M1 冻结计数；规则包变更时此数随之重核
    return entries


def _corpora(entries):
    words = [e["word"] for e in entries]
    rng = random.Random(20261015)
    corpora = []
    for _ in range(120):  # 词与词粘连拼接，制造重叠/长词优先竞争
        corpora.append("".join(rng.choice(words) for _ in range(rng.randint(1, 12))))
    for _ in range(80):  # 混入标点/括号/空白的模板文案
        corpora.append(rng.choice(
            ["本产品%s效果第一", "国家级%s认证", "%s治愈，%s保证", "无风险%s保本保收益",
             "（%s）「%s」】%s", "%s"]
        ).format(*[rng.choice(words) for _ in range(3)]))
    corpora += ["", "\n", "无", "词", "的", "\n\n", "a" * 200,
                "\n".join(words[:50]), "".join(words), "".join(reversed(words))]
    return corpora


def test_dfa_equivalence_with_baseline_over_real_wordlist(real_entries):
    corpora = _corpora(real_entries)
    checked = 0
    for text in corpora:
        for cw in (0, 3, 10):
            old = _baseline_scan(text, real_entries, cw)
            new = mod.scan_text(text, real_entries, cw)
            assert json.dumps(old, ensure_ascii=False) == json.dumps(new, ensure_ascii=False)
            checked += 1
    assert checked >= 600  # 210 语料 × 3 上下文，量级防呆
    # 语料非全空：确认对拍有真实命中而非空洞通过
    assert sum(len(mod.scan_text(t, real_entries)) for t in corpora) > 1000


def test_dfa_output_invariant_to_entry_order(real_entries):
    """新实现对词条传入顺序不敏感（终止节点序被全局排序归一）。"""
    words = [e["word"] for e in real_entries]
    rng = random.Random(7)
    text = "".join(rng.choice([w for w in words if len(w) == 2]) for _ in range(60))
    baseline = json.dumps(mod.scan_text(text, real_entries), ensure_ascii=False, sort_keys=True)
    for _ in range(10):
        shuffled = real_entries[:]
        rng.shuffle(shuffled)
        assert json.dumps(mod.scan_text(text, shuffled), ensure_ascii=False, sort_keys=True) == baseline


def test_longest_match_wins_and_non_overlapping(real_entries):
    """长词优先 + 非重叠：从规则包运行时选一对前缀词（短词是长词前缀）实测。"""
    words = [e["word"] for e in real_entries]
    pair = None
    for long_w in sorted(words, key=len, reverse=True):
        for short_w in words:
            if len(short_w) < len(long_w) and long_w.startswith(short_w):
                pair = (short_w, long_w)
                break
        if pair:
            break
    assert pair, "词表中应存在前缀词对"
    short_w, long_w = pair
    by_word = {e["word"]: e for e in real_entries}
    entries = [by_word[short_w], by_word[long_w]]
    # 长词在前：应整段命中长词、消费后不再命中其中的短词（非重叠）
    hits = mod.scan_text(long_w, entries)
    assert [(h["word"], h["line"], h["col"]) for h in hits] == [(long_w, 1, 1)]
    # 短词单独出现仍命中（"x词 y词 z"：第二处词面从 x+空格+y 之后起算）
    hits = mod.scan_text("x%s y%s z" % (short_w, short_w), entries)
    assert [(h["word"], h["col"]) for h in hits] == [(short_w, 2), (short_w, 2 + len(short_w) + 2)]


def test_same_word_two_categories_each_recorded():
    """同词多类别各记一条（同文件两类别 + 跨文件同词两种形态）。"""
    entries = [
        {"word": "自检占位词甲", "category": "类一", "risk": "high", "suggestion": "改写一"},
        {"word": "自检占位词甲", "category": "类二", "risk": "low", "suggestion": "改写二"},
        {"word": "自检占位词甲", "category": "类二", "risk": "low", "suggestion": "改写二"},  # 全同条目不重复
    ]
    hits = mod.scan_text("看看自检占位词甲", entries)
    assert [(h["word"], h["category"], h["risk"]) for h in hits] == [
        ("自检占位词甲", "类一", "high"),
        ("自检占位词甲", "类二", "low"),
    ]
    # 跨文件同词：模拟两个类别文件的词条合并传入（K5 允许，逐类别各记一条）
    hits = mod.scan_text("前缀自检占位词甲\n第二行自检占位词甲", entries)
    assert [(h["line"], h["col"], h["category"]) for h in hits] == [
        (1, 3, "类一"), (1, 3, "类二"), (2, 4, "类一"), (2, 4, "类二"),
    ]


def test_position_semantics_bom_crlf_cr_multiline(real_entries):
    """K3：BOM 剥离、CRLF/CR 归一 LF 后 1 起码点列。选一个 2 字词实测。"""
    word = next(e["word"] for e in real_entries if len(e["word"]) == 2)
    by_word = {e["word"]: e for e in real_entries}
    entries = [by_word[word]]
    raw = "\ufeff前缀%s，\r\n%s在行首\r孤%s行\n" % (word, word, word)
    text = mod._normalize_text(raw)
    hits = mod.scan_text(text, entries)
    assert [(h["line"], h["col"]) for h in hits] == [(1, 3), (2, 1), (3, 2)]
    lines = text.split("\n")
    for h in hits:  # 位置逐字可定位
        assert lines[h["line"] - 1][h["col"] - 1:h["col"] - 1 + len(h["word"])] == h["word"]


def test_context_window_boundaries(real_entries):
    word = next(e["word"] for e in real_entries if len(e["word"]) == 2)
    by_word = {e["word"]: e for e in real_entries}
    entries = [by_word[word]]
    line = "甲乙丙丁%s戊己庚辛壬癸" % word  # 前后各 4 字
    # 窗口 3：命中列 5，左边界 5-1-3=1 → 从"乙"起
    hits = mod.scan_text(line, entries, context_window=3)
    assert hits[0]["context"] == "乙丙丁%s戊己庚" % word
    # 窗口 0：仅词面
    assert mod.scan_text(line, entries, context_window=0)[0]["context"] == word
    # 窗口 10 超出行长：截到行边界
    hits = mod.scan_text(line, entries, context_window=10)
    assert hits[0]["context"] == line
    # 窗口超出词长：右边界为词尾+窗口（切片 min 保护）
    short_line = "%s" % word
    assert mod.scan_text(short_line, entries, context_window=1)[0]["context"] == word


def test_empty_and_whitespace_inputs(real_entries):
    assert mod.scan_text("", real_entries) == []
    assert mod.scan_text("\n\n\n", real_entries) == []
    assert mod.scan_text("   \t \n  ", real_entries) == []


def test_real_wordlist_end_to_end_hits(real_entries):
    """真实词表端到端：多类别命中、位置正确（词面运行时取，不内嵌）。"""
    pool = {}
    for e in real_entries:
        pool.setdefault(e["category"], e["word"])
    w1, w2, w3 = pool["绝对化用语"], pool["医疗违禁"], pool["行业违禁"]
    text = "开头%s中间%s结尾%s。\n第二行无命中。" % (w1, w2, w3)
    c2 = 3 + len(w1) + 2  # "中间"两字
    c3 = c2 + len(w2) + 2  # "结尾"两字
    hits = mod.scan_text(text, real_entries)
    assert [(h["word"], h["line"], h["col"], h["category"]) for h in hits] == [
        (w1, 1, 3, "绝对化用语"), (w2, 1, c2, "医疗违禁"), (w3, 1, c3, "行业违禁"),
    ]
    for h in hits:
        assert set(h) == set(mod.HIT_FIELDS)
