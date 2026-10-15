# -*- coding: utf-8 -*-
"""M3 判定协议结构测试（plan/04 §7 M3 行）。

口径：判定层的执行者是宿主 Agent（决策 D-2），本文件把协议
`references/judgment-protocol.md` 的行为规范编码为**可执行的参考实现**并锁定不变量：

- 字段 schema：判定层只追加 verdict/verdict_reason/verdict_anchor（K10），
  扫描层 7 字段契约不动（K1，HIT_FIELDS 锁定）；
- 注释副本不改位置：word/line/col 等扫描字段与命中集合（条数/顺序）逐字保持；
- 降级路径：off → 纯扫描输出＋全 uncertain＋显式声明；failed → 同（声明含原因）；
- 三态语义边界（exempt 必须有锚点与理由；uncertain 必须说明为何无法判定——非垃圾桶）。

测试构造含词面的输入一律运行时实算（conftest.rulepack_word_tokens，K6/D-10 纪律）。
"""
import json
from pathlib import Path

import pytest

from conftest import ROOT, load_check_module

PROTOCOL = ROOT / "references" / "judgment-protocol.md"

# K10：判定层允许追加的全部字段（白名单，逐字锁定）
JUDGMENT_FIELDS = ("verdict", "verdict_reason", "verdict_anchor")
VALID_VERDICTS = ("confirmed", "exempt", "uncertain")

# K12 统一措辞（协议 §5）：降级声明必须显式出现在输出中
DEGRADED_NOTE_OFF = "仅扫描结果，未经语境判定"


# ---------------------------------------------------------------- 参考实现


def annotate_hit(hit, verdict, reason, anchor):
    """按协议 §0 对单条命中做注释副本：只追加三字段，不动扫描字段。"""
    annotated = dict(hit)  # 浅拷贝后只追加——任何对原字段的改动都会被结构测试抓住
    annotated["verdict"] = verdict
    annotated["verdict_reason"] = reason
    annotated["verdict_anchor"] = anchor
    return annotated


def apply_judgment(hits, judgments):
    """按协议 §0/§3 对命中集合逐条注释（judgments 与 hits 等长时）。"""
    assert len(judgments) == len(hits), "每条命中都必须有一行注释（禁止批量跳过）"
    return [annotate_hit(h, *j) for h, j in zip(hits, judgments)]


def degrade(hits, mode, note_reason=""):
    """按协议 §3 降级：off/failed → 全 uncertain ＋ meta 显式声明。"""
    assert mode in ("off", "failed")
    note = DEGRADED_NOTE_OFF if mode == "off" else "判定失败：%s；%s" % (
        note_reason, DEGRADED_NOTE_OFF)
    annotated = [
        annotate_hit(h, "uncertain", "降级：%s" % DEGRADED_NOTE_OFF, None)
        for h in hits
    ]
    meta = {"judgment": mode, "note": note}
    return annotated, meta


# ---------------------------------------------------------------- 夹具


@pytest.fixture(scope="module")
def check():
    return load_check_module(ROOT / "scripts" / "check.py")


@pytest.fixture()
def real_hits(check):
    """真实词表跑一条合成文案，取扫描层命中作为注释对象（词面运行时实算）。"""
    tokens = [w for w in json.loads(json.dumps(_first_tokens())) if len(w) >= 3]
    assert tokens, "词表 token 实算为空"
    entries, skipped = check._load_entries(
        ROOT / "references" / "wordlists", ROOT / "references" / "statutes")
    assert entries, "真实词表无生效条目"
    text = "本款产品是%s之选，效果出众。\n" % tokens[0]
    hits = check.scan_text(text, entries)
    return hits


def _first_tokens():
    """运行时实算词表词面（≥3 字优先），供夹具组文案用——不内嵌词面于源码。"""
    from conftest import rulepack_word_tokens
    tokens = sorted(rulepack_word_tokens(), key=lambda w: (-len(w), w))
    return [t for t in tokens if len(t) >= 3][:5] or list(rulepack_word_tokens())


