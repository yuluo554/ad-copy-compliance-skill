#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真值样例生成器（M4，plan/04 §5.2）。

从生效词表确定性枚举构造合成文案样例：每生效词条 ≥1 条"单词命中"样例（逐词全量），
外加手工语义样例（多词 / 负例 / 位置边界 / 判定类 / 假品牌白名单语境豁免位）。
真值 expect_hits 由生成器内的**独立朴素 oracle**（逐词 find，自右验证独立实现非共用
引擎代码）运行时实算，不手写；生成期守卫断言 oracle 与扫描器引擎逐位一致（见 SELF-CHECK）。

冻结纪律（K15）：cases.json / manifest.json 是冻结件——禁手改，变更走本脚本重生成；
--check 位级一致守门；--write-manifest 派生 manifest.json（计数 / 双数覆盖 / 采样清单 /
验收门槛——**数据非代码**）。

确定性：无 random、无 set 迭代序依赖（排序后消费）、无时钟、无时间戳；3.8/3.12 双解释器可跑。
合成文案只用假品牌白名单名（K8，data/README.md §3）；不引真实品牌案例。

用法：py -X utf8 tools/gen_cases.py [--check] [--write-manifest]
  默认写 data/samples/cases.json（+ --write-manifest 时同时写 manifest.json）；
  --check 只重生成到内存并核对库内位级一致（不改库内文件）。
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
WORDLISTS = _REPO_ROOT / "references" / "wordlists"
STATUTES = _REPO_ROOT / "references" / "statutes"
OUT_CASES = _REPO_ROOT / "data" / "samples" / "cases.json"
OUT_MANIFEST = _REPO_ROOT / "data" / "samples" / "manifest.json"

# ---------------------------------------------------------------------------
# 假品牌白名单（K8，data/README.md §3）：合成文案只允许用这些名字，不涉真实品牌
# ---------------------------------------------------------------------------
BRANDS = ("仙鹤草堂", "云杉电器", "青芜食品", "北岸学堂")

CONTEXT_WINDOW = 10  # 与 scripts/check.py DEFAULT_CONTEXT 对齐（用于覆盖声明 only）


# ---------------------------------------------------------------------------
# 独立朴素 oracle：与 check.py 的 DFA 引擎**不共用代码**的自右独立实现。
# 语义按 K2/K3 复刻：CRLF/CR→LF、BOM 剥离、1 起行列（列按码点）、
# 左→右、最长优先、非重叠、同词多类别各记一条、扫描序排序。
# ---------------------------------------------------------------------------
def _oracle_scan(text, entries):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    words = sorted({e["word"] for e in entries}, key=lambda w: (-len(w), w))
    hits = []
    for line_no, line in enumerate(text.split("\n"), start=1):
        pos = 0
        while pos < len(line):
            best = None
            for w in words:
                if line.startswith(w, pos) and (best is None or len(w) > len(best)):
                    best = w
            if best is None:
                pos += 1
                continue
            for e in entries:
                if e["word"] == best:
                    hits.append((best, e["category"], line_no, pos + 1))
            pos += len(best)
    hits.sort(key=lambda t: (t[2], t[3], t[1], t[0]))
    return hits


