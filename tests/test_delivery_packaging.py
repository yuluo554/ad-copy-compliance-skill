# -*- coding: utf-8 -*-
"""M5 交付包装测试（plan/04 §7 M5 行）。

- 契约一致性（K1/plan/04 §1）：SKILL.md 机器可解析契约块字段集合 == check.py HIT_FIELDS
  （双向：文档不许多、不许少）；
- 编码守卫（K13）：全部可执行入口（scripts/ ＋ tools/）在 main() 入口调用
  _ensure_utf8_stdio 探针式守卫（AST 断言，防"新增入口忘了挂守卫"）；
- README 快速开始可跑性（plan/04 §7 M5）：README 代码块中的仓库内命令逐条
  实测语义锁定（命令形态与退出码）。
"""
import ast
import json
import re
from pathlib import Path

import pytest

from conftest import ROOT, load_check_module

SKILL = ROOT / "SKILL.md"


# ---------------------------------------------------------------- 契约一致性（K1）


def _contract_fields_from_skill():
    text = SKILL.read_text(encoding="utf-8")
    blocks = re.findall(r"<!--\s*contract-fields:\s*([a-z ]+?)\s*-->", text)
    assert blocks, "SKILL.md 缺机器可解析契约块（<!-- contract-fields: ... -->）"
    assert len(blocks) == 1, "SKILL.md 契约块必须唯一（现 %d 个）" % len(blocks)
    return tuple(blocks[0].split())


@pytest.fixture(scope="module")
def check():
    return load_check_module(ROOT / "scripts" / "check.py")


def test_skill_contract_fields_equal_hit_fields(check):
    """双向一致性：契约块字段集合与 HIT_FIELDS 完全相等（不许多、不许少）。"""
    fields = _contract_fields_from_skill()
    hit_fields = tuple(check.HIT_FIELDS)
    assert set(fields) == set(hit_fields), (
        "SKILL.md 契约块与 HIT_FIELDS 不一致：多 %s / 少 %s"
        % (sorted(set(fields) - set(hit_fields)), sorted(set(hit_fields) - set(fields)))
    )
    assert len(fields) == len(hit_fields), "契约块字段有重复"


def test_skill_contract_block_order_matches_hit_fields(check):
    """块内字段序与 HIT_FIELDS 声明序一致（文档即契约，漂移即红）。"""
    assert _contract_fields_from_skill() == tuple(check.HIT_FIELDS)


def test_hit_fields_match_actual_hit_shape(check):
    """HIT_FIELDS 与引擎实际产出的命中字段（序）一致——契约三方对齐。"""
    entries, _ = check._load_entries(
        ROOT / "references" / "wordlists", ROOT / "references" / "statutes")
    assert entries, "真实词表无生效条目"
    from conftest import rulepack_word_tokens
    tokens = sorted(rulepack_word_tokens(), key=lambda w: (-len(w), w))
    text = "本款产品是%s之选。\n" % tokens[0]
    hits = check.scan_text(text, entries)
    assert hits, "夹具未产生命中"
    assert list(hits[0].keys()) == list(check.HIT_FIELDS)


def test_skill_md_keeps_m3_workflow_alignment():
    """M5 重写 SKILL.md 不得破坏 M3 对齐的工作流语义（test_judgment_protocol 同族口径）。"""
    skill = SKILL.read_text(encoding="utf-8")
    for term in ("confirmed", "exempt", "uncertain", "judgment-protocol.md"):
        assert term in skill, "SKILL.md 工作流未与协议对齐（缺 %s）" % term
    assert "只注释、不改位置" in skill or "不改位置" in skill
    assert "未经语境判定" in skill, "SKILL.md 缺降级声明措辞"


def test_skill_md_k12_wording():
    skill = SKILL.read_text(encoding="utf-8")
    assert "不构成法律意见" in skill
    assert "不等于合规" in skill, "SKILL.md 缺 K12 零命中≠合规统一措辞"


def test_skill_md_k4_exit_codes():
    """退出码三语义摘要必须在文档中（K4）。"""
    skill = SKILL.read_text(encoding="utf-8")
    for code in ("0", "1", "2"):
        assert code in skill


# ---------------------------------------------------------------- 编码守卫（K13）


