# -*- coding: utf-8 -*-
"""pytest 共享夹具：check.py 模块加载、规则包 token 运行时实算。

词表词面只在测试运行时从规则包实算（K6：脚本/测试源码不内嵌词表词面；
门禁的豁免路径 = 动态词面标记对，见 test_repo_gates.py）。
"""
import glob
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_check_module(check_path):
    """把 scripts/check.py 以独立模块载入（避免对 scripts/ 做 import 包化）。"""
    spec = importlib.util.spec_from_file_location(check_path.stem, str(check_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rulepack_word_tokens():
    """运行时实算规则包全部词面：返回 {word: [category, ...]}。"""
    tokens = {}
    for f in sorted(glob.glob(str(ROOT / "references" / "wordlists" / "*.json"))):
        payload = json.loads(Path(f).read_text(encoding="utf-8"))
        for e in payload["entries"]:
            tokens.setdefault(e["word"], []).append(payload["category"])
    return tokens