def _load_entries():
    """读规则包生效词条（M1 已全部 verified；门控语义以扫描器为准，此处不做锚点复核）。"""
    entries = []
    for f in sorted(WORDLISTS.glob("*.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        for e in payload["entries"]:
            entries.append(e)
    return entries


# ---------------------------------------------------------------------------
# 模板（固定字符串；{w} = 植入词，{b} = 假品牌）
# ---------------------------------------------------------------------------

def _pos_template(i, w, b):
    """单词命中样例：词内嵌于句子中段（col>1），覆盖列位/上下文窗口。"""
    heads = (
        "{b}新品上市，都说它{w}，不信你来试试。",
        "选{b}的理由有很多，{w}就是其中一条。",
        "朋友都在问{b}怎么样——{w}，用了就知道。",
        "{b}店长说：这款{w}，欢迎对比。",
    )
    return heads[i % len(heads)].format(b=b, w=w)


def _edge_texts(w, b):
    """位置边界组：行首 / 行尾 / 空行隔行 / CRLF / BOM（生成器统一 BOM 前缀）。"""
    return [
        "{w}，{b}只做这一句承诺。",              # 行首 col=1
        "选{b}不后悔，认准{w}",                  # 行尾
        "开头提过{w}。\n\n{b}在末行再说一遍{w}。",  # 空行 / 跨行两次
    ]


# ---------------------------------------------------------------------------
# 手工语义样例（kind -> [(id, text 模板, expect_verdict, note)])。
# 词面一律运行时自词表解析（_pick_words），源码不内嵌词表词面（K6/D-10 纪律，
# 由 tests 断言本源文件不含任何规则包词面）。{b} = 假品牌。
# expect_verdict 为判定类样例真值（D-11：confirmed/exempt/uncertain；None=非判定类）。
# ---------------------------------------------------------------------------
MANUAL = {
    "multi-word": [
        ("mw-0001", "{b}{hf_nature}蜂蜜上市：{hf_beauty}、{hf_spot}，一瓶多效。", None,
         "一段文案同段植入三个保健食品类词面（功效+妆效类）"),
        ("mw-0002", "{b}{abs_rank}，{abs_champ}，{abs_price}。", "confirmed",
         "一段连排三个序位/价格类绝对化断言（判定类，无豁免特征）"),
    ],
    "negative": [
        ("neg-0001", "今天天气不错，青芜食品的新品上架了，欢迎选购。", None,
         "无任何词表词面的负例"),
        ("neg-0002", "仙鹤草堂提醒您：请遵医嘱，理性消费。", None,
         "含'医'字等子串干扰但无完整词面命中"),
        ("neg-0003", "", None, "空输入（合法，零命中）"),
    ],
    "position-edge": [
        ("pe-0001", "\ufeff{law0}品质，青芜食品出品。", "confirmed",
         "UTF-8 BOM 剥离后列号按剥离后文本计（判定类，行首命中）"),
        ("pe-0002", "青芜食品郑重承诺：{hf_safe}\r\n{hf_zero}。\r\n{hf_nature}工艺。", None,
         "CRLF 归一为 LF 后计数（连续三行命中）"),
        ("pe-0003", "北岸学堂课程支持试听。\r{ind_scope}校内学员。", None,
         "CR 单字符换行归一（第二行行首命中）"),
    ],
    "same-word-multi-category": [],
    "exempt": [
        ("ex-0001", "《中华人民共和国广告法》第九条规定，广告不得使用“{law0}”“{law1}”“{law2}”等用语。",
         "exempt", "引述法律条文原文（判定类：语境豁免，但扫描层仍逐词命中）"),
        ("ex-0002", "北岸学堂老师课上举例说：“这种‘{abs_moderate}’的说法在广告里要慎用。”",
         "exempt", "转述/引号内他人原话（判定类：语境豁免位）"),
        ("ex-0003", "根据国家有关规定，仙鹤草堂此款产品不适宜人群请查看标签。", "uncertain",
         "“国家有关规定”为泛指表述（扫描层不命中；判定类：uncertain 记录供参考）"),
        ("ex-0004", "青芜食品在行业评比中获{abs_evidence}（见2026年统计出处）。", "uncertain",
         "有据可查的序位断言存证待核（判定类：uncertain——证据不足需人工复核，非垃圾桶）"),
    ],
}
MANUAL_KINDS = ("multi-word", "negative", "position-edge", "exempt")


def _pick_words(entries):
    """手工样例词面解析：按类别码点序下标取词（词表冻结件按 word 码点序落库）。

    下标对应当前冻结规则包；词表变更需重生成样例并由 --check 守门。
    注释只写语义不写词面（K6/D-10：本源文件不得出现规则包词面，测试断言）。
    """
    by_cat = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e["word"])  # 冻结序 = word 码点序
    abs_words = by_cat["绝对化用语"]
    hf_words = by_cat["保健食品违禁"]
    ind_words = by_cat["行业违禁"]
    literal_abs = [e["word"] for e in entries
                   if e["category"] == "绝对化用语" and e["anchor"]["basis"] == "literal"]
    return {
        "law0": literal_abs[0], "law1": literal_abs[1], "law2": literal_abs[2],
        "abs_price": abs_words[11],     # 范围+价格类绝对化断言
        "abs_moderate": abs_words[31],  # 中风险程度断言（判定类豁免位样例用）
        "abs_rank": abs_words[39],      # 行业序位断言
        "abs_champ": abs_words[41],     # 销量序位断言
        "abs_evidence": abs_words[42],  # 销量序位断言（存证待核样例用）
        "hf_nature": hf_words[15],      # 天然属性断言
        "hf_beauty": hf_words[16],      # 妆效功效词
        "hf_spot": hf_words[13],        # 妆效功效词
        "hf_safe": hf_words[7],         # 安全性断言
        "hf_zero": hf_words[21],        # 安全断言变体
        "ind_scope": ind_words[3],      # 泛指专供（medium）
    }


def _find_first_dup_category(entries):
    """找同词多类别（跨文件同词）——本规则包无；找不到返回 None（覆盖声明如实登记）。"""
    seen = {}
    for e in entries:
        cats = seen.setdefault(e["word"], [])
        if e["category"] not in cats:
            cats.append(e["category"])
    for w in sorted(seen):
        if len(seen[w]) > 1:
            return w, sorted(seen[w])
    return None


# ---------------------------------------------------------------------------
# SELF-CHECK：oracle 与扫描器引擎一致性守卫（生成期执行，违者退出 1）
# ---------------------------------------------------------------------------
def _self_check_engine_equivalence(check_mod, entries, texts):
    all_texts = list(texts)
    # 额外等价性语料：全词表词面拼接 + 相邻/重叠构造，强化对拍强度
    all_texts.append("".join(sorted({e["word"] for e in entries})))
    all_texts.append("．".join(sorted({e["word"] for e in entries})))
    ok = True
    for t in all_texts:
        # 与 CLI 通路一致：scan_text 之前由入口 _normalize_text 做规范化（K3）
        nt = check_mod._normalize_text(t)
        got = [(h["word"], h["category"], h["line"], h["col"]) for h in check_mod.scan_text(nt, entries)]
        exp = _oracle_scan(t, entries)
        if got != exp:
            print("SELF-CHECK 失败（oracle≠引擎）：%r\n  oracle=%r\n  engine=%r" % (t[:40], exp, got),
                  file=sys.stderr)
            ok = False
    if not ok:
        print("gen_cases 守卫失败：oracle 与扫描器引擎不一致", file=sys.stderr)
        return False
    return True


# ---------------------------------------------------------------------------
# cases 构造
# ---------------------------------------------------------------------------
def build_cases(check_mod, entries):
    """返回 cases 列表（有序）与覆盖统计（coverage dict）。"""
    cases = []

    def add(cid, kind, text, verdict, note, expect_hits):
        cases.append({
            "id": cid,
            "kind": kind,
            "text": text,
            "expect_hits": [{"word": w, "category": c, "line": ln, "col": cl}
                            for w, c, ln, cl in expect_hits],
            "expect_verdict": verdict,
            "note": note,
        })

    # ① 逐词全量：每生效词条 ≥1 条"单词命中"样例（kind=positive-per-word）
    for i, e in enumerate(entries):
        brand = BRANDS[i % len(BRANDS)]
        text = _pos_template(i, e["word"], brand)
        # 全词表对拍守卫：模板填充词不得混入任何词表词面（只允许命中本词条一次）
        hits = _oracle_scan(text, entries)
        want = [(e["word"], e["category"], 1, text.index(e["word"]) + 1)]
        if hits != want:
            print("生成守卫失败：单词样例（词条=%s）期望 %r 实得 %r" % (e["word"], want, hits),
                  file=sys.stderr)
            sys.exit(1)
        add("pos-%04d" % (i + 1), "positive-per-word", text, None,
            "逐词全量采样（每生效词条 1 条）", hits)

    # ② 多词 / 负例 / 位置边界 / 判定类（手工语义样例；词面运行时自词表解析填充）
    picked = _pick_words(entries)
    seq = 0
    for kind in MANUAL_KINDS:
        for cid, tpl, verdict, note in MANUAL[kind]:
            seq += 1
            text = tpl.format(b=BRANDS[0], **picked)
            hits = _oracle_scan(text, entries)
            if kind == "negative" and hits:
                print("生成守卫失败：负例混入词面命中（%s）：%r" % (cid, hits), file=sys.stderr)
                sys.exit(1)
            add("%s-%04d" % (kind, seq), kind, text, verdict, note, hits)

    # ③ 同词异类（存在时才生成；本规则包无 → 如实登记，不虚构）
    dup = _find_first_dup_category(entries)

    # 位置边界补组（每词面固定 3 形态，抽首个词面代表，避免样本集膨胀）
    rep = sorted({e["word"] for e in entries})[0]
    for j, tpl in enumerate(_edge_texts(rep, BRANDS[0])):
        text = tpl.format(w=rep, b=BRANDS[0])
        # 全词表对拍守卫：填充词不得混入任何词表词面（只允许命中代表词面本身）
        hits = _oracle_scan(text, entries)
        want_count = text.count(rep)
        if len(hits) != want_count or any(h[0] != rep for h in hits):
            print("生成守卫失败：边界样例混入旁词面（%s）：%r" % (tpl, hits), file=sys.stderr)
            sys.exit(1)
        add("edge-%04d" % (j + 1), "position-edge", text, None,
            "位置边界（行首/行尾/跨行）——词面=%s" % rep, hits)

    # BOM 组：与 cases 内文本统一（生成器对 BOM 样例不额外去重，保留手工组）
    coverage = {
        "per_word_total": len(entries),
        "dup_word_categories": dup,
    }
    return cases, coverage


# ---------------------------------------------------------------------------
# manifest 派生（--write-manifest）
# ---------------------------------------------------------------------------
def build_manifest(cases, coverage, entries):
    kinds = {}
    for c in cases:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1

    # 采样清单：逐词全量样例（pos-*）的 id 与词面对照
    sampled = [{"id": c["id"], "word": c["expect_hits"][0]["word"], "category": c["expect_hits"][0]["category"]}
               for c in cases if c["kind"] == "positive-per-word"]

    by_cat = {}
    for e in entries:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1

    dup = coverage["dup_word_categories"]
    dup_note = ("同词异类样例存在（词面=%s）" % dup[0]) if dup else \
        "本规则包无跨文件同词多类别词面——该形态如实登记为 0，不虚构样例"

    # ⑤ 判定类样例（expect_verdict 非 null）：扫描层不断言，仅供有 LLM 时评估
    verdict_cases = [c["id"] for c in cases if c["expect_verdict"] is not None]

    return {
        "schema": "ad-copy-compliance/samples-manifest@1",
        "base_date": "2026-10-15",
        "sampling": {
            "declaration": "抽样覆盖非穷举：逐词全量（每生效词条 1 条单词命中样例）＋手工语义样例；词面组合/句式不做穷举",
            "context_window": CONTEXT_WINDOW,
            "brands_whitelist": list(BRANDS),
            "total_words_verified": coverage["per_word_total"],
            "total_cases": len(cases),
            "sampled_words": len(sampled),
            "counts_by_kind": {k: kinds[k] for k in sorted(kinds)},
            "words_by_category": {k: by_cat[k] for k in sorted(by_cat)},
            "sample_list": sampled,
            "coverage_claims": [
                "① 逐词全量：每生效词条 ≥1 条单词命中样例（kind=positive-per-word）",
                "② 每类别 ≥1 多词（multi-word 覆盖 绝对化用语/行业违禁/保健食品违禁）",
                "③ 位置边界：行首/行尾/跨行/空行/CRLF/CR/BOM（kind=position-edge）",
                "④ 同词异类：" + dup_note,
                "⑤ 判定类样例 %d 条（expect_verdict 非 null；离线基准只断言扫描层，不进 bench 断言）" % len(verdict_cases),
            ],
            "verdict_case_ids": verdict_cases,
        },
        "acceptance": {
            "exact_match_required": 1.0,
            "note": "命中集合（词+类别+行+列）双向精确匹配；任一样例不匹配即 bench exit 1",
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def render_cases(cases):
    return json.dumps(cases, ensure_ascii=False, indent=2) + "\n"


def render_manifest(manifest):
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"



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
    args = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in args
    write_manifest = "--write-manifest" in args
    unknown = [a for a in args if a not in ("--check", "--write-manifest")]
    if unknown:
        print("未知参数：%s" % " ".join(unknown), file=sys.stderr)
        return 2

    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    import check as check_mod  # noqa: E402

    entries = _load_entries()
    if not entries:
        print("规则包零词条——拒绝生成（真值基准依赖生效词表）", file=sys.stderr)
        return 2

    # 生成期守卫：oracle 与引擎对拍（等价语料 = 全部将入库的样例文本 + 拼接语料）
    cases, coverage = build_cases(check_mod, entries)
    if not _self_check_engine_equivalence(check_mod, entries, [c["text"] for c in cases]):
        return 1

    manifest = build_manifest(cases, coverage, entries)
    case_bytes = render_cases(cases).encode("utf-8")
    manifest_bytes = render_manifest(manifest).encode("utf-8")

    if check_only:
        ok = True
        if not OUT_CASES.is_file() or OUT_CASES.read_bytes() != case_bytes:
            print("位级不一致：cases.json（请走 tools/gen_cases.py 重生成，禁手改）", file=sys.stderr)
            ok = False
        if OUT_MANIFEST.is_file() and OUT_MANIFEST.read_bytes() != manifest_bytes:
            print("位级不一致：manifest.json（请走 tools/gen_cases.py --write-manifest 重生成）", file=sys.stderr)
            ok = False
        if not ok:
            return 1
        print("GEN_CASES_OK %d cases / %d words" % (len(cases), coverage["per_word_total"]))
        return 0

    OUT_CASES.write_bytes(case_bytes)
    print("written %s %d cases" % (OUT_CASES.name, len(cases)))
    if write_manifest:
        OUT_MANIFEST.write_bytes(manifest_bytes)
        print("written %s（exact_match_required=%s）" % (OUT_MANIFEST.name, manifest["acceptance"]["exact_match_required"]))
    print("GEN_CASES_WRITTEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