# ---------------------------------------------------------------- 协议文档结构


def test_protocol_doc_exists_with_six_sections():
    assert PROTOCOL.is_file(), "references/judgment-protocol.md 未落盘"
    text = PROTOCOL.read_text(encoding="utf-8")
    for marker in ("三态定义", "适用边界", "降级路径", "判定理由与锚点字段口径",
                   "免责与统一措辞", "输入 / 输出"):
        assert marker in text, "协议缺节：%s" % marker


def test_protocol_terms_use_confirmed_not_violated():
    """三态命名全仓口径 = confirmed/exempt/uncertain（HANDOFF-M3 的 violated 为笔误）。"""
    text = PROTOCOL.read_text(encoding="utf-8")
    for term in VALID_VERDICTS:
        assert term in text
    assert "violated" not in text, "协议文档出现既定口径外的三态命名"


def test_protocol_carries_k12_zero_hit_wording():
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "零命中" in text and "不等于合规" in text, "协议缺 K12 零命中≠合规措辞"
    assert "不构成法律意见" in text


# ---------------------------------------------------------------- 字段 schema（K1/K10）


def test_judgment_fields_disjoint_from_scan_contract(check):
    """判定追加字段与扫描 7 字段契约无交集；扫描契约本身未被 M3 改动。"""
    assert list(check.HIT_FIELDS) == [
        "word", "category", "risk", "line", "col", "context", "suggestion",
    ]
    assert not set(JUDGMENT_FIELDS) & set(check.HIT_FIELDS)


def test_annotated_copy_appends_only_three_fields(check, real_hits):
    assert real_hits, "真实词表夹具未产生命中"
    for h in real_hits:
        annotated = annotate_hit(h, "confirmed", "测试理由", {"doc": "advertising-law", "clause": "第九条"})
        assert list(annotated.keys()) == list(h.keys()) + list(JUDGMENT_FIELDS)
        # 扫描字段逐字不动
        for k in check.HIT_FIELDS:
            assert annotated[k] == h[k]


def check_keys(hit):  # noqa: 保留名（历史上误用为模块引用的教训占位）
    return list(hit.keys())


# ---------------------------------------------------------------- 注释不改位置（K10）


def test_annotation_preserves_hits_set_and_positions(real_hits):
    judgments = [("confirmed", "直接向消费者宣称", {"doc": "advertising-law", "clause": "第九条"})] * len(real_hits)
    annotated = apply_judgment(real_hits, judgments)
    assert len(annotated) == len(real_hits), "注释副本不得增删命中"
    scan_keys = ("word", "category", "risk", "line", "col", "context", "suggestion")
    for before, after in zip(real_hits, annotated):
        assert tuple(before[k] for k in scan_keys) == tuple(after[k] for k in scan_keys), \
            "注释副本改动了扫描字段（K10）"


def test_annotation_positions_locate_in_source_text(check, real_hits):
    """注释副本的 (line,col) 仍可在原文逐字定位（位置语义 K3 不因判定而失效）。"""
    entries, _ = check._load_entries(
        ROOT / "references" / "wordlists", ROOT / "references" / "statutes")
    text = "本款产品是%s之选，效果出众。\n" % _first_tokens()[0]
    judgments = [("confirmed", "直接向消费者宣称", {"doc": "advertising-law", "clause": "第九条"})] * len(real_hits)
    annotated = apply_judgment(real_hits, judgments)
    lines = text.split("\n")
    for h in annotated:
        seg = lines[h["line"] - 1][h["col"] - 1: h["col"] - 1 + len(h["word"])]
        assert seg == h["word"], "注释副本位置不可定位：%r" % h


# ---------------------------------------------------------------- 三态语义边界


def test_confirmed_requires_nonempty_anchor_and_reason():
    with pytest.raises(AssertionError):
        _assert_verdict_shape({"verdict": "confirmed", "verdict_reason": "", "verdict_anchor": None})


