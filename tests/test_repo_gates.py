# -*- coding: utf-8 -*-
"""仓库门禁测试：零依赖/零外联（import 白名单）、CI workflow 结构。

口径：scripts/ 源码只允许白名单内的顶层 import（新增必须显式登记并复核——
"零第三方、零网络"是本项目的安装面承诺，见 plan/03 §7）。
"""
import ast
from pathlib import Path

import yaml

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
