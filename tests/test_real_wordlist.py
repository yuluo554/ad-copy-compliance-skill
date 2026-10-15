# -*- coding: utf-8 -*-
"""M2 真实词表端到端测试（子进程 CLI 层）：命中/退出码/部分坏文件/确定性。

词面一律运行时从规则包实算（conftest.rulepack_word_tokens），源码不内嵌
词表词面（K6）。真实词表锚点指向仓库 references/statutes/（默认路径可用，
M1 冻结件）。
"""
import json
import shutil

import pytest

from conftest import ROOT, rulepack_word_tokens

CHECK = ROOT / "scripts" / "check.py"
WORDLISTS_DIR = ROOT / "references" / "wordlists"

from test_check import run_check  # 复用子进程 runner（cwd=ROOT，UTF-8）


@pytest.fixture(scope="module")
def tokens():
    t = rulepack_word_tokens()
    assert len(t) == 133
    return t


def _pick(tokens, category, min_len=1):
    return next(w for w in sorted(tokens) if category in tokens[w] and len(w) >= min_len)


def test_real_wordlist_hit_positions_and_exit_code(tokens):
    w1 = _pick(tokens, "绝对化用语")
    w2 = _pick(tokens, "医疗违禁")
    w3 = _pick(tokens, "行业违禁")
    text = "开头%s中间%s结尾%s。\n第二行干净。" % (w1, w2, w3)
    proc = run_check(["-", "--format", "text"], input_bytes=text.encode("utf-8"))
    assert proc.returncode == 1
    out = proc.stdout.decode("utf-8")
    assert "共 3 条命中" in out
    c2 = 3 + len(w1) + 2
    c3 = c2 + len(w2) + 2
    assert ("1:3\t%s\t[绝对化用语/" % w1) in out
    assert ("1:%d\t%s\t[医疗违禁/" % (c2, w2)) in out
    assert ("1:%d\t%s\t[行业违禁/" % (c3, w3)) in out
    assert "未启用条目" not in proc.stderr.decode("utf-8")


def test_real_wordlist_clean_input_exit_zero(tokens):
    proc = run_check(["-"], input_bytes="一段完全正常的文案，没有任何问题。\n".encode("utf-8"))
    assert proc.returncode == 0
    assert json.loads(proc.stdout.decode("utf-8")) == []


def test_real_wordlist_exit_zero_flag_and_context_zero(tokens):
    w = _pick(tokens, "绝对化用语")
    args = ["-", "--exit-zero", "--context", "0"]
    proc = run_check(args, input_bytes=("前缀%s后缀\n" % w).encode("utf-8"))
    assert proc.returncode == 0
    hit = json.loads(proc.stdout.decode("utf-8"))[0]
    assert hit["context"] == w and hit["col"] == 3


def test_partial_bad_file_others_still_load(tmp_path, tokens):
    """部分文件坏 → 其余文件正常加载（有真实命中）+ 坏文件进未启用清单。"""
    wdir = tmp_path / "wordlists"
    wdir.mkdir()
    for f in WORDLISTS_DIR.glob("*.json"):
        shutil.copyfile(f, wdir / f.name)
    (wdir / "zz-broken.json").write_bytes(b"{not json")
    (wdir / "zz-not-object.json").write_bytes(b"[1,2,3]")
    w = _pick(tokens, "绝对化用语")
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir)],
        input_bytes=("文案含%s。\n" % w).encode("utf-8"),
    )
    assert proc.returncode == 1
    assert json.loads(proc.stdout.decode("utf-8"))[0]["word"] == w
    err = proc.stderr.decode("utf-8")
    assert "zz-broken.json / - / 词表文件不可解析" in err
    assert "zz-not-object.json / - / 词表文件结构非法（顶层须为对象）" in err
    # 其余 133 条不受坏文件影响（stderr 无其它未启用行）
    assert err.count("未启用条目") == 2


def test_determinism_two_runs_byte_identical(tokens):
    w1 = _pick(tokens, "绝对化用语")
    w2 = _pick(tokens, "医疗违禁")
    data = ("%s和%s都在第一行。\r\n第二行%s。\n" % (w1, w2, w1)).encode("utf-8")
    args = ["-", "--format", "text"]
    p1 = run_check(args, input_bytes=data)
    p2 = run_check(args, input_bytes=data)
    assert (p1.stdout, p1.stderr, p1.returncode) == (p2.stdout, p2.stderr, p2.returncode)
    assert p1.returncode == 1


def test_real_wordlist_position_locatable_in_raw(tokens):
    """命中位置在原始（BOM/CRLF 归一后）文本上逐字可定位。"""
    w = _pick(tokens, "绝对化用语")
    raw = "\ufeff甲%s乙\r\n%s行首\n" % (w, w)
    proc = run_check(["-"], input_bytes=raw.encode("utf-8"))
    assert proc.returncode == 1
    text = raw.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    for h in json.loads(proc.stdout.decode("utf-8")):
        assert lines[h["line"] - 1][h["col"] - 1:h["col"] - 1 + len(h["word"])] == h["word"]
    assert [(h["line"], h["col"]) for h in json.loads(proc.stdout.decode("utf-8"))] == [
        (1, 2), (2, 1),
    ]
