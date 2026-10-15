# -*- coding: utf-8 -*-
"""check.py 的行为测试（M0 骨架基线；M2 全量扩展见 test_scan_dfa.py / test_real_wordlist.py）。

约定：只依赖 pytest + 标准库；子进程显式 UTF-8 读写；测试夹具一律使用合成占位词。
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check.py"

PLACEHOLDER_A = "自检占位词甲"
PLACEHOLDER_B = "自检占位词乙"
PLACEHOLDER_C = "自检占位词丙"
PLACEHOLDER_D = "自检占位词丁"

STATUTE_TEXT = "第九条 测试条款：%s属于受限表述。\n第十条 其他内容。\n" % PLACEHOLDER_A


def run_check(args, input_bytes=None, cwd=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, str(CHECK)] + list(args),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(cwd if cwd is not None else ROOT),
    )
    return proc


def json_out(proc):
    return json.loads(proc.stdout.decode("utf-8"))


def load_module():
    spec = importlib.util.spec_from_file_location("check_skeleton", CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verified_entry(word, category="绝对化用语", risk="high", doc="test-law",
                   clause="第九条", basis="literal", suggestion="改为可核实的客观表述"):
    return {
        "word": word,
        "category": category,
        "risk": risk,
        "anchor": {"doc": doc, "clause": clause, "basis": basis},
        "source": {"type": "synthetic", "ref": "test fixture", "note": "测试夹具，非真实词表"},
        "status": "verified",
        "suggestion": suggestion,
    }


def make_fixture(tmp_path, entries, statute_text=STATUTE_TEXT, doc="test-law", category="绝对化用语"):
    wdir = tmp_path / "wordlists"
    wdir.mkdir(exist_ok=True)
    sdir = tmp_path / "statutes"
    sdir.mkdir(exist_ok=True)
    if statute_text is not None:
        (sdir / (doc + ".txt")).write_bytes(statute_text.encode("utf-8"))
    payload = {"category": category, "note": "synthetic test fixture", "entries": entries}
    (wdir / "absolute-terms.json").write_bytes(
        json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    )
    return wdir, sdir


def test_selftest_ok():
    proc = run_check(["--selftest"])
    assert proc.returncode == 0
    assert b"SELFTEST_OK" in proc.stdout


def test_version_prints():
    proc = run_check(["--version"])
    assert proc.returncode == 0
    assert b"ad-copy-compliance-check" in proc.stdout


def test_hit_fields_contract_locked():
    mod = load_module()
    assert list(mod.HIT_FIELDS) == [
        "word", "category", "risk", "line", "col", "context", "suggestion",
    ]


def test_empty_wordlists_yields_empty_array(tmp_path):
    wdir = tmp_path / "wordlists"
    wdir.mkdir()
    proc = run_check(["-", "--wordlists-dir", str(wdir)], input_bytes="测试文案一。\n".encode("utf-8"))
    assert proc.returncode == 0
    assert json_out(proc) == []


def test_basic_matching_positions_and_contract(tmp_path):
    wdir, sdir = make_fixture(
        tmp_path,
        [
            verified_entry(PLACEHOLDER_A, risk="high"),
            verified_entry(PLACEHOLDER_B, risk="medium", basis="variant"),
        ],
    )
    text = "示例：%s，还有%s。\n" % (PLACEHOLDER_A, PLACEHOLDER_B)
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir)],
        input_bytes=text.encode("utf-8"),
    )
    assert proc.returncode == 1
    hits = json_out(proc)
    assert [(h["word"], h["line"], h["col"]) for h in hits] == [
        (PLACEHOLDER_A, 1, 4),
        (PLACEHOLDER_B, 1, 13),
    ]
    assert list(hits[0].keys()) == [
        "word", "category", "risk", "line", "col", "context", "suggestion",
    ]
    assert hits[0]["risk"] == "high" and hits[1]["risk"] == "medium"
    assert hits[0]["category"] == "绝对化用语"
    assert hits[0]["context"] == text.strip()
    # 命中位置可在原文逐字定位
    lines = text.split("\n")
    for h in hits:
        seg = lines[h["line"] - 1][h["col"] - 1: h["col"] - 1 + len(h["word"])]
        assert seg == h["word"]
    assert "未启用条目".encode("utf-8") not in proc.stderr


def test_gating_rejects_pending_and_bad_anchors(tmp_path):
    pending = dict(verified_entry(PLACEHOLDER_B), status="pending")
    bad_clause = verified_entry(PLACEHOLDER_C, clause="第九十九条")
    literal_miss = verified_entry(PLACEHOLDER_D)  # 词面不在条款正文中
    wdir, sdir = make_fixture(tmp_path, [verified_entry(PLACEHOLDER_A), pending, bad_clause, literal_miss])
    text = "甲%s 乙%s 丙%s 丁%s\n" % (PLACEHOLDER_A, PLACEHOLDER_B, PLACEHOLDER_C, PLACEHOLDER_D)
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir)],
        input_bytes=text.encode("utf-8"),
    )
    assert proc.returncode == 1
    hits = json_out(proc)
    assert [h["word"] for h in hits] == [PLACEHOLDER_A]
    err = proc.stderr.decode("utf-8")
    assert "未启用条目" in err
    assert "status 非 verified" in err
    assert "条款解析不到" in err
    assert "literal 词面未见于条款" in err


def test_gating_anchor_file_missing(tmp_path):
    entry = verified_entry(PLACEHOLDER_A, doc="missing-law")
    wdir, sdir = make_fixture(tmp_path, [entry])
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir)],
        input_bytes=("%s\n" % PLACEHOLDER_A).encode("utf-8"),
    )
    assert proc.returncode == 0
    assert json_out(proc) == []
    assert "锚点文件缺失".encode("utf-8") in proc.stderr


def test_missing_input_file_exit_2(tmp_path):
    wdir = tmp_path / "wordlists"
    wdir.mkdir()
    proc = run_check(["no-such-file.txt", "--wordlists-dir", str(wdir)])
    assert proc.returncode == 2
    assert "输入文件不存在".encode("utf-8") in proc.stderr


def test_non_utf8_input_exit_2(tmp_path):
    wdir = tmp_path / "wordlists"
    wdir.mkdir()
    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"\xff\xfe\x00bad")
    proc = run_check([str(bad), "--wordlists-dir", str(wdir)])
    assert proc.returncode == 2
    assert "非 UTF-8".encode("utf-8") in proc.stderr


def test_wordlists_dir_missing_exit_2(tmp_path):
    proc = run_check(["-", "--wordlists-dir", str(tmp_path / "nope")], input_bytes=b"x\n")
    assert proc.returncode == 2
    assert "词表目录不存在".encode("utf-8") in proc.stderr


def test_unknown_flag_exit_2():
    proc = run_check(["--no-such-flag"])
    assert proc.returncode == 2


def test_crlf_bom_and_slice_positions(tmp_path):
    wdir, sdir = make_fixture(tmp_path, [verified_entry(PLACEHOLDER_A)])
    raw = "\ufeff%s。\r\n第二行也有%s。\r\n" % (PLACEHOLDER_A, PLACEHOLDER_B)
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir)],
        input_bytes=raw.encode("utf-8"),
    )
    assert proc.returncode == 1
    hits = json_out(proc)
    assert [(h["word"], h["line"], h["col"]) for h in hits] == [(PLACEHOLDER_A, 1, 1)]
    # 第二行虽有占位词乙但未生效（未在词表）→ 零命中；此处验证 BOM/CRLF 不破坏位置
    assert hits[0]["context"] == "%s。" % PLACEHOLDER_A


def test_context_option_zero(tmp_path):
    wdir, sdir = make_fixture(tmp_path, [verified_entry(PLACEHOLDER_A)])
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir), "--context", "0"],
        input_bytes=("前缀%s后缀\n" % PLACEHOLDER_A).encode("utf-8"),
    )
    assert proc.returncode == 1
    hits = json_out(proc)
    assert hits[0]["context"] == PLACEHOLDER_A


def test_determinism_two_runs_byte_identical(tmp_path):
    wdir, sdir = make_fixture(
        tmp_path,
        [verified_entry(PLACEHOLDER_A), verified_entry(PLACEHOLDER_B, risk="low", basis="variant")],
    )
    args = ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir)]
    data = ("%s和%s都在。\n再一行%s。\n" % (PLACEHOLDER_A, PLACEHOLDER_B, PLACEHOLDER_A)).encode("utf-8")
    p1 = run_check(args, input_bytes=data)
    p2 = run_check(args, input_bytes=data)
    assert p1.stdout == p2.stdout
    assert p1.returncode == p2.returncode == 1


def test_exit_zero_flag(tmp_path):
    wdir, sdir = make_fixture(tmp_path, [verified_entry(PLACEHOLDER_A)])
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--statutes-dir", str(sdir), "--exit-zero"],
        input_bytes=("%s\n" % PLACEHOLDER_A).encode("utf-8"),
    )
    assert proc.returncode == 0
    assert json_out(proc)


def test_text_format_runs(tmp_path):
    wdir = tmp_path / "wordlists"
    wdir.mkdir()
    proc = run_check(
        ["-", "--wordlists-dir", str(wdir), "--format", "text"],
        input_bytes="一段普通文案。\n".encode("utf-8"),
    )
    assert proc.returncode == 0
    assert "共 0 条命中".encode("utf-8") in proc.stdout


def test_ensure_utf8_stdio_reconfigures_cp1252():
    mod = load_module()
    buf = io.BytesIO()
    stream = io.TextIOWrapper(buf, encoding="cp1252", errors="strict")
    mod._ensure_utf8_stdio([stream])
    stream.write("测")
    stream.flush()
    assert buf.getvalue() == "测".encode("utf-8")