def _has_utf8_stdio_guard(path):
    """AST 检查：入口 main() 体内调用 _ensure_utf8_stdio。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                        and sub.func.id == "_ensure_utf8_stdio":
                    return True
    return False


def test_all_executable_entrypoints_have_utf8_guard():
    """全部可执行入口（scripts/ ＋ tools/）main() 内挂 _ensure_utf8_stdio 探针守卫（K13）。"""
    entry_files = sorted(
        list((ROOT / "scripts").glob("*.py")) + list((ROOT / "tools").glob("*.py")))
    assert len(entry_files) >= 6, "可执行入口数量异常（scripts+tools 应 ≥6）"
    missing = [p.name for p in entry_files if not _has_utf8_stdio_guard(p)]
    assert not missing, "以下可执行入口缺 _ensure_utf8_stdio 编码守卫：%s" % missing


# ---------------------------------------------------------------- README 快速开始可跑


def _readme_quickstart_commands():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    # 只取"快速开始"节内的 bash 代码块
    m = re.search(r"## 快速开始.*?\n```bash\n(.*?)```", text, re.S)
    assert m, "README 缺'快速开始'节或其中无 bash 代码块"
    cmds = []
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].strip()  # 去行尾注释
        if line:
            cmds.append(line)
    assert cmds, "README 快速开始代码块无命令"
    return cmds


def _quickstart_interpreter(py):
    """选 README 快速开始实测用解释器前缀（列表形态，如 ["py", "-3.8"]）。

    Windows 优先 py 启动器（`py -3.x -X utf8`，本机 D-5 双道）；探测不可用且
    宿主解释器版本匹配时回退 sys.executable；仍不可得则 skip——
    "逐条实测"语义不变，执行道因环境而异（CI ubuntu 无 py / CI windows 无 3.8）。
    """
    import os
    import subprocess
    import sys
    if os.name == "nt":
        try:
            probe = subprocess.run(["py", "-%s" % py, "-c", "import sys"],
                                   capture_output=True, timeout=60)
        except OSError:
            probe = None
        if probe is not None and probe.returncode == 0:
            return ["py", "-%s" % py]
    host = "%d.%d" % sys.version_info[:2]
    if host == py:
        return [sys.executable]
    pytest.skip("本环境无 Python %s 运行道（py 启动器不可用且宿主为 %s）" % (py, host))


@pytest.mark.parametrize("py", ["3.8", "3.12"])
def test_readme_quickstart_commands_run(py, tmp_path):
    """README 快速开始逐条实测（plan/04 §7 M5：'每条命令实测过再写可跑'）。

    文档命令形态：`python scripts/check.py ...` / `python tools/bench.py ...`。
    按 `_quickstart_interpreter` 选道执行（py 启动器优先，宿主版本回退），
    语义等同、逐条断言退出码。
    """
    import os
    import subprocess
    _created = []
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for cmd in _readme_quickstart_commands():
        # 文档里 stdin 形态写作 `echo "…" | python scripts/check.py -`：
        # 测试剥掉管道左端，等价直喂合成文案
        stdin_data = None
        if "|" in cmd:
            _, cmd = cmd.split("|", 1)
            cmd = cmd.strip()
            stdin_data = "示例文案。".encode("utf-8")
        if cmd.startswith("echo ") and ">" in cmd:
            # 文案.txt 造数命令：等价写出同内容文件后继续（实测该行 shell 语义可行）
            (ROOT / "文案.txt").write_bytes(
                "本款产品是全效之王，销量第一。\n".encode("utf-8"))
            _created.append(ROOT / "文案.txt")
            continue
        assert cmd.startswith("python "), "README 快速开始命令应以 python 开头：%r" % cmd
        rest = cmd[len("python "):].split()
        argv = _quickstart_interpreter(py) + ["-X", "utf8"] + rest
        if rest[-1] == "-":
            argv = argv[:-1]
            stdin_data = stdin_data or "示例文案。".encode("utf-8")
        proc = subprocess.run(argv, cwd=str(ROOT), input=stdin_data,
                              capture_output=True, timeout=120, env=env)
        if "--selftest" in cmd or "--version" in cmd:
            assert proc.returncode == 0, "%s → exit %d: %s" % (cmd, proc.returncode, proc.stderr)
        else:
            # 扫描/基准命令：退出码三语义（0 零命中 / 1 有命中或基准 fail / 2 配置错误）
            assert proc.returncode in (0, 1), "%s → exit %d: %s" % (cmd, proc.returncode, proc.stderr)
            body = proc.stdout.decode("utf-8")
            if "check.py" in cmd:
                parsed = json.loads(body)
                assert isinstance(parsed, list), "check.py stdout 非命中集合 JSON"
    for f in _created:
        if f.exists():
            f.unlink()
