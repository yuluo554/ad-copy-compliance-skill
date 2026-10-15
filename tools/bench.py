#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真值基准运行器（M4，plan/04 §5.3）。

一条命令复现评测：加载 data/samples/cases.json → 运行时实算（真喂 check.py 的
生效词条与扫描函数）→ 与 expect_hits 集合**精确比对**（词+类别+行+列，双向集合相等）
→ 人读摘要（stderr/stdout）＋机读 JSON（--report PATH）。

退出码（K4 同族三语义）：
  0 = 全部样例精确匹配（且验收门槛满足）；
  1 = 任一样例不匹配 / 门控拦截（bench 样例词面未被引擎生效）；
  2 = 用法或配置错误（--help 误用、manifest 缺 acceptance.exact_match_required、
      cases/manifest/词表目录缺失等——配置错误不回落代码默认值）。

判定类样例（expect_verdict 非 null）仅供有 LLM 时离线评估，**不进 bench 断言**（K9/D-2）。
零第三方依赖（K7）；无 random / 无时钟 / 无时间戳。
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = _REPO_ROOT / "data" / "samples" / "cases.json"
DEFAULT_MANIFEST = _REPO_ROOT / "data" / "samples" / "manifest.json"
DEFAULT_WORDLISTS = _REPO_ROOT / "references" / "wordlists"
DEFAULT_STATUTES = _REPO_ROOT / "references" / "statutes"

CASE_KEYS = ("id", "kind", "text", "expect_hits", "expect_verdict", "note")
HIT_KEYS = ("word", "category", "line", "col")


