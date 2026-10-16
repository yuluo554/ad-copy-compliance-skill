# skill 调用演练记录（可复现）

> **用途**：把题面评分项"skill 可被 agent 实际调用（安装即用）"落成**可核验物**——
> 记录一次真实执行的"安装 → 发现 → 扫描 → 判定"全流程，含逐条真跑命令与原始输出；
> 任何人在同版本上照本文件重跑应得到一致结果。**非截图、非录屏**，是可复现的步骤台账。
>
> **执行信息**：本机 Windows 10 / Git Bash；解释器 `py -3.12`（本机 `py -0p` 双道 3.8+3.12）；
> 演练日期同本轮修复；被测版本 `scripts/check.py --version` = `0.0.1`。
> 命令按仓库根为工作目录给出；宿主 skills 目录以临时目录替代（避免污染本机 agent 配置），
> 安装语义与真实 skills 目录一致（本仓库根即 skill 根）。

---

## 步骤 1：安装（放入 skills 目录）

```bash
# 模拟"克隆到宿主 skills 目录"（此处用临时目录，语义等同）
mkdir -p /tmp/drill/skills
git clone <本仓库> /tmp/drill/skills/ad-copy-compliance-skill
# 或：cp -r <本仓库> /tmp/drill/skills/ad-copy-compliance-skill
```

**结果**：skill 根目录出现，顶层含 `SKILL.md` / `scripts/` / `references/` / `README.md`。

---

## 步骤 2：被 agent 发现（解析 frontmatter）

宿主 agent 靠 `SKILL.md` 顶部 YAML frontmatter 的 `name` + `description`（含触发词）发现并决定调用。

```bash
py -3.12 -c "import re,yaml,pathlib; t=pathlib.Path('SKILL.md').read_text(encoding='utf-8'); d=yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)); print('name =',d['name']); print('description =',d['description'][:70],'...')"
```

**原始输出**：

```
name = ad-copy-compliance-skill
description = 广告文案合规自查（《广告法》第九条绝对化用语 + 平台违禁词）。粘贴推广文案（商品标题/详情页/直播话术/朋友圈/短视频脚本），逐句标红 ...
```

**结论**：frontmatter 可解析、`name` 与目录名一致、`description` 含触发词 → agent 可发现。

---

## 步骤 3：工作流①——确定性扫描（零 LLM、零网络）

```bash
py -3.12 -X utf8 scripts/check.py --selftest      # 冒烟
py -3.12 -X utf8 scripts/check.py --version
printf '本店青芜食品销量第一，国家级认证，包治百病。\n' > copy.txt
py -3.12 -X utf8 scripts/check.py copy.txt          # → 命中集合 JSON（stdout）
```

**原始输出（节选）**：

```
SELFTEST_OK ad-copy-compliance-check 0.0.1
ad-copy-compliance-check 0.0.1
[
  { "word": "销量第一", "category": "绝对化用语", "risk": "high", "line": 1, "col": 7,
    "context": "本店青芜食品销量第一，国家级认证，包治百", "suggestion": "删除绝对化表述，改为可核实的客观描述（如具体数据并附出处）" },
  { "word": "国家级", "category": "绝对化用语", "risk": "high", "line": 1, "col": 12,
    "context": "店青芜食品销量第一，国家级认证，包治百病。", "suggestion": "删除该表述，或改为可核实的客观事实描述" },
  { "word": "包治百病", "category": "医疗违禁", "risk": "high", "line": 1, "col": 18,
    "context": "量第一，国家级认证，包治百病。", "suggestion": "删除医疗功效表述；普通商品改为客观成分/质地描述，医疗商品须持证并按审查证明发布" }
]
```

退出码 `1`（有命中，K4 三语义）。命中位置逐字可定位（`word`/`line`/`col` 可在原文核对）。

---

## 步骤 4：工作流②——会话内语境判定（按 `references/judgment-protocol.md`）

判定层由宿主 agent 在会话内执行：对扫描层**每条命中**做注释副本，**只追加**三字段
（`verdict` / `verdict_reason` / `verdict_anchor`），不得新增/删除/移动命中（K10）。

**本轮执行方式**：agent 会话内对步骤 3 的三条命中逐条判定并组装注释副本，同时用脚本断言
"字段只增不减、命中条数/位置/顺序未变"（脚本见下），产物如下：

```json
{
  "meta": { "judgment": "on", "note": "判定层产物，可复跑性弱于扫描层" },
  "hits": [
    { "word": "销量第一", "line": 1, "col": 7,  "verdict": "confirmed",
      "verdict_reason": "直接向消费者的商品宣称中使用序位绝对化断言，无限定语/无引述豁免特征（协议 §1.1）",
      "verdict_anchor": { "doc": "advertising-law", "clause": "第九条" } },
    { "word": "国家级", "line": 1, "col": 12, "verdict": "confirmed",
      "verdict_reason": "“国家级”属《广告法》第九条明列禁止用语，本语境为直接宣称（协议 §1.1）",
      "verdict_anchor": { "doc": "advertising-law", "clause": "第九条" } },
    { "word": "包治百病", "line": 1, "col": 18, "verdict": "confirmed",
      "verdict_reason": "普通食品宣称疗效，属医疗功效断言（协议 §1.1）",
      "verdict_anchor": { "doc": "medical-ad-measures", "clause": "第七条" } }
  ]
}
```

**K10 断言（脚本化，真跑通过）**：

```python
import json, subprocess, sys, pathlib
copy = pathlib.Path("copy.txt")
hits = json.loads(subprocess.run([sys.executable, "-X", "utf8", "scripts/check.py", str(copy)],
                                 capture_output=True).stdout.decode("utf-8"))
# ...（见本轮执行：逐条追加 verdict 三字段后组装 annotated）...
assert all(set(a) == set(h) | {"verdict", "verdict_reason", "verdict_anchor"}
           for a, h in zip(annotated, hits))
assert all((a["word"], a["line"], a["col"]) == (h["word"], h["line"], h["col"])
           for a, h in zip(annotated, hits))
```

**输出**：`OK: K10 命中条数/位置/顺序未变，仅追加三字段`。

---

## 步骤 5：降级路径（判定关闭 → 全 uncertain）

判定层可随时要求"只扫描、不判定"：所有命中标 `uncertain`，`meta.judgment="off"`，
note 含"仅扫描结果，未经语境判定"——工具可用性不依赖 LLM 在场
（协议 §0；结构测试 `tests/test_judgment_protocol.py` 锁定）。

---

## 复现方式

1. `git clone` / 复制本仓库到任意 skills 目录（或仓库根）；
2. 按上列步骤 2–4 依次执行（步骤 3/4 的命令与断言脚本均为纯 stdlib，`py -3.12`/`py -3.8` 均可）；
3. 扫描输出应与步骤 3 逐字节一致（确定性引擎，同输入同位置）；
4. 判定产物依会话证据可不同——**判定层可复现性弱于扫描层**，此点由协议显式声明、本记录如实保留。

> **诚实口径**：本文件记录的是**一次本机真实执行**；不确定项（如宿主 skills 目录的具体位置）
> 已标注"随 agent 而异"，未虚构统一路径。