def test_exempt_requires_anchor_and_reason():
    with pytest.raises(AssertionError):
        _assert_verdict_shape({"verdict": "exempt", "verdict_reason": "没问题", "verdict_anchor": None})
    _assert_verdict_shape({"verdict": "exempt", "verdict_reason": "法定专名语境",
                           "verdict_anchor": {"doc": "advertising-law", "clause": "第九条"}})


def test_uncertain_must_state_why_not_judgeable():
    with pytest.raises(AssertionError):
        _assert_verdict_shape({"verdict": "uncertain", "verdict_reason": "待定", "verdict_anchor": None})
    _assert_verdict_shape({"verdict": "uncertain", "verdict_reason": "证据不足：缺统计口径", "verdict_anchor": None})


def _assert_verdict_shape(annotated):
    """协议 §1 的三态下限校验（宿主 Agent 自检用的口径，测试锁定）。"""
    v = annotated.get("verdict")
    reason = annotated.get("verdict_reason", "")
    anchor = annotated.get("verdict_anchor")
    assert v in VALID_VERDICTS, "verdict 非三态：%r" % (v,)
    assert isinstance(reason, str) and reason.strip(), "verdict_reason 不得为空"
    if v == "confirmed":
        assert anchor is not None, "confirmed 必须给锚点（协议 §1.1）"
        assert "直接" in reason or "宣称" in reason or "明令" in reason or len(reason) >= 8
    if v == "exempt":
        assert anchor is not None, "exempt 必须给锚点——不承认默认豁免（协议 §1.2）"
    if v == "uncertain":
        assert len(reason) >= 6 and ("无法" in reason or "不足" in reason or "歧义" in reason or "降级" in reason), \
            "uncertain 必须说明为何无法判定——非垃圾桶（协议 §1.3）"
    return True


# ---------------------------------------------------------------- 降级路径（协议 §3）


def test_degrade_off_all_uncertain_with_explicit_note(real_hits):
    annotated, meta = degrade(real_hits, "off")
    assert meta["judgment"] == "off"
    assert DEGRADED_NOTE_OFF in meta["note"], "降级声明必须显式出现在输出 meta 中"
    assert len(annotated) == len(real_hits)
    for h in annotated:
        assert h["verdict"] == "uncertain"
    _assert_scan_fields_untouched(real_hits, annotated)


def test_degrade_failed_all_uncertain_with_reason(real_hits):
    annotated, meta = degrade(real_hits, "failed", note_reason="会话内证据不可得")
    assert meta["judgment"] == "failed"
    assert DEGRADED_NOTE_OFF in meta["note"]
    assert "会话内证据不可得" in meta["note"]
    for h in annotated:
        assert h["verdict"] == "uncertain"
    _assert_scan_fields_untouched(real_hits, annotated)


def test_degraded_output_keeps_scanner_stdout_pure(check, real_hits):
    """降级是 Agent 会话内行为：扫描器 stdout 契约不变——7 字段、无 verdict 字段。"""
    entries, _ = check._load_entries(
        ROOT / "references" / "wordlists", ROOT / "references" / "statutes")
    hits = check.scan_text("文字%s文字\n" % _first_tokens()[0], entries)
    for h in hits:
        assert not (set(JUDGMENT_FIELDS) & set(h.keys())), "扫描层 stdout 出现判定字段"


def _assert_scan_fields_untouched(before_list, after_list):
    scan_keys = ("word", "category", "risk", "line", "col", "context", "suggestion")
    for b, a in zip(before_list, after_list):
        assert tuple(b[k] for k in scan_keys) == tuple(a[k] for k in scan_keys)


# ---------------------------------------------------------------- SKILL.md 对齐


def test_skill_md_workflow_aligned_with_protocol():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for term in ("confirmed", "exempt", "uncertain", "judgment-protocol.md"):
        assert term in skill, "SKILL.md 工作流未与协议对齐（缺 %s）" % term
    assert "只注释、不改位置" in skill or "不改位置" in skill
    assert "未经语境判定" in skill, "SKILL.md 缺降级声明措辞"