def _load_check_module():
    spec = importlib.util.spec_from_file_location(
        "check", str(_REPO_ROOT / "scripts" / "check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fail2(msg):
    print("bench 配置错误：%s" % msg, file=sys.stderr)
    return 2


def load_cases(path):
    """加载并结构校验 cases.json；结构非法视为配置错误（exit 2）。"""
    p = Path(path)
    if not p.is_file():
        raise SystemExit(_fail2("cases 文件不存在：%s" % p))
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(_fail2("cases 文件不可解析：%s" % exc))
    if not isinstance(payload, list) or not payload:
        raise SystemExit(_fail2("cases 结构非法（顶层须为非空数组）"))
    seen_ids = set()
    for c in payload:
        if not isinstance(c, dict) or any(k not in c for k in CASE_KEYS):
            raise SystemExit(_fail2("样例字段不齐（须含 %s）" % "/".join(CASE_KEYS)))
        if "observed" in c:
            raise SystemExit(_fail2("真值混入 observed 类字段（K8 纪律）：%s" % c.get("id")))
        for h in c["expect_hits"]:
            if not isinstance(h, dict) or any(k not in h for k in HIT_KEYS):
                raise SystemExit(_fail2("expect_hits 字段不齐：%s" % c.get("id")))
        if c["id"] in seen_ids:
            raise SystemExit(_fail2("样例 id 重复：%s" % c["id"]))
        seen_ids.add(c["id"])
    return payload


def load_threshold(manifest_path):
    """从 manifest 读 exact_match_required；缺失即配置错误（exit 2，不回落默认值）。"""
    p = Path(manifest_path)
    if not p.is_file():
        raise SystemExit(_fail2("manifest 文件不存在：%s" % p))
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(_fail2("manifest 文件不可解析：%s" % exc))
    acc = manifest.get("acceptance")
    if not isinstance(acc, dict) or "exact_match_required" not in acc:
        raise SystemExit(_fail2("manifest 缺 acceptance.exact_match_required（门槛随数据下发，不回落代码默认值）"))
    req = acc["exact_match_required"]
    if not isinstance(req, (int, float)) or isinstance(req, bool) or not 0.0 <= req <= 1.0:
        raise SystemExit(_fail2("exact_match_required 非法：%r" % (req,)))
    return float(req)


def _bench_words(cases):
    """样例真值涉及的 (word, category) 集合（用于门控拦截判定）。"""
    words = set()
    for c in cases:
        for h in c["expect_hits"]:
            words.add((h["word"], h["category"]))
    return words


def compare_hits(expected, actual):
    """命中集合双向精确比对（词+类别+行+列）。返回 (match, expected_only, actual_only)。"""
    exp = {(h["word"], h["category"], h["line"], h["col"]) for h in expected}
    act = {(h["word"], h["category"], h["line"], h["col"]) for h in actual}
    return exp == act, exp - act, act - exp


def run_bench(cases, wordlists_dir, statutes_dir, check_mod=None):
    """跑基准。返回 (results, summary)；results 逐样例（机读），summary 人读行。"""
    if check_mod is None:
        check_mod = _load_check_module()
    entries, skipped = check_mod._load_entries(Path(wordlists_dir), Path(statutes_dir))

    results = []
    n_pass = 0
    for c in cases:
        # 与 CLI 通路一致：scan_text 之前由入口 _normalize_text 做规范化（K3）
        text = check_mod._normalize_text(c["text"])
        actual = check_mod.scan_text(text, entries)
        match, missing, extra = compare_hits(c["expect_hits"], actual)
        if match:
            n_pass += 1
        results.append({
            "id": c["id"],
            "kind": c["kind"],
            "match": match,
            "missing": [dict(zip(("word", "category", "line", "col"), t)) for t in sorted(missing)],
            "extra": [dict(zip(("word", "category", "line", "col"), t)) for t in sorted(extra)],
        })

    gate_blocked = sorted({(fw, fc, r) for fname, fw, r in skipped
                           for fc in [c for (w2, c) in _bench_words(cases) if w2 == fw]})
    total = len(cases)
    exact_rate = (n_pass / total) if total else 0.0
    summary = {
        "total": total,
        "passed": n_pass,
        "failed": total - n_pass,
        "exact_match_rate": round(exact_rate, 10),
        "gate_blocked": [{"word": w, "category": cat, "reason": r} for w, cat, r in gate_blocked],
    }
    return results, summary



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
    parser = argparse.ArgumentParser(
        prog="bench.py",
        description="广告文案极限词合规体检 · 真值基准运行器（exact-match 双向比对）",
    )
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="cases.json 路径")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="manifest.json 路径（读验收门槛）")
    parser.add_argument("--wordlists-dir", default=str(DEFAULT_WORDLISTS), help="词表目录")
    parser.add_argument("--statutes-dir", default=str(DEFAULT_STATUTES), help="法条目录")
    parser.add_argument("--report", default=None, help="机读 JSON 报告输出路径（缺省只打印摘要）")
    parser.add_argument("--version", action="store_true", help="打印版本后退出")
    args = parser.parse_args(argv)

    if args.version:
        check_mod = _load_check_module()
        print("bench %s" % check_mod.__version__)
        return 0

    req = load_threshold(args.manifest)
    cases = load_cases(args.cases)
    check_mod = _load_check_module()
    try:
        results, summary = run_bench(cases, args.wordlists_dir, args.statutes_dir, check_mod=check_mod)
    except check_mod.InputError as exc:
        return _fail2(str(exc))

    # 门控拦截（样例词面未被引擎生效）按不匹配计（K9：门控拦截 → exit 1）
    n_ok = summary["passed"]
    total = summary["total"]
    rate = n_ok / total if total else 0.0
    ok = (summary["failed"] == 0) and (not summary["gate_blocked"]) and (rate >= req)
    summary["exact_match_rate"] = round(rate, 10)
    summary["exact_match_required"] = req
    summary["verdict"] = "pass" if ok else "fail"

    print("BENCH %s  %d/%d exact-match (required=%.2f)  gate_blocked=%d"
          % (summary["verdict"].upper(), n_ok, total, req, len(summary["gate_blocked"])))
    for r in results:
        if not r["match"]:
            print("FAIL %s (%s): missing=%s extra=%s"
                  % (r["id"], r["kind"],
                     [(m["word"], m["line"], m["col"]) for m in r["missing"]],
                     [(m["word"], m["line"], m["col"]) for m in r["extra"]]))

    if args.report:
        Path(args.report).write_text(
            json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    else:
        print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
