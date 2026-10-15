# -*- coding: utf-8 -*-
"""仓库门禁测试：零依赖/零外联（import 白名单）、词面不内嵌（K6）、CI workflow 结构。

口径：scripts/ 源码只允许白名单内的顶层 import（新增必须显式登记并复核——
"零第三方、零网络"是本项目的安装面承诺，见 plan/03 §7）；
scripts/ 源码不得出现规则包词面（token 由规则包运行时实算，K6/M2 初版）。
"""
import ast
import re
from pathlib import Path

import yaml

from conftest import rulepack_word_tokens

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_TOP_LEVEL_IMPORTS = {"argparse", "json", "re", "sys", "pathlib"}


def _imports_of(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def test_scripts_only_use_whitelisted_stdlib():
    script_files = sorted((ROOT / "scripts").glob("*.py"))
    assert script_files, "scripts/ 下未找到任何脚本"
    for path in script_files:
        bad = _imports_of(path) - ALLOWED_TOP_LEVEL_IMPORTS
        assert not bad, "%s 出现白名单外 import：%s" % (path.name, sorted(bad))


# K6 词面不内嵌门禁（M2 初版）：scripts/ 源码（含注释/文档串）不得逐字出现
# 规则包词面；规则内容只能定义在 references/，脚本运行时从规则包加载。
# 只查 ≥3 字词面（决策 D-10）：2 字中文词面（如"绝对"）在正常行文/类别枚举
# （"绝对化用语"）中碰撞不可收敛，纯误报；特征违禁词均在 3 字以上。
# 测试若需构造含词面的输入，同样运行时实算（见 conftest）；自检合成占位词
# 以"自检占位词"前缀区分，不与词表词面撞面。
def test_scripts_do_not_embed_wordlist_tokens():
    tokens = [t for t in rulepack_word_tokens() if len(t) >= 3]
    assert tokens, "规则包 token 实算为空——规则包缺失或被清空？"
    script_files = sorted((ROOT / "scripts").glob("*.py"))
    assert script_files, "scripts/ 下未找到任何脚本"
    for path in script_files:
        source = path.read_text(encoding="utf-8")
        embedded = sorted(t for t in tokens if t in source)
        assert not embedded, (
            "%s 源码内嵌规则包词面（K6 门禁）：%s；规则内容只能定义于 references/，"
            "脚本运行时加载" % (path.name, embedded[:5])
        )


def test_wordlist_tokens_are_distinct_from_selftest_placeholders():
    """自检合成占位词不得与词表词面重合（否则 M2 门禁上线即撞红）。"""
    tokens = rulepack_word_tokens()
    for placeholder in ("自检占位词甲", "自检占位词乙", "自检占位词丙", "自检占位词丁"):
        assert placeholder not in tokens, "自检占位词 %s 撞真实词表词面" % placeholder


def _workflow_files():
    wdir = ROOT / ".github" / "workflows"
    return sorted(wdir.glob("*.yml")) if wdir.is_dir() else []


def test_workflows_parse_and_structure_ok():
    files = _workflow_files()
    assert files, "未找到 .github/workflows/*.yml"
    for wf in files:
        data = yaml.safe_load(wf.read_text(encoding="utf-8"))
        assert isinstance(data, dict), "%s 顶层非映射" % wf.name
        jobs = data.get("jobs")
        assert isinstance(jobs, dict) and jobs, "%s 无可解析的 jobs" % wf.name
        for job_name, job in jobs.items():
            assert isinstance(job, dict), "%s/%s 非映射" % (wf.name, job_name)
            assert "runs-on" in job, "%s/%s 缺 runs-on" % (wf.name, job_name)
            steps = job.get("steps") or []
            assert steps, "%s/%s 缺 steps" % (wf.name, job_name)


def test_workflow_checkout_fetches_full_history():
    files = _workflow_files()
    assert files, "未找到 .github/workflows/*.yml"
    for wf in files:
        data = yaml.safe_load(wf.read_text(encoding="utf-8"))
        for job_name, job in (data.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                uses = step.get("uses", "") or ""
                if "actions/checkout" in uses:
                    with_ = step.get("with") or {}
                    assert with_.get("fetch-depth") == 0, (
                        "%s/%s checkout 必须 fetch-depth: 0（历史类守门测试依赖，浅克隆会静默空验）"
                        % (wf.name, job_name)
                    )
