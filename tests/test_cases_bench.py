# -*- coding: utf-8 -*-
"""M4 真值基准测试：冻结件 schema/双数覆盖/门槛随 manifest/退出码三语义/三形态探活（端到端必红）。

探活铁律：三形态全部打到端到端入口（subprocess 起 bench 主函数，断言进程退出码 != 0），
不断言"调了某内部函数"——只红在调用面不红在入口的探活不算数。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT, load_check_module, rulepack_word_tokens

CASES = ROOT / "data" / "samples" / "cases.json"
MANIFEST = ROOT / "data" / "samples" / "manifest.json"
BENCH = ROOT / "tools" / "bench.py"
GEN_CASES = ROOT / "tools" / "gen_cases.py"
WORDLISTS = ROOT / "references" / "wordlists"
STATUTES = ROOT / "references" / "statutes"

PY = sys.executable


def _run_bench(args, cwd=ROOT):
    return subprocess.run(
        [PY, "-X", "utf8", str(BENCH)] + args,
        cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
        env={"PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
             "PATH": __import__("os").environ.get("PATH", "")},
    )


def _run_gen_cases(args):
    return subprocess.run(
        [PY, "-X", "utf8", str(GEN_CASES)] + args,
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
        env={"PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
             "PATH": __import__("os").environ.get("PATH", "")},
    )


# ---------------------------------------------------------------------------
# 冻结件 schema 与纪律
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def cases():
    return json.loads(CASES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_cases_schema_and_frozen_fields(cases):
    assert cases, "cases 为空"
    for c in cases:
        assert set(c) == {"id", "kind", "text", "expect_hits", "expect_verdict", "note"}
        assert c["kind"] in ("positive-per-word", "multi-word", "negative",
                             "position-edge", "same-word-multi-category", "exempt")
        assert c["expect_verdict"] in ("confirmed", "exempt", "uncertain", None)
        for h in c["expect_hits"]:
            assert set(h) == {"word", "category", "line", "col"}
            assert isinstance(h["line"], int) and h["line"] >= 1
            assert isinstance(h["col"], int) and h["col"] >= 1


def test_cases_no_observed_fields(cases):
    """K8：真值只存输入与期望——出现 observed 类字段即缺陷。"""
    for c in cases:
        assert "observed" not in c, "样例 %s 混入 observed 字段" % c["id"]
        for h in c["expect_hits"]:
            assert "observed" not in h
    raw = CASES.read_text(encoding="utf-8")
    assert "observed" not in raw, "cases.json 原文中出现 observed 词面"


def test_case_ids_unique_and_dense(cases):
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    for c in cases:
        assert c["note"], "样例 %s 缺植入说明" % c["id"]


def test_negative_cases_expect_empty(cases):
    neg = [c for c in cases if c["kind"] == "negative"]
    assert neg, "缺负例"
    for c in neg:
        assert c["expect_hits"] == [], "负例 %s expect_hits 非空" % c["id"]


def test_verdict_cases_not_empty(cases):
    """判定类样例存在（D-11 枚举），且只登记 expect_verdict（扫描层不断言 verdict）。"""
    v = [c for c in cases if c["expect_verdict"] is not None]
    assert v, "缺判定类样例"
    assert all(c["expect_verdict"] in ("confirmed", "exempt", "uncertain") for c in v)


# ---------------------------------------------------------------------------
# manifest：双数覆盖 / 采样清单 / 门槛（数据非代码）
# ---------------------------------------------------------------------------
def test_manifest_counts_match_cases(cases, manifest):
    s = manifest["sampling"]
    assert s["total_cases"] == len(cases)
    assert sum(s["counts_by_kind"].values()) == len(cases)
    per_word = [c for c in cases if c["kind"] == "positive-per-word"]
    assert s["total_words_verified"] == s["sampled_words"] == len(per_word)


def test_manifest_sampling_declaration(cases, manifest):
    s = manifest["sampling"]
    assert "非穷举" in s["declaration"], "覆盖声明必须显式承认抽样非穷举"
    assert s["sample_list"], "缺采样清单"
    per_word_ids = {c["id"] for c in cases if c["kind"] == "positive-per-word"}
    assert {e["id"] for e in s["sample_list"]} == per_word_ids


def test_manifest_coverage_claims_five_kinds(manifest):
    claims = manifest["sampling"]["coverage_claims"]
    assert len(claims) == 5, "覆盖口径须按 plan/04 §5.2 ①–⑤ 五条登记"
    assert any("同词异类" in c for c in claims)


def test_manifest_acceptance_threshold(manifest):
    """门槛随 manifest 下发（数据非代码）；缺失/非法由 bench 侧测试锁定 exit 2。"""
    req = manifest["acceptance"]["exact_match_required"]
    assert req == 1.0


# ---------------------------------------------------------------------------
# gen_cases --check 位级守门（K15）
# ---------------------------------------------------------------------------
def test_gen_cases_check_bit_identical():
    r = _run_gen_cases(["--check"])
    assert r.returncode == 0, "gen_cases --check 失败：\n%s%s" % (r.stdout, r.stderr)
    assert "GEN_CASES_OK" in r.stdout


def test_gen_cases_rejects_unknown_arg():
    r = _run_gen_cases(["--frobnicate"])
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# bench 端到端：exit 0 全绿 / exit 1 / exit 2 三语义
# ---------------------------------------------------------------------------
def test_bench_end_to_end_green():
    r = _run_bench(["--report", str(ROOT / "data" / "samples" / ".bench-report.tmp.json")])
    try:
        assert r.returncode == 0, "bench 未全绿：\n%s%s" % (r.stdout, r.stderr)
        assert "BENCH PASS" in r.stdout
        report = json.loads((ROOT / "data" / "samples" / ".bench-report.tmp.json").read_text(encoding="utf-8"))
        assert report["summary"]["verdict"] == "pass"
        assert report["summary"]["exact_match_rate"] == 1.0
        assert report["summary"]["total"] == report["summary"]["passed"]
        assert len(report["results"]) == report["summary"]["total"]
    finally:
        (ROOT / "data" / "samples" / ".bench-report.tmp.json").unlink(missing_ok=True)


def test_bench_exit2_manifest_missing(tmp_path):
    r = _run_bench(["--manifest", str(tmp_path / "nope.json")])
    assert r.returncode == 2


def test_bench_exit2_threshold_missing(tmp_path):
    """门槛缺失 = 配置错误 exit 2，不回落代码默认值（K9）。"""
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    del m["acceptance"]
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    r = _run_bench(["--manifest", str(p)])
    assert r.returncode == 2
    assert "exact_match_required" in (r.stderr + r.stdout)


def test_bench_exit2_cases_missing(tmp_path):
    r = _run_bench(["--cases", str(tmp_path / "nope.json")])
    assert r.returncode == 2


def test_bench_exit2_wordlists_dir_missing(tmp_path):
    r = _run_bench(["--wordlists-dir", str(tmp_path / "nowhere")])
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# 三形态探活（端到端必红）——子进程断言退出码 != 0，不断言内部函数被调
# ---------------------------------------------------------------------------
def _probe(tmp_path, mutate_cases=None, wordlists_dir=None, extra_args=None):
    """端到端探活夹持：复制 cases/manifest 到 tmp，按需变异，跑 bench 进程。"""
    args = ["--cases", str(tmp_path / "cases.json"),
            "--manifest", str(tmp_path / "manifest.json")]
    if mutate_cases is not None:
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        mutate_cases(cases)
        (tmp_path / "cases.json").write_text(
            json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        shutil.copy(CASES, tmp_path / "cases.json")
    shutil.copy(MANIFEST, tmp_path / "manifest.json")
    if wordlists_dir is not None:
        args += ["--wordlists-dir", str(wordlists_dir)]
    if extra_args:
        args += extra_args
    return _run_bench(args)


def test_probe_1_tampered_truth_must_fail(tmp_path):
    """探活①：篡改一条真值（位置 +1）→ bench 进程必红（端到端）。"""
    def mutate(cs):
        for c in cs:
            if c["expect_hits"]:
                c["expect_hits"][0]["col"] += 1
                return
        raise AssertionError("没有可篡改的样例")

    r = _probe(tmp_path, mutate_cases=mutate)
    assert r.returncode == 1, "篡改真值后 bench 仍绿——探活失效：\n%s" % r.stdout
    assert "FAIL" in r.stdout and "BENCH FAIL" in r.stdout


def test_probe_1b_tampered_text_must_fail(tmp_path):
    """探活① 变体：篡改样例文本（前面插入两字）→ 期望位置错位 → 必红。"""
    def mutate(cs):
        for c in cs:
            if c["kind"] == "positive-per-word":
                c["text"] = "前缀" + c["text"]
                return
        raise AssertionError("没有 positive-per-word 样例")

    r = _probe(tmp_path, mutate_cases=mutate)
    assert r.returncode == 1


def test_probe_2_empty_wordlist_must_fail(tmp_path):
    """探活②：注入空词表 → 零生效词条 → 正面样例全漏报 → 必红（端到端）。"""
    wdir = tmp_path / "empty-wordlists"
    wdir.mkdir()
    (wdir / "empty.json").write_text(
        json.dumps({"category": "绝对化用语", "entries": []}, ensure_ascii=False),
        encoding="utf-8")
    r = _probe(tmp_path, wordlists_dir=wdir)
    assert r.returncode == 1, "空词表下 bench 仍绿——探活失效：\n%s" % r.stdout
    assert "BENCH FAIL" in r.stdout


def test_probe_3_bad_anchor_must_fail(tmp_path):
    """探活③：坏锚点注入（词表词条锚点指向不存在的法条）→ 该词不生效 →
    依赖它的样例漏报 → bench 必红（端到端）。"""
    # 取一个真值样例涉及的词面，改其锚点 doc 使门控拒绝
    check = load_check_module(ROOT / "scripts" / "check.py")
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    target_word = next(c["expect_hits"][0]["word"] for c in cases if c["kind"] == "positive-per-word")

    wdir = tmp_path / "wordlists"
    wdir.mkdir()
    n_broken = 0
    for f in sorted(WORDLISTS.glob("*.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        hit = False
        for e in payload["entries"]:
            if e["word"] == target_word:
                e["anchor"]["doc"] = "no-such-statute"
                hit = True
                n_broken += 1
        (wdir / f.name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    assert n_broken >= 1, "未找到目标词面：%s" % target_word

    r = _probe(tmp_path, wordlists_dir=wdir)
    assert r.returncode == 1, "坏锚点注入后 bench 仍绿——探活失效：\n%s%s" % (r.stdout, r.stderr)
    assert "BENCH FAIL" in r.stdout


def test_probe_bench_threshold_enforced(tmp_path):
    """探活补充：门槛不被满足时必红（把 exact_match_required 提到不可能值）。"""
    def mutate_manifest(m):
        m["acceptance"]["exact_match_required"] = 1.5

    shutil.copy(CASES, tmp_path / "cases.json")
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutate_manifest(m)
    # 1.5 超界 → exit 2（配置错误）；改用 1.0 且篡改一条真值 → exit 1
    r = _run_bench(["--cases", str(tmp_path / "cases.json"), "--manifest",
                    str(tmp_path / "manifest.json")])
    assert r.returncode == 2
    # 合法门槛下的失败路径：篡改真值
    m["acceptance"]["exact_match_required"] = 1.0
    (tmp_path / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    for c in cases:
        if c["expect_hits"]:
            c["expect_hits"][0]["word"] = "不存在的词面"
            break
    (tmp_path / "cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    r2 = _run_bench(["--cases", str(tmp_path / "cases.json"), "--manifest",
                     str(tmp_path / "manifest.json")])
    assert r2.returncode == 1


# ---------------------------------------------------------------------------
# K6/D-10 词面门禁（tools/ 扩展）：gen_cases.py 源码不内嵌词表词面
# ---------------------------------------------------------------------------
def test_gen_cases_source_no_wordlist_tokens():
    tokens = [t for t in rulepack_word_tokens() if len(t) >= 3]
    assert tokens
    source = GEN_CASES.read_text(encoding="utf-8")
    embedded = sorted(t for t in tokens if t in source)
    assert not embedded, "gen_cases.py 源码内嵌规则包词面：%s" % embedded[:5]


# ---------------------------------------------------------------------------
# 确定性：bench 机读摘要逐字节稳定（两次运行一致）
# ---------------------------------------------------------------------------
def test_bench_summary_deterministic():
    outs = []
    for _ in range(2):
        r = _run_bench([])
        assert r.returncode == 0
        outs.append(r.stdout)
    assert outs[0] == outs[1], "bench 摘要两次运行不一致（确定性破坏）"
